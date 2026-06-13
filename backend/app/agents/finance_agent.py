from app.services.gemini_service import gemini_service
from app.core.logger import get_logger

logger = get_logger(__name__)


class FinanceAgent:
    def __init__(self) -> None:
        self.agent_name = "Finance Agent"

    def handle_query(self, query: str) -> str:
        logger.info("Finance Agent handling query: %s", query)
        system_prompt = (
            "You are the specialized Finance Agent for our Enterprise AI Knowledge Assistant.\n"
            "You are an expert on company finance procedures, including expenses, reimbursements, invoices, and budget-related questions.\n"
            "Answer the user's question professionally, clearly, and helpfully. State guidelines on how to file reports, what is reimbursable, or invoice processing. Since this is a demonstration, you can invent reasonable mock policies if details are missing, but maintain a realistic and professional tone.\n\n"
            f"User Question: {query}\n"
            "Answer:"
        )
        return gemini_service.generate_reply(system_prompt)


finance_agent = FinanceAgent()
