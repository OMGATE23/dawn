import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Executes a shell command inside the container."
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute (e.g., 'npm install', 'ls -la')"
            }
        },
        "required": ["command"]
    }

    def run(self, command: str) -> ToolResponse:
        """Execute a shell command in the container."""
        logger.info(f"Executing shell command: {command}")
        
        try:
            result = self.docker_engine.run_command(command)
            
            if "error" in result:
                logger.error(f"Command execution failed: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Command failed: {result['error']}",
                    data=result
                )
            
            exit_code = result.get("exit_code", 0)
            if exit_code != 0:
                logger.warning(f"Command exited with code {exit_code}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Command exited with code {exit_code}",
                    data=result
                )
            
            logger.info(f"Command executed successfully: {command}")
            return ToolResponse(
                status=ToolStatus.SUCCESS,
                message="Command executed successfully",
                data=result
            )
        except Exception as e:
            logger.exception(f"Error executing command {command}: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to execute command: {str(e)}",
                data={"error": str(e)}
            )
