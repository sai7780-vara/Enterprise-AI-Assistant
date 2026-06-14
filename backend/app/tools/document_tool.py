from app.mcp.client import mcp_client_manager
from app.core.logger import get_logger

logger = get_logger(__name__)

def search_documents(query: str, top_k: int = 4) -> dict:
    """Searches vectorized documents."""
    try:
        result = mcp_client_manager.call_tool("document-search-mcp", "search_documents", {
            "query": query,
            "top_k": top_k
        })
        return {
            "success": True,
            "data": result,
            "mcp_server": "document-search-mcp",
            "selected_tool": "search_documents"
        }
    except Exception as e:
        logger.error("document_tool.search_documents failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "mcp_server": "document-search-mcp",
            "selected_tool": "search_documents"
        }

def get_sources(doc_id: str) -> dict:
    """Gets citation details for a source document."""
    try:
        result = mcp_client_manager.call_tool("document-search-mcp", "get_sources", {"doc_id": doc_id})
        return {
            "success": True,
            "data": result,
            "mcp_server": "document-search-mcp",
            "selected_tool": "get_sources"
        }
    except Exception as e:
        logger.error("document_tool.get_sources failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "mcp_server": "document-search-mcp",
            "selected_tool": "get_sources"
        }
