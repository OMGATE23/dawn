import json
from typing import Dict, List, Any
from pydantic import BaseModel
from backend.core.llm import OpenAIClient
from backend.core.session import CanvasStaticWebsiteOutput


class _StaticSiteSchema(BaseModel):
    html: str
    css: str
    js: str


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


class StaticWebsiteGenerator:
    def __init__(self):
        self.llm = OpenAIClient()

    def generate(
        self,
        prompt_parts: List[Dict[str, Any]],
        task: str,
        current_code: CanvasStaticWebsiteOutput,
    ) -> CanvasStaticWebsiteOutput:

        system_prompt = (
            "You are an expert web developer (HTML, CSS, JS). "
            "Generate updates for a static website based on the user's prompt and the current task. "
            "Return ONLY a JSON object with keys 'html', 'css', and 'js'. "
            "Each value MUST be raw code text with NO markdown code fences, NO backticks, and NO commentary. "
            "The HTML must be a single page that references external 'styles.css' and 'script.js'."
        )

        user_parts = _to_openai_content_parts(prompt_parts)
        user_parts.extend([
            {"type": "text", "text": f"Current Task: {task}"},
            {"type": "text", "text": f"Existing HTML:\n{current_code.html}"},
            {"type": "text", "text": f"Existing CSS:\n{current_code.css}"},
            {"type": "text", "text": f"Existing JS:\n{current_code.js}"},
        ])

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_parts},
        ]

        schema = _StaticSiteSchema.model_json_schema()

        response = self.llm.chat_completions(
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "static_site_schema",
                    "schema": schema,
                    "strict": True,
                },
            },
        )

        if not response or not response.content:
            raise ValueError("Empty response from LLM for static site generation.")

        data = json.loads(response.content)
        validated = _StaticSiteSchema.model_validate(data)
        return CanvasStaticWebsiteOutput(**validated.model_dump())
