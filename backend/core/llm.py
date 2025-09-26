from typing import Dict
import json
from enum import Enum
import os
from typing import List

from openai.types.chat import ChatCompletion
from pydantic import BaseModel, Field, field_validator, FieldValidationInfo
from pydantic_settings import SettingsConfigDict

class LLMResponseStatus:
    SUCCESS: bool = True
    ERROR: bool = False


class LLMResponse(BaseModel):
    """Response model for completions from LLMs."""

    content: str = ""
    tool_calls: List[Dict] = []
    send_tokens: int = 0
    recv_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""
    status: int = LLMResponseStatus.ERROR


class OpenAIChatModel(str, Enum):
    """Enum for OpenAI Chat models"""

    GPT4 = "gpt-4"
    GPT4_32K = "gpt-4-32k"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4o = "gpt-4o-2024-11-20"
    GPT4o_MINI = "gpt-4o-mini"
    o3_MINI = "o3-mini"


class OpenaiConfig(BaseModel):
    """OpenAI Config"""

    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        extra="ignore",
    )

    llm_type: str = "openai"
    api_key: str = os.getenv("OPENAI_API_KEY")
    api_base: str = os.getenv("OPENAI_API_BASE")
    chat_model: str = Field(default=OpenAIChatModel.GPT4o)
    max_tokens: int = 4096
    temperature: float = 0.9
    top_p: float = 1
    timeout: int = 120
    

    @field_validator("api_key")
    @classmethod
    def validate_non_empty(cls, v, info: FieldValidationInfo):
        if not v:
            raise ValueError(
                f"{info.field_name} must not be empty. please set {info.field_name.upper()} environment variable."
            )
        return v


class OpenAIClient:
    def __init__(self, config: OpenaiConfig = None):
        """
        :param config: OpenAI Config
        """
        if config is None:
            config = OpenaiConfig()
        # Initialize config attributes
        self.api_key = config.api_key
        self.api_base = config.api_base
        self.chat_model = config.chat_model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.timeout = config.timeout
        try:
            import openai
        except ImportError:
            raise ImportError("Please install OpenAI python library.")

        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)


    def _format_messages(self, messages: list):
        """Format the messages to the format that OpenAI expects."""
        formatted_messages = []
        for message in messages:
            if message["role"] == "assistant" and message.get("tool_calls"):
                formatted_messages.append(
                    {
                        "role": message["role"],
                        "content": message["content"],
                        "tool_calls": [
                            {
                                "id": tool_call["id"],
                                "function": {
                                    "name": tool_call["tool"]["name"],
                                    "arguments": json.dumps(
                                        tool_call["tool"]["arguments"]
                                    ),
                                },
                                "type": tool_call["type"],
                            }
                            for tool_call in message["tool_calls"]
                        ],
                    }
                )
            else:
                formatted_messages.append(message)
        return formatted_messages

    def _format_tools(self, tools: list):
        """Format the tools to the format that OpenAI expects.

        **Example**::

            [
                {
                    "type": "function",
                    "function": {
                        "name": "get_delivery_date",
                        "description": "Get the delivery date for a customer's order.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "order_id": {
                                    "type": "string",
                                    "description": "The customer's order ID."
                                }
                            },
                            "required": ["order_id"],
                            "additionalProperties": False
                        }
                    }
                }
            ]
        """
        formatted_tools = []
        for tool in tools:
            formatted_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                    "strict": True,
                }
            )
        return formatted_tools

    def chat_completions(
        self, messages: list, tools: list = [], stop=None, response_format=None
    ):
        """Get completions for chat.

        docs: https://platform.openai.com/docs/guides/function-calling
        """
        params = {
            "model": self.chat_model,
            "messages": self._format_messages(messages),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop": stop,
            "timeout": self.timeout,
        }
        if tools:
            params["tools"] = self._format_tools(tools)
            params["tool_choice"] = "auto"

        if response_format:
            params["response_format"] = response_format

        try:
            response: ChatCompletion = self.client.chat.completions.create(**params)
        except Exception as e:
            print(f"Error: {e}")
            return LLMResponse(content=f"Error: {e}")

        return LLMResponse(
            content=response.choices[0].message.content or "",
            tool_calls=[
                {
                    "id": tool_call.id,
                    "tool": {
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                    },
                    "type": tool_call.type,
                }
                for tool_call in response.choices[0].message.tool_calls
            ]
            if response.choices[0].message.tool_calls
            else [],
            finish_reason=response.choices[0].finish_reason,
            send_tokens=response.usage.prompt_tokens,
            recv_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            status=LLMResponseStatus.SUCCESS,
        )