import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class LintCheckTool(BaseTool):
    name = "check_lint_errors"
    description = "Runs TypeScript compiler (tsc) to check for errors."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def run(self) -> ToolResponse:
        """Run TypeScript compiler to check for errors."""
        logger.info("Running type checks (TSC)...")
        
        try:
            result = self.docker_engine.check_lint_errors()
            
            if "error" in result:
                logger.error(f"Lint check failed: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Lint check failed: {result['error']}",
                    data=result
                )
            
            exit_code = result.get('exit_code', 1)
            if exit_code == 0:
                logger.info("No linting errors found")
                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message="No linting errors found",
                    data=result
                )
            else:
                logger.warning("Linting errors detected")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message="Linting errors detected",
                    data=result
                )
        except Exception as e:
            logger.exception(f"Error running lint check: {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to run lint check: {str(e)}",
                data={"error": str(e)}
            )
