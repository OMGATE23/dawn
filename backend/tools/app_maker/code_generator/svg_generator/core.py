import json
from typing import Dict, List, Any
from pydantic import BaseModel
from backend.core.llm import OpenAIClient
from backend.core.session import CanvasSVGOutput


class _SVGSchema(BaseModel):
    code: str


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


class SVGGenerator:
    def __init__(self):
        self.llm = OpenAIClient()

    def generate(
        self,
        prompt_parts: List[Dict[str, Any]],
        task: str,
        current_code: CanvasSVGOutput,
    ) -> CanvasSVGOutput:

        system_prompt = (
            "You are an expert in generating SVG images. "
            "Return ONLY a JSON object with a single key 'code' containing the COMPLETE SVG markup. "
            "The value MUST be raw SVG code with NO markdown code fences, NO backticks, and NO commentary."
        )

        user_parts = _to_openai_content_parts(prompt_parts)
        user_parts.extend([
            {"type": "text", "text": f"Current Task: {task}"},
            {"type": "text", "text": f"Existing SVG:\n{current_code.code}"},
        ])

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_parts},
        ]

        schema = _SVGSchema.model_json_schema()

        response = self.llm.chat_completions(
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "svg_schema",
                    "schema": schema,
                    "strict": True,
                },
            },
        )

        if not response or not response.content:
            raise ValueError("Empty response from LLM for SVG generation.")

        data = json.loads(response.content)
        validated = _SVGSchema.model_validate(data)
        return CanvasSVGOutput(**validated.model_dump())
