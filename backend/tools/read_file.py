import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class ReadFileFormattedTool(BaseTool):
    name = "read_file"
    description = "Reads a file and returns it in a Markdown table format with line numbers."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["file_path"]
    }

    def run(self, file_path: str) -> ToolResponse:
        """Read a file and return its content in a formatted table."""
        logger.info(f"Reading file (formatted): {file_path}")
        
        try:
            result = self.docker_engine.read_file_formatted(file_path)

            if "error" in result:
                logger.error(f"Failed to read file {file_path}: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Failed to read file: {result['error']}",
                    data=result
                )
            else:
                logger.info(f"File read successfully: {file_path}")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=f"File read successfully: {file_path}",
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error reading file {file_path}: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to read file: {str(e)}",
                data={"error": str(e)}
            )
