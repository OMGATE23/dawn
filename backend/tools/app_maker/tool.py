from backend.tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus
from core.session import Session
from typing import List, Dict, Any
from .orchestrator import AppMakerOrchestrator


class AppMakerTool(BaseTool):
    def __init__(self, session: Session):
        super().__init__(session)

    @property
    def name(self):
        return "generate_app"

    @property
    def description(self):
        return "Generates an application (either a static website or an SVG image) based on a prompt containing text and images."

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "prompt_parts": {
                    "type": "array",
                    "description": "A list of content parts for the prompt, which can be text or images.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["text", "image_url"]},
                            "text": {"type": "string"},
                            "image_url": {
                                "type": "object",
                                "properties": {"url": {"type": "string", "format": "uri"}},
                            },
                        },
                        "required": ["type"],
                    },
                }
            },
            "required": ["prompt_parts"],
        }

    def run(self, prompt_parts: List[Dict[str, Any]]) -> ToolResponse:
        try:
            orchestrator = AppMakerOrchestrator(
                session=self.session,
                output_message=self.session.output_message
            )
            canvas_content = orchestrator.run(prompt_parts)
            return ToolResponse(
                status=ToolStatus.SUCCESS,
                message="Successfully generated application.",
                data=canvas_content.model_dump(),
            )
        except Exception as e:
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to generate application: {str(e)}",
                data={"error": str(e)},
            )
