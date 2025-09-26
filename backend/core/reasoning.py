import asyncio
import json
import logging
from typing import List
from mcp import Tool

from tools.base import BaseTool, ToolResponse
from tools.app_maker.tool import AppMakerTool
from core.enums import ToolStatus
from core.session import (
    Session,
    OutputMessage,
    InputMessage,
    ContextMessage,
    RoleTypes,
    MsgStatus,
    ToolContent,
    TextContent,
)
from core.llm import OpenAIClient, LLMResponse
from fastmcp import Client

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine whether or not a loop is already running.
    - If no loop: use asyncio.run
    - If inside a running loop: run in a separate thread with its own loop
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(asyncio.run, coro).result()


class ReasoningEngine:
    def __init__(
        self,
        system_prompt: str,
        input_message: InputMessage,
        session: Session,
        mcp_config_path: str = None,
    ):
        self.input_message = input_message
        self.session = session
        self.system_prompt = system_prompt
        self.max_iterations = 10
        self.llm = OpenAIClient()
        self.tools: List[BaseTool] = []
        self.tools.append(AppMakerTool(session=self.session))
        self.stop_flag = False
        self.output_message: OutputMessage = self.session.output_message

        if mcp_config_path is None:
            import os
            mcp_config_path = os.path.join(os.path.dirname(__file__), "..", "mcp.json")
        
        try:
            with open(mcp_config_path, "r") as f:
                self.mcp_config = json.load(f)
            self._init_mcp_sync()
        except FileNotFoundError:
            logger.warning(f"MCP config file not found at {mcp_config_path}. MCP tools will not be available.")
            self.mcp_config = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in MCP config file {mcp_config_path}: {e}. MCP tools will not be available.")
            self.mcp_config = {}
        except Exception as e:
            logger.error(f"Error loading MCP config file {mcp_config_path}: {e}. MCP tools will not be available.")
            self.mcp_config = {}

    # -----------------
    # MCP integration
    # -----------------
    def _init_mcp_sync(self):
        """Load MCP tools once, without eventlet or manual loop juggling."""
        
        # Skip MCP initialization if config is empty (file loading failed)
        if not self.mcp_config:
            logger.info("Skipping MCP initialization due to empty config")
            return

        try:
            tools: List[Tool] = _run_async(self._list_mcp_tools())
            print(f"Tools: {tools}")
            for tool in tools:
                mcp_tool = self._wrap_mcp_tool(
                    tool_name=tool.name,
                    tool_description=tool.description or "",
                    tool_parameters=tool.inputSchema.get("properties", {}),
                )
                self.tools.append(mcp_tool)
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")

    async def _list_mcp_tools(self) -> List[Tool]:
        mcp_client = Client(self.mcp_config)
        async with mcp_client:
            return await mcp_client.list_tools()

    def _wrap_mcp_tool(self, tool_name: str, tool_description: str, tool_parameters: dict):
        client = Client(self.mcp_config)

        class MCPTool(BaseTool):
            def __init__(self, session: Session):
                super().__init__(session)

            @property
            def name(self):
                return tool_name

            @property
            def description(self):
                return tool_description

            @property
            def parameters(self):
                return {"type": "object", "properties": tool_parameters}

            def to_llm_format(self):
                return {
                    "name": tool_name,
                    "description": tool_description,
                    "parameters": {"type": "object", "properties": tool_parameters},
                }

            def run(self, **kwargs) -> ToolResponse:
                try:
                    result = _run_async(self._call_tool_async(tool_name, kwargs))
                    return ToolResponse(status=ToolStatus.SUCCESS, message="", data=result.data)
                except Exception as e:
                    logger.error(f"Tool call failed for {tool_name}: {e}")
                    return ToolResponse(status=ToolStatus.ERROR, message=str(e), data={"error": str(e)})


            async def _call_tool_async(self, tool_name: str, arguments: dict):
                async with client:
                    return await client.call_tool(tool_name, arguments=arguments)

        return MCPTool(self.session)

    # -----------------
    # Engine plumbing
    # -----------------
    def register_tools(self, tools: List[BaseTool]):
        self.tools.extend(tools)

    def build_context(self):
        """Build initial context with system + user message, safely extracting text."""
        content = [part.model_dump() for part in self.input_message.content]
        input_context = ContextMessage(content=content, role=RoleTypes.user)

        if not self.session.reasoning_context:
            self.session.reasoning_context.append(
                ContextMessage(content=self.system_prompt, role=RoleTypes.system)
            )
        self.session.reasoning_context.append(input_context)

    def _append_and_publish_text(self, text: str, status: MsgStatus):
        self.session.reasoning_context.append(
            ContextMessage(content=text, role=RoleTypes.assistant)
        )
        self.output_message.content.append(TextContent(text=text, type="text"))
        self.output_message.status = status
        self.output_message.publish()

    def run_tool(self, tool_name: str, **kwargs) -> ToolResponse:
        tool_content = ToolContent(
            tool_name=tool_name,
            tool_args=kwargs,
            tool_response=None,
            tool_status=ToolStatus.PROGRESS,
        )
        self.output_message.content.append(tool_content)
        self.output_message.publish()

        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            response = ToolResponse(status=ToolStatus.ERROR, message=f"Tool {tool_name} not found", data={"error": f"Tool {tool_name} not found"})
        else:
            response = tool.safe_call(**kwargs)

        tool_content.tool_status = response.status
        tool_content.tool_response = response.data
        self.output_message.publish()
        return response

    def stop(self):
        self.stop_flag = True

    def step(self):
        if self.stop_flag:
            return

        # First LLM call
        llm_response: LLMResponse = self.llm.chat_completions(
            messages=[m.to_llm_msg() for m in self.session.reasoning_context],
            tools=[t.to_llm_format() for t in self.tools],
        )
        logger.info(f"LLM Response: {llm_response}")

        if not llm_response.status:
            self._append_and_publish_text(llm_response.content, MsgStatus.error)
            self.stop()
            return

        if not llm_response.tool_calls:
            self._append_and_publish_text(llm_response.content, MsgStatus.success)
            self.stop()
            return

        # If tool calls were requested, run them synchronously, then do one final LLM call
        self.session.reasoning_context.append(
            ContextMessage(content=llm_response.content, tool_calls=llm_response.tool_calls, role=RoleTypes.assistant)
        )

        for tc in llm_response.tool_calls:
            tr: ToolResponse = self.run_tool(tc["tool"]["name"], **tc["tool"]["arguments"])
            self.session.reasoning_context.append(
                ContextMessage(content=str(tr), tool_call_id=tc["id"], role=RoleTypes.tool)
            )

        final_response: LLMResponse = self.llm.chat_completions(
            messages=[m.to_llm_msg() for m in self.session.reasoning_context]
        )
        status = MsgStatus.success if final_response.status else MsgStatus.error
        self._append_and_publish_text(final_response.content, status)
        self.stop()

    def run(self, max_iterations: int | None = None):
        self.iterations = max_iterations or self.max_iterations
        self.build_context()
        self.output_message.actions.append("Reasoning the message..")
        self.output_message.publish()

        while self.iterations > 0 and not self.stop_flag:
            self.iterations -= 1
            self.step()

        self.session.save_context_messages()
        logger.info("Reasoning Engine Finished")
