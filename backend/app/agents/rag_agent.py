from typing import List, Tuple
from app.services.rag_service import rag_service
from app.core.logger import get_logger

logger = get_logger(__name__)


class RagAgent:
    def __init__(self) -> None:
        self.agent_name = "RAG Agent"

    def handle_query(self, query: str, use_rag: bool = True, top_k: int = 4, state: dict = None) -> Tuple[str, List[dict], float]:
        logger.info("RAG Agent handling query: %s (use_rag=%s, top_k=%d)", query, use_rag, top_k)
        # Delegate to the existing Phase 3 RAG service
        reply, sources, confidence = rag_service.generate_reply_with_context(
            message=query,
            use_rag=use_rag,
            top_k=top_k
        )
        return reply, sources, confidence


rag_agent = RagAgent() 