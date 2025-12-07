import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "Lists files and folders in a specific directory."
    parameters = {
        "type": "object",
        "properties": {
            "subpath": {
                "type": "string",
                "description": "The folder path to list (default: '.')",
                "default": "."
            }
        },
        "required": []
    }
    
    def run(self, subpath: str = ".") -> ToolResponse:
        """List files and folders in a directory."""
        logger.info(f"Listing files in: {subpath}")
        
        try:
            result = self.docker_engine.list_files(subpath)

            if isinstance(result, dict) and "error" in result:
                logger.error(f"Failed to list files in {subpath}: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Failed to list files: {result['error']}",
                    data=result
                )
            
            count = len(result) if isinstance(result, list) else 0
            logger.info(f"Found {count} items in {subpath}")
            return ToolResponse(
                status=ToolStatus.SUCCESS,
                message=f"Found {count} items in {subpath}",
                data={"items": result, "count": count}
            )
        except Exception as e:
            logger.exception(f"Error listing files in {subpath}: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to list files: {str(e)}",
                data={"error": str(e)}
            )