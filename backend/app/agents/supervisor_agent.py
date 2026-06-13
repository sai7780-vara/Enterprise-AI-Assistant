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

    def route_and_resolve(self, message: str, use_rag: bool = True, top_k: int = 4) -> Tuple[str, List[dict], float, str]:
        """Analyze user query, decide which agent should handle it, and route it."""
        logger.info("Supervisor Agent analyzing query: %s", message)

        classify_prompt = (
            "You are the Supervisor Agent for an enterprise AI assistant system.\n"
            "Your job is to classify the user's query into exactly one of these categories:\n"
            "- 'HR': For questions about leave policies, benefits, holidays, and employee handbook queries.\n"
            "- 'FINANCE': For questions about expenses, reimbursements, invoices, and budget-related questions.\n"
            "- 'IT': For questions about laptop requests, VPN issues, access requests, and technical support.\n"
            "- 'RAG': For questions that require searching uploaded documents, papers (e.g. Transformer paper, PDFs, custom context) or referencing uploaded files.\n\n"
            "Guidelines:\n"
            "1. Respond ONLY with one of the following category names: HR, FINANCE, IT, or RAG.\n"
            "2. Do not include any other text, explanation, or punctuation. Just the uppercase name.\n\n"
            f"User Query: {message}\n"
            "Category:"
        )

        try:
            category = gemini_service.generate_reply(classify_prompt)
            logger.info("Raw supervisor classification: '%s'", category)
            clean_category = "".join(c for c in category if c.isalnum()).upper()
            logger.info("Supervisor classified query as: %s", clean_category)
        except Exception as exc:
            logger.exception("Supervisor classification failed, defaulting to RAG: %s", exc)
            clean_category = "RAG"

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
            # Default to RAG Agent for RAG category or unrecognized categories
            reply, sources, confidence = rag_agent.handle_query(message, use_rag=use_rag, top_k=top_k)
            return reply, sources, confidence, rag_agent.agent_name


supervisor_agent = SupervisorAgent()
