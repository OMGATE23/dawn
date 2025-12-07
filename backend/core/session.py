# session.py
from enum import Enum
from datetime import datetime
from typing import Any, Optional, List, Union, TYPE_CHECKING
import uuid

from pydantic import BaseModel, Field, ConfigDict

from database.db import SQLiteDB
from core.enums import ToolStatus
from flask_socketio import emit

from pathlib import Path
from core.docker_orchestrator import DockerOrchestrator


class RoleTypes(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class MsgStatus(str, Enum):
    progress = "progress"
    success = "success"
    error = "error"


class MsgType(str, Enum):
    input = "input"
    output = "output"


class ToolContent(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        validate_default=True,
    )
    
    type: str = "tool"
    tool_name: str
    tool_args: dict
    tool_response: Any
    tool_status: ToolStatus

class TextContent(BaseModel):
    type: str = "text"
    text: Optional[str] = None
    status: MsgStatus = MsgStatus.progress

class ImageContent(BaseModel):
    type: str = "image_url"
    image_url: str

class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class TaskContent(BaseModel):
    type: str = "task"
    task: str
    status: TaskStatus

class TaskListContent(BaseModel):
    type: str = "task_list"
    title: str
    task_list: List[TaskContent]

class CanvasSVGOutput(BaseModel):
    type: str = "svg"
    code: str


class CanvasStaticWebsiteOutput(BaseModel):
    type: str = "static_website"
    html: str
    css: str
    js: str


class CanvasContent(BaseModel):
    type: str = "canvas"
    content: Union[CanvasSVGOutput, CanvasStaticWebsiteOutput]

class BaseMessage(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        validate_default=True,
    )

    session_id: str
    conv_id: str
    msg_type: MsgType
    actions: List[str] = []
    tools: List[str] = []
    content: List[
        Union[
            dict,
            TextContent,
            ImageContent,
            ToolContent,
            TaskListContent,
            CanvasContent
        ]
    ] = []
    status: MsgStatus = MsgStatus.success
    msg_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )


class InputMessage(BaseMessage):
    db: SQLiteDB
    msg_type: MsgType = MsgType.input

    def publish(self):
        self.db.add_or_update_msg_to_conv(**self.model_dump(exclude={"db"}))


class OutputMessage(BaseMessage):
    db: SQLiteDB = Field(exclude=True)
    msg_type: MsgType = MsgType.output
    status: MsgStatus = MsgStatus.progress

    def update_status(self, status: MsgStatus):
        self.status = status
        self.publish()

    def publish(self):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            emit("chat", self.model_dump(), namespace="/chat")
        except Exception as e:
            logger.error(f"Failed to emit message via socket: {e}")
        
        try:
            self.db.add_or_update_msg_to_conv(**self.model_dump())
        except Exception as e:
            logger.error(f"Failed to save message to database: {e}")


class ContextMessage(BaseModel):

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        use_enum_values=True,
    )

    content: Optional[Union[List[dict], str]] = None
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    role: RoleTypes = RoleTypes.system

    def to_llm_msg(self):
        import logging
        logger = logging.getLogger(__name__)
        
        msg = {
            "role": self.role,
            "content": self.content,
        }
        if self.role == RoleTypes.system:
            return msg

        if self.role == RoleTypes.user:
            return msg

        if self.role == RoleTypes.assistant:
            if self.tool_calls:
                msg["tool_calls"] = self.tool_calls
            if not self.content:
                msg["content"] = []
            return msg

        if self.role == RoleTypes.tool:
            msg["tool_call_id"] = self.tool_call_id
            return msg
        
        logger.warning(f"Unexpected role type: {self.role}")
        return msg

    @classmethod
    def from_json(cls, json_data):
        return cls(**json_data)


class Session:

    def __init__(
        self,
        db: SQLiteDB,
        workspace_root: str,
        session_id: str = "",
        conv_id: str = "",
        **kwargs,
    ):
        self.db = db
        self.session_id = session_id
        self.conv_id = conv_id
        self.conversations = []
        self.reasoning_context = []
        self.state = {}
        self.output_message = OutputMessage(
            db=self.db, session_id=self.session_id, conv_id=self.conv_id, msg_id=str(uuid.uuid4())
        )

        self.docker_engine = DockerOrchestrator(
            session_id=self.session_id,
            workspace_root=Path(workspace_root)
        )

        self.get_context_messages()

    def save_context_messages(self):
        context = {
            "reasoning": [message.to_llm_msg() for message in self.reasoning_context],
        }
        self.db.add_or_update_context_msg(self.session_id, context)

    def get_context_messages(self):
        if not self.reasoning_context:
            context = self.db.get_context_messages(self.session_id)
            self.reasoning_context = [
                ContextMessage.from_json(message)
                for message in context.get("reasoning", [])
            ]

        return self.reasoning_context

    def create(self):
        self.db.create_session(session_id=self.session_id)

    def get(self):
        session = self.db.get_session(self.session_id)
        conversation = self.db.get_conversations(self.session_id)
        session["conversation"] = conversation
        return session

    def get_all(self):
        return self.db.get_sessions()

    def delete(self):
        return self.db.delete_session(self.session_id)