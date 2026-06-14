from typing import List, Tuple
from app.services.gemini_service import gemini_service
from app.core.logger import get_logger

# Import other agents
from app.agents.hr_agent import hr_agent
from app.agents.finance_agent import finance_agent
from app.agents.it_agent import it_agent
from app.agents.rag_agent import rag_agent

logger = get_logger(__name__)


class SupervisorAgent:
    def __init__(self) -> None:
        self.agent_name = "Supervisor Agent"

    def classify(self, message: str) -> str:
        """Helper to classify user message intent using Gemini."""
        classify_prompt = (
            "You are the Supervisor Agent for an enterprise AI assistant system.\n"
            "Your job is to classify the user's query into exactly one of these categories:\n"
            "- 'ONBOARDING': Specifically for requests to *create, plan, or prepare* comprehensive onboarding plans or schedules for new hires (e.g., 'Create onboarding plan for a new employee').\n"
            "- 'TRAVEL': Specifically for requests to *prepare or plan* travel reimbursement plans or travel itineraries (e.g., 'Prepare travel reimbursement plan').\n"
            "- 'CROSS_FUNCTIONAL': Specifically for requests to *create or prepare* cross-departmental setups or cross-functional employee plans (e.g., 'Create cross-functional employee setup plan').\n"
            "- 'HR': For simple/general questions about human resources, leave policies, holidays, handbook, or benefits (e.g., 'What is the leave policy?', 'How many holidays do we have?').\n"
            "- 'FINANCE': For simple/general questions about expense reports, expenses, invoicing, or simple budget inquiries (e.g., 'How to submit an expense report?', 'Where do I submit invoices?').\n"
            "- 'IT': For simple/general questions about tech setup, VPN, laptops, passwords, or systems access (e.g., 'My VPN is not working', 'How to set up my laptop?').\n"
            "- 'RAG': For general queries asking to summarize, search, or extract information from uploaded files/PDFs (e.g., 'Summarize the uploaded Transformer paper', 'What does the PDF say?').\n\n"
            "Classification Rules:\n"
            "1. If the user asks a simple question about leave, expense reports, VPN, or uploaded documents, classify it as HR, FINANCE, IT, or RAG respectively. DO NOT classify them as ONBOARDING or TRAVEL or CROSS_FUNCTIONAL unless they explicitly ask to CREATE A PLAN/SCHEDULE.\n"
            "2. Respond ONLY with one of the following uppercase category names: ONBOARDING, TRAVEL, CROSS_FUNCTIONAL, HR, FINANCE, IT, or RAG.\n"
            "3. Do not include any other text, explanation, or punctuation. Just the uppercase name.\n\n"
            f"User Query: {message}\n"
            "Category:"
        )
        try:
            category = gemini_service.generate_reply(classify_prompt)
            logger.info("Raw supervisor classification: '%s'", category)
            clean_category = "".join(c for c in category if c.isalnum()).upper()
            return clean_category
        except Exception as exc:
            logger.exception("Supervisor classification failed, defaulting to RAG: %s", exc)
            return "RAG"

    def route_and_resolve(self, message: str, use_rag: bool = True, top_k: int = 4) -> Tuple[str, List[dict], float, str]:
        """Analyze user query, decide which agent should handle it, and route it."""
        logger.info("Supervisor Agent analyzing query: %s", message)
        clean_category = self.classify(message)
        logger.info("Supervisor classified query as: %s", clean_category)

        # Route the request to the correct agent
        if clean_category == "HR":
            reply = hr_agent.handle_query(message)
            return reply, [], 0.0, hr_agent.agent_name
        elif clean_category == "FINANCE":
            reply = finance_agent.handle_query(message)
            return reply, [], 0.0, finance_agent.agent_name
        elif clean_category == "IT":
            reply = it_agent.handle_query(message)
            return reply, [], 0.0, it_agent.agent_name
        else:
            # Default to RAG Agent for RAG category, unrecognized categories, or multi-agent fallbacks
            reply, sources, confidence = rag_agent.handle_query(message, use_rag=use_rag, top_k=top_k)
            return reply, sources, confidence, rag_agent.agent_name



supervisor_agent = SupervisorAgent()
