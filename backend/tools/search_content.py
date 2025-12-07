import logging
from tools.base import BaseTool, ToolResponse
from core.enums import ToolStatus

logger = logging.getLogger(__name__)


class SearchContentTool(BaseTool):
    name = "search_content"
    description = "Searches for a specific string pattern across all files."
    parameters = {
        "type": "object",
        "properties": {
            "search_term": {
                "type": "string",
                "description": "The string to grep for"
            }
        },
        "required": ["search_term"]
    }

    def run(self, search_term: str) -> ToolResponse:
        """Search for a string pattern across all files."""
        logger.info(f"Searching for: {search_term}")
        
        try:
            result = self.docker_engine.search_content(search_term)
            
            if isinstance(result, dict) and "error" in result:
                logger.error(f"Search failed: {result['error']}")
                return ToolResponse(
                    status=ToolStatus.ERROR,
                    message=f"Search failed: {result['error']}",
                    data=result
                )
            
            match_count = len(result) if isinstance(result, list) else 0
            logger.info(f"Found {match_count} matches for '{search_term}'")
            return ToolResponse(
                status=ToolStatus.SUCCESS,
                message=f"Found {match_count} matches",
                data={"matches": result, "count": match_count, "search_term": search_term}
            )
        except Exception as e:
            logger.exception(f"Error searching for '{search_term}': {e}")
            return ToolResponse(
                status=ToolStatus.ERROR,
                message=f"Failed to search: {str(e)}",
                data={"error": str(e)}
            )