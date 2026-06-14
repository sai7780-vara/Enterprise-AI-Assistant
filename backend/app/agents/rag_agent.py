import json
from typing import List, Tuple
from app.services.gemini_service import gemini_service
from app.core.logger import get_logger
from app.tools import document_tool

logger = get_logger(__name__)


class RagAgent:
    def __init__(self) -> None:
        self.agent_name = "RAG Agent"

    def handle_query(self, query: str, use_rag: bool = True, top_k: int = 4, state: dict = None) -> Tuple[str, List[dict], float]:
        logger.info("RAG Agent handling query: %s (use_rag=%s, top_k=%d)", query, use_rag, top_k)
        
        if state is not None:
            state["selected_tool"] = None
            state["mcp_server"] = None
            
        if not use_rag:
            reply = gemini_service.generate_reply(query)
            return reply, [], 0.0

        # Run Document search tool
        res = document_tool.search_documents(query, top_k)
        if state is not None:
            state["selected_tool"] = res.get("selected_tool")
            state["mcp_server"] = res.get("mcp_server")

        if not res.get("success", False):
            # Structured error feedback fallback
            err_msg = res.get("error", "Unknown document search error.")
            return f"Error executing document tool: {err_msg}", [], 0.0

        search_data = res.get("data", {})
        chunks = search_data.get("chunks", [])
        confidence = search_data.get("confidence", 0.0)

        if not chunks:
            reply = gemini_service.generate_reply(query)
            return reply, [], 0.0

        context_chunks = []
        sources = []
        for chunk in chunks:
            context_chunks.append(f"Source: {chunk['filename']} (Page {chunk.get('page_number', 1)})\nContent: {chunk['text']}")
            sources.append({
                "document_name": chunk["filename"],
                "page_number": chunk.get("page_number", 1),
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "similarity_score": chunk.get("score", 0.0)
            })

        context_block = "\n---\n".join(context_chunks)
        rag_prompt = (
            "You are a professional Enterprise AI Assistant. Use the following retrieved document context pieces to answer the user's question.\n"
            "Ground your answer strictly in the context. If the context does not contain enough information to answer, state that "
            "the information is not available in the uploaded documents. Do not utilize external information to make up facts.\n\n"
            "--- RETRIEVED CONTEXT ---\n"
            f"{context_block}\n"
            "-------------------------\n\n"
            f"User Question: {query}\n"
            "Assistant Answer:"
        )

        reply = gemini_service.generate_reply(rag_prompt)
        return reply, sources, confidence

rag_agent = RagAgent() 