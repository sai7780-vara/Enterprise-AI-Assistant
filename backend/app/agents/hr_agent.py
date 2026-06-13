from app.services.gemini_service import gemini_service
from app.core.logger import get_logger

logger = get_logger(__name__)


class HRAgent:
    def __init__(self) -> None:
        self.agent_name = "HR Agent"

    def handle_query(self, query: str) -> str:
        logger.info("HR Agent handling query: %s", query)
        system_prompt = (
            "You are the specialized HR Agent for our Enterprise AI Knowledge Assistant.\n"
            "You are an expert on company HR policies, including leave policies, benefits, holidays, and employee handbook queries.\n"
            "Answer the user's question professionally, clearly, and helpfully. Since this is a demonstration, you can invent reasonable mock policies if details are missing, but maintain a realistic and professional tone.\n\n"
            f"User Question: {query}\n"
            "Answer:"
        )
        return gemini_service.generate_reply(system_prompt)


hr_agent = HRAgent()
