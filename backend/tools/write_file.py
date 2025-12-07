import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Creates a new file or folder, or overwrites an existing file with new content."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file or folder to create (e.g., 'src/App.jsx' or 'src/components')"
            },
            "type_of_content": {
                "type": "string",
                "description": "Either 'file' or 'folder'",
                "enum": ["file", "folder"]
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file (only required if type_of_content is 'file')",
                "default": ""
            }
        },
        "required": ["path", "type_of_content"]
    }

    def run(self, path: str, type_of_content: str, content: str = "") -> ToolResponse:
        """Create or overwrite a file or folder."""
        logger.info(f"Writing {type_of_content}: {path}")
        
        try:
            result = self.docker_engine.write_file_folder(path, type_of_content, content)
            
            if "error" in result:
                logger.error(f"Failed to write {type_of_content} {path}: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Failed to write {type_of_content}: {result['error']}",
                    data=result
                )
            else:
                logger.info(f"Successfully created {type_of_content}: {path}")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=result.get('message', f"{type_of_content.capitalize()} created: {path}"),
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error writing {type_of_content} {path}: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to write {type_of_content}: {str(e)}",
                data={"error": str(e)}
            )

