from app.mcp.client import mcp_client_manager
from app.core.logger import get_logger

logger = get_logger(__name__)

def get_employee(emp_id: int) -> dict:
    """Gets details for an employee by ID."""
    try:
        result = mcp_client_manager.call_tool("employee-db-mcp", "get_employee", {"id": emp_id})
        return {
            "success": True,
            "data": result,
            "mcp_server": "employee-db-mcp",
            "selected_tool": "get_employee"
        }
    except Exception as e:
        logger.error("employee_tool.get_employee failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "mcp_server": "employee-db-mcp",
            "selected_tool": "get_employee"
        }

def search_employee(name: str) -> dict:
    """Searches for employees matching a name substring."""
    try:
        result = mcp_client_manager.call_tool("employee-db-mcp", "search_employee", {"name": name})
        return {
            "success": True,
            "data": result,
            "mcp_server": "employee-db-mcp",
            "selected_tool": "search_employee"
        }
    except Exception as e:
        logger.error("employee_tool.search_employee failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "mcp_server": "employee-db-mcp",
            "selected_tool": "search_employee"
        }

def create_employee(name: str, department: str, email: str, role: str) -> dict:
    """Registers a new employee."""
    try:
        result = mcp_client_manager.call_tool("employee-db-mcp", "create_employee", {
            "name": name,
            "department": department,
            "email": email,
            "role": role
        })
        return {
            "success": True,
            "data": result,
            "mcp_server": "employee-db-mcp",
            "selected_tool": "create_employee"
        }
    except Exception as e:
        logger.error("employee_tool.create_employee failed: %s", e)
        return {
            "success": False,
            "error": str(e),
            "mcp_server": "employee-db-mcp",
            "selected_tool": "create_employee"
        }
