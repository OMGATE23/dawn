import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class GetServerLogsTool(BaseTool):
    active = False
    name = "get_server_logs"
    description = "Retrieves the last N lines of logs from the running container."
    parameters = {
        "type": "object",
        "properties": {
            "lines": {
                "type": "integer",
                "description": "Number of lines to retrieve (default: 50)",
                "default": 50
            }
        },
        "required": []
    }

    def run(self, lines: int = 50) -> ToolResponse:
        """Retrieve server logs from the container."""
        logger.info(f"Fetching last {lines} server logs...")
        
        try:
            result = self.docker_engine.get_server_logs(lines)
            
            if "error" in result:
                logger.error(f"Failed to retrieve logs: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Failed to retrieve logs: {result['error']}",
                    data=result
                )
            else:
                logger.info(f"Successfully retrieved {lines} lines of logs")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=f"Retrieved last {lines} lines of logs",
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error retrieving server logs: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to retrieve logs: {str(e)}",
                data={"error": str(e)}
            )