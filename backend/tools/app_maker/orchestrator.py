import json
from typing import Dict, List, Any, Literal
from pydantic import BaseModel
from backend.core.session import (
    OutputMessage,
    Session,
    TaskListContent,
    CanvasContent,
    CanvasStaticWebsiteOutput,
    CanvasSVGOutput,
)
from backend.tools.app_maker.task_chunker import generate_task_list
from backend.core.llm import OpenAIClient
from backend.tools.app_maker.code_generator.static_website_generator.core import StaticWebsiteGenerator
from backend.tools.app_maker.code_generator.svg_generator.core import SVGGenerator


class IntendedAppDecision(BaseModel):
    choice: Literal["svg", "static_website"]
    reason: str


def _to_openai_content_parts(parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


class AppMakerOrchestrator:
    def __init__(self, session: Session, output_message: OutputMessage):
        self.session = session
        self.output_message = output_message
        self.llm = OpenAIClient()

    def _determine_app_style(self, prompt_parts: List[Dict[str, Any]]) -> str:
        """
        Returns 'svg' or 'static_website' using JSON-schema constrained output.
        """
        system_prompt = (
            "Classify the user's request as either an SVG image or a static website.\n"
            "Choose 'svg' for logos, icons, single diagrams/graphics.\n"
            "Choose 'static_website' for pages/sites with layout, CSS, JS, navigation, or multiple sections.\n"
            "Return ONLY JSON matching the provided schema."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _to_openai_content_parts(prompt_parts)},
        ]

        schema = IntendedAppDecision.model_json_schema()

        response = self.llm.chat_completions(
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "intended_app_decision",
                    "schema": schema,
                    "strict": True,
                },
            },
        )

        if response and response.content:
            try:
                decision = IntendedAppDecision.model_validate(json.loads(response.content))
                return decision.choice
            except Exception:
                pass

        return "static_website"

    def run(self, prompt_parts: List[Dict[str, Any]], max_iterations: int = 10):
        app_style = self._determine_app_style(prompt_parts)

        task_list_content: TaskListContent = generate_task_list(prompt_parts)
        self.output_message.content.append(task_list_content)
        self.output_message.publish()

        tasks = task_list_content.task_list

        if app_style == "svg":
            generator = SVGGenerator()
            canvas_output = CanvasSVGOutput(code="")
        else:
            generator = StaticWebsiteGenerator()
            canvas_output = CanvasStaticWebsiteOutput(html="", css="", js="")

        final_canvas = CanvasContent(content=canvas_output)
        self.output_message.content.append(final_canvas)

        for task in tasks:
            canvas_output = generator.generate(prompt_parts, task.task, canvas_output)
            final_canvas.content = canvas_output
            self.output_message.content.append(final_canvas)
            self.output_message.publish()

        return final_canvas
