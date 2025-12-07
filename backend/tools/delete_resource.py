import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class DeleteResourceTool(BaseTool):
    name = "delete_resource"
    description = "Deletes a file or folder permanently."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to delete"
            }
        },
        "required": ["path"]
    }

    def run(self, path: str) -> ToolResponse:
        """Delete a file or folder permanently."""
        logger.warning(f"Deleting: {path}")
        
        try:
            result = self.docker_engine.delete_item(path)
            
            if "error" in result:
                logger.error(f"Deletion failed for {path}: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Deletion failed: {result['error']}",
                    data=result
                )
            else:
                logger.info(f"Successfully deleted: {path}")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=result.get('message', f"Successfully deleted: {path}"),
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error deleting {path}: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to delete: {str(e)}",
                data={"error": str(e)}
            )
