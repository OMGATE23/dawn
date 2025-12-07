import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class StartContainerTool(BaseTool):
    name = "start_container"
    description = "Starts or restarts the Docker container environment for the project. Returns the localhost URL."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def run(self) -> ToolResponse:
        """Start or restart the Docker container."""
        logger.info(f"Initializing container environment for session_id: {self.docker_engine.session_id}")

        try:
            result = self.docker_engine.get_container()

            if "url" in result:
                logger.info(f"Container started successfully at {result['url']}")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=f"Container started! Access the app at: {result['url']}",
                    data=result
                )
            else:
                logger.error(f"Failed to start container: {result.get('error')}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Failed to start container: {result.get('error', 'Unknown error')}",
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error starting container: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to start container: {str(e)}",
                data={"error": str(e)}
            )