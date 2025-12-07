import logging

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel

from core.docker_orchestrator import DockerOrchestrator
from core.session import Session, OutputMessage
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class ToolResponse(BaseModel):
    """Data model for responses from tools."""

    status: ToolStatus = ToolStatus.SUCCESS
    message: str = ""
    data: Any = None


class BaseTool(ABC):
    """Interface for all tools. All tools should inherit from this class."""
    active = True

    def __init__(self, session: Session, **kwargs):
        self.session: Session = session
        self.docker_engine: DockerOrchestrator = self.session.docker_engine
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
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def run(self, *args, **kwargs) -> ToolResponse:
        """Execute the tool - must be implemented by subclasses."""
        pass

    def safe_call(self, *args, **kwargs):
        try:
            return self.run(*args, **kwargs)

        except Exception as e:
            logger.exception(f"error in {self.name} tool: {e}")
            return ToolResponse(status=ToolStatus.ERROR, message=str(e))
