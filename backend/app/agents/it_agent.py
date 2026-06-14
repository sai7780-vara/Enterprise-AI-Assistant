import re
import json
from app.services.gemini_service import gemini_service
from app.core.logger import get_logger
from app.tools import ticket_tool

logger = get_logger(__name__)


class ITAgent:
    def __init__(self) -> None:
        self.agent_name = "IT Agent"

    def handle_query(self, query: str, state: dict = None) -> str:
        logger.info("IT Agent handling query: %s", query)
        
        if state is not None:
            state["selected_tool"] = None
            state["mcp_server"] = None
            
        tool_info = ""
        
        # Check if checking status of a ticket
        ticket_match = re.search(r'\b(TCK-\d{4})\b', query, re.IGNORECASE)
        if ticket_match:
            ticket_id = ticket_match.group(1).upper()
            res = ticket_tool.get_ticket_status(ticket_id)
            if state is not None:
                state["selected_tool"] = res.get("selected_tool")
                state["mcp_server"] = res.get("mcp_server")
            tool_info = f"\n\n--- IT Ticket Status Tool Result ---\n{json.dumps(res)}\n-----------------------------------"
        # Check if query is reporting a support problem / asking to create ticket
        elif any(kw in query.lower() for kw in ["not working", "vpn", "issue", "setup", "error", "ticket", "create", "broken", "laptop"]):
            res = ticket_tool.create_ticket(
                title="Support Request: " + (query[:40] + "..." if len(query) > 40 else query),
                description=query,
                priority="High"
            )
            if state is not None:
                state["selected_tool"] = res.get("selected_tool")
                state["mcp_server"] = res.get("mcp_server")
            tool_info = f"\n\n--- IT Ticket Creation Tool Result ---\n{json.dumps(res)}\n-------------------------------------"

        hr_context = ""
        if state and state.get("hr_response"):
            hr_context = f"\n\n--- HR ONBOARDING CONTEXT (Prior Agent Decisions) ---\n{state['hr_response']}\n-----------------------------"
            
        system_prompt = (
            "You are the specialized IT Agent for our Enterprise AI Knowledge Assistant.\n"
            "You handle technical support, laptop requests, VPN issues, access requests, and other IT questions.\n"
            "Answer the user's question professionally, clearly, and helpfully. Provide basic troubleshooting steps or processes. Ground your response in any ticket/tool results provided below.\n"
            f"{hr_context}"
            f"{tool_info}\n\n"
            f"User Question: {query}\n"
            "Answer:"
        )
        return gemini_service.generate_reply(system_prompt)


it_agent = ITAgent()
