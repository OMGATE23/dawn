import logging

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

from core.session import Session, OutputMessage
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class ToolResponse(BaseModel):
    """Data model for respones from tools."""

    status: ToolStatus = ToolStatus.SUCCESS
    message: str = ""
    data: Any = None


class BaseTool(ABC):
    """Interface for all tools. All tools should inherit from this class."""

    def __init__(self, session: Session, **kwargs):
        self.session: Session = session
        self.output_message: OutputMessage = self.session.output_message

    def to_llm_format(self):
        """Convert the tool to LLM tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    @property
    @abstractmethod
    def name(self):
        """Tool name - must be implemented by subclasses."""
        pass

    @property
    @abstractmethod
    def description(self):
        """Tool description - must be implemented by subclasses."""
        pass

    @property
    @abstractmethod
    def parameters(self):
        """Tool parameters schema - must be implemented by subclasses."""
        pass

    def safe_call(self, *args, **kwargs):
        try:
            return self.run(*args, **kwargs)

        except Exception as e:
            logger.exception(f"error in {self.name} tool: {e}")
            return ToolResponse(status=ToolStatus.ERROR, message=str(e))

    @abstractmethod
    def run(self, *args, **kwargs) -> ToolResponse:
        """Execute the tool - must be implemented by subclasses."""
        pass