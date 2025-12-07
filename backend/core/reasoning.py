# reasoning.py
import logging
from typing import Dict
from tools.base import BaseTool, ToolResponse
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
from core.prompts import REASONING_PROMPT
from tools import available_tools

logger = logging.getLogger(__name__)


class ReasoningEngine:
    def __init__(
        self,
        system_prompt: str,
        input_message: InputMessage,
        session: Session,
    ):
        self.input_message = input_message
        self.session = session
        self.system_prompt = system_prompt or REASONING_PROMPT
        self.max_iterations = 10
        self.llm = OpenAIClient()
        self.tools: Dict[str, BaseTool] = {}
        self.stop_flag = False
        self.output_message: OutputMessage = self.session.output_message

        for tool in available_tools:
            tool_instance = tool(self.session)
            self.tools[tool_instance.name] = tool_instance

    def build_context(self):
        """Build initial context with system + user message, safely extracting text."""
        content = [part for part in self.input_message.content]
        input_context = ContextMessage(content=content, role=RoleTypes.user)

        if not self.session.reasoning_context:
            self.session.reasoning_context.append(
                ContextMessage(content=self.system_prompt, role=RoleTypes.system)
            )
        self.session.reasoning_context.append(input_context)

    def get_tool_info(self):
        return [
            tool.to_llm_format() for tool in self.tools.values()
        ]

    def run_tool(self, tool_name: str, **kwargs) -> ToolResponse:
        tool_content = ToolContent(
            tool_name=tool_name,
            tool_args=kwargs,
            tool_response=None,
            tool_status=ToolStatus.PROGRESS,
        )
        self.output_message.content.append(tool_content)
        self.output_message.publish()

        tool = self.tools.get(tool_name, None)
        if not tool:
            response = ToolResponse(
                status=ToolStatus.ERROR, 
                message=f"Tool {tool_name} not found", 
                data={"error": f"Tool {tool_name} not found"}
            )
        else:
            response = tool.safe_call(**kwargs)

        tool_content.tool_status = response.status
        tool_content.tool_response = response.data
        self.output_message.publish()
        return response

    def stop(self):
        self.stop_flag = True

    def step(self):

        while True:
            if self.stop_flag:
                return

            llm_response: LLMResponse = self.llm.chat_completions(
                messages=[m.to_llm_msg() for m in self.session.reasoning_context],
                tools=self.get_tool_info(),
            )
            logger.info(f"LLM Response: {llm_response}")

            if not llm_response.status:
                text_content = TextContent(
                    text=llm_response.content or "Something went wrong.", 
                    status=MsgStatus.error
                )
                self.output_message.content.append(text_content)
                self.output_message.status = MsgStatus.error
                self.output_message.publish()

                self.session.reasoning_context.append(
                    ContextMessage(content=text_content.text, role=RoleTypes.assistant)
                )
                self.stop()
                return

            if not llm_response.tool_calls:
                text_content = TextContent(text=llm_response.content or "", status=MsgStatus.success)
                self.output_message.content.append(text_content)

                self.output_message.status = MsgStatus.success
                self.output_message.publish()

                self.session.reasoning_context.append(
                    ContextMessage(content=text_content.text, role=RoleTypes.assistant)
                )
                self.stop()
                return

            self.session.reasoning_context.append(
                ContextMessage(
                    content=llm_response.content,
                    tool_calls=llm_response.tool_calls,
                    role=RoleTypes.assistant
                )
            )

            for tc in llm_response.tool_calls:
                tool_info = tc.get("tool", {})
                tool_name = tool_info.get("name")
                tool_args = tool_info.get("arguments", {})
                tool_call_id = tc.get("id")
                
                if not tool_name or not tool_call_id:
                    logger.error(f"Invalid tool call format: {tc}")
                    continue
                
                tr: ToolResponse = self.run_tool(tool_name, **tool_args)
                self.session.reasoning_context.append(
                    ContextMessage(content=str(tr), tool_call_id=tool_call_id, role=RoleTypes.tool)
                )
            
            # Break to return control to outer loop for iteration counting
            break


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
