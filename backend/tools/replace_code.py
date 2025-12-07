import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class ReplaceCodeTool(BaseTool):
    name = "replace_code"
    description = "Replaces a specific block of code with new code. Search block must match exactly."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            },
            "search_block": {
                "type": "string",
                "description": "The exact code block to find"
            },
            "replace_block": {
                "type": "string",
                "description": "The new code block to insert"
            }
        },
        "required": ["file_path", "search_block", "replace_block"]
    }

    def run(self, file_path: str, search_block: str, replace_block: str) -> ToolResponse:
        """Replace a code block in a file."""
        logger.info(f"Replacing code in: {file_path}")
        
        try:
            result = self.docker_engine.replace_code(file_path, search_block, replace_block)

            if "error" in result:
                logger.error(f"Code replacement failed in {file_path}: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Replacement failed: {result['error']}",
                    data=result
                )
            else:
                logger.info(f"Code block replaced successfully in {file_path}")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=f"Code block replaced successfully in {file_path}",
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error replacing code in {file_path}: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to replace code: {str(e)}",
                data={"error": str(e)}
            )

