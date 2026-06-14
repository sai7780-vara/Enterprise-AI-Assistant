from app.services.gemini_service import gemini_service
from app.core.logger import get_logger

logger = get_logger(__name__)


class ITAgent:
    def __init__(self) -> None:
        self.agent_name = "IT Agent"

    def handle_query(self, query: str, state: dict = None) -> str:
        logger.info("IT Agent handling query: %s", query)
        
        hr_context = ""
        if state and state.get("hr_response"):
            hr_context = f"\n\n--- HR ONBOARDING CONTEXT (Prior Agent Decisions) ---\n{state['hr_response']}\n-----------------------------"
            
        system_prompt = (
            "You are the specialized IT Agent for our Enterprise AI Knowledge Assistant.\n"
            "You handle technical support, laptop requests, VPN issues, access requests, and other IT questions.\n"
            "Answer the user's question professionally, clearly, and helpfully. Provide basic troubleshooting steps or processes for raising access/equipment requests. Since this is a demonstration, you can invent reasonable mock policies if details are missing, but maintain a realistic and professional tone."
            f"{hr_context}\n\n"
            f"User Question: {query}\n"
            "Answer:"
        )
        return gemini_service.generate_reply(system_prompt)


it_agent = ITAgent()
