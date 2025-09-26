import json
from typing import List, Dict, Any
from enum import Enum
from pydantic import BaseModel
from backend.core.llm import OpenAIClient


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


def _to_openai_content_parts(parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert inbound content list to OpenAI message parts:
      - text => {"type":"text","text":"..."}
      - image_url => {"type":"image_url","image_url":{"url":"..."}}
    """
    out: List[Dict[str, Any]] = []
    for p in parts:
        t = p.get("type")
        if t == "text" and "text" in p:
            out.append({"type": "text", "text": p["text"]})
        elif t == "image_url":
            url = (
                p["image_url"]
                if isinstance(p.get("image_url"), str)
                else (p.get("image_url") or {}).get("url")
            )
            if url:
                out.append({"type": "image_url", "image_url": {"url": url}})
    return out


def generate_task_list(prompt_parts: List[Dict[str, Any]]) -> TaskListContent:
    """
    1) Formats content list into OpenAI Chat Completions `messages`
    2) Calls OpenAI with JSON Schema forcing TaskListContent
    3) Parses/validates JSON into TaskListContent
    """
    llm = OpenAIClient()

    user_content = _to_openai_content_parts(prompt_parts)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a task planner. Given the user's mixed input (text and images), "
                "break it down into a clear task list. "
                "Return ONLY JSON that matches the provided JSON schema."
            ),
        },
        {"role": "user", "content": user_content},
    ]

    schema = TaskListContent.model_json_schema()

    resp = llm.chat_completions(
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "task_list_content",
                "schema": schema,
                "strict": True,
            },
        },
        # temperature defaults from client; deterministic not required here
    )

    if not resp or not resp.content:
        raise ValueError("Empty response from LLM for task list.")

    data = json.loads(resp.content)
    return TaskListContent.model_validate(data)
