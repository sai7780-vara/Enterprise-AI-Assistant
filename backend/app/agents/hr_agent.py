import re
import json
from app.services.gemini_service import gemini_service
from app.core.logger import get_logger
from app.tools import employee_tool

logger = get_logger(__name__)


class HRAgent:
    def __init__(self) -> None:
        self.agent_name = "HR Agent"

    def handle_query(self, query: str, state: dict = None) -> str:
        logger.info("HR Agent handling query: %s", query)
        
        if state is not None:
            state["selected_tool"] = None
            state["mcp_server"] = None
            
        tool_info = ""
        
        # Check if looking up by employee ID
        id_match = re.search(r'\b(?:employee\s+)?(\d{3,})\b', query)
        if id_match:
            emp_id = int(id_match.group(1))
            res = employee_tool.get_employee(emp_id)
            if state is not None:
                state["selected_tool"] = res.get("selected_tool")
                state["mcp_server"] = res.get("mcp_server")
            tool_info = f"\n\n--- Employee DB Tool Result ---\n{json.dumps(res)}\n---------------------------------"
        # Check if searching by name
        elif any(kw in query.lower() for kw in ["search", "find", "get details", "about", "for"]):
            name_match = re.search(r'(?:search for|find|details for|about|employee)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', query, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else None
            if not name:
                # fallback to checking capitalized words
                words = [w for w in query.split() if w.istitle() and w.lower() not in ("what", "how", "why", "my", "employee", "details", "for")]
                if words:
                    name = words[0]
            if name:
                res = employee_tool.search_employee(name)
                if state is not None:
                    state["selected_tool"] = res.get("selected_tool")
                    state["mcp_server"] = res.get("mcp_server")
                tool_info = f"\n\n--- Employee DB Tool Result ---\n{json.dumps(res)}\n---------------------------------"

        system_prompt = (
            "You are the specialized HR Agent for our Enterprise AI Knowledge Assistant.\n"
            "You are an expert on company HR policies, including leave policies, benefits, holidays, and employee handbook queries.\n"
            "Answer the user's question professionally, clearly, and helpfully. Ground your response in any tool result provided below.\n\n"
            f"User Question: {query}"
            f"{tool_info}\n"
            "Answer:"
        )
        return gemini_service.generate_reply(system_prompt)


hr_agent = HRAgent()
