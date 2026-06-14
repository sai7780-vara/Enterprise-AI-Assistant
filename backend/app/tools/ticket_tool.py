from app.mcp.client import mcp_client_manager
from app.core.logger import get_logger

logger = get_logger(__name__)

def create_ticket(title: str, description: str, priority: str) -> dict:
    """Creates a new IT ticket."""
    try:
        result = mcp_client_manager.call_tool("ticket-mcp", "create_ticket", {
            "title": title,
            "description": description,
            "priority": priority
        })
        return {
            "success": True,
            "data": result,
            "mcp_server": "ticket-mcp",
            "selected_tool": "create_ticket"
        }
    except Exception as e:
        logger.error("ticket_tool.create_ticket failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "mcp_server": "ticket-mcp",
            "selected_tool": "create_ticket"
        }

def get_ticket_status(ticket_id: str) -> dict:
    """Gets details for an IT support ticket."""
    try:
        result = mcp_client_manager.call_tool("ticket-mcp", "get_ticket_status", {"ticket_id": ticket_id})
        return {
            "success": True,
            "data": result,
            "mcp_server": "ticket-mcp",
            "selected_tool": "get_ticket_status"
        }
    except Exception as e:
        logger.error("ticket_tool.get_ticket_status failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "mcp_server": "ticket-mcp",
            "selected_tool": "get_ticket_status"
        }
