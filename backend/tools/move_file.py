import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class MoveFileTool(BaseTool):
    name = "move_resource"
    description = "Moves or renames a file or folder."
    parameters = {
        "type": "object",
        "properties": {
            "source_path": {
                "type": "string",
                "description": "Current path of the item"
            },
            "destination_path": {
                "type": "string",
                "description": "New path or name for the item"
            }
        },
        "required": ["source_path", "destination_path"]
    }

    def run(self, source_path: str, destination_path: str) -> ToolResponse:
        """Move or rename a file or folder."""
        logger.info(f"Moving '{source_path}' to '{destination_path}'")
        
        try:
            result = self.docker_engine.move_item(source_path, destination_path)

            if "error" in result:
                logger.error(f"Move failed: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Move failed: {result['error']}",
                    data=result
                )
            else:
                logger.info(f"Successfully moved '{source_path}' to '{destination_path}'")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=result.get('message', f"Moved '{source_path}' to '{destination_path}'"),
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error moving '{source_path}' to '{destination_path}': {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to move item: {str(e)}",
                data={"error": str(e)}
            )
