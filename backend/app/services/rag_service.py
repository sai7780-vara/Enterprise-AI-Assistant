"""RAG (Retrieval-Augmented Generation) Orchestrator.

Retrieves relevant document segments for a given query, constructs
an instruction-grounded prompt, calls the Gemini model, and returns
the reply along with sources used.
"""

from typing import List, Tuple

import google.generativeai as genai

from app.core.config import settings
from app.core.logger import get_logger
from app.services.gemini_service import gemini_service
from app.services.vector_store import vector_store

logger = get_logger(__name__)


class RagService:
    def __init__(self) -> None:
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        if not self.embedding_model.startswith("models/"):
            self.embedding_model = f"models/{self.embedding_model}"

        # Initialize the API configuration
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY missing. Set it in backend/.env")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("RagService ready with model %s", settings.GEMINI_MODEL)

    def generate_reply_with_context(self, message: str, use_rag: bool = True, top_k: int = 4) -> Tuple[str, List[dict], float]:
        """Generate response by embedding user query, fetching top documents, and calling Gemini."""
        # Print temporary debug logs requested by user
        print(f"DEBUG: use_rag value received by backend: {use_rag}")
        print(f"DEBUG: number of documents in vector store: {len(vector_store.documents.get('documents', {}))}")

        # Check if RAG is requested and if we have any documents in store
        has_docs = len(vector_store.chunk_metadata_map) > 0

        if not use_rag or not has_docs:
            logger.info("Skipping RAG (use_rag=%s, has_docs=%s). Direct fallback to Gemini.", use_rag, has_docs)
            reply = gemini_service.generate_reply(message)
            return reply, [], 0.0

        logger.info("Executing RAG flow for query (chars=%d)", len(message))

        # 1. Embed query
        try:
            query_resp = genai.embed_content(
                model=self.embedding_model,
                content=message,
                task_type="retrieval_query",
            )
            
            raw_emb = query_resp.get("embedding", [])
            if isinstance(raw_emb, dict) and "values" in raw_emb:
                query_embedding = raw_emb["values"]
            elif isinstance(raw_emb, list):
                if raw_emb and isinstance(raw_emb[0], list):
                    query_embedding = raw_emb[0]
                elif raw_emb and isinstance(raw_emb[0], dict) and "values" in raw_emb[0]:
                    query_embedding = raw_emb[0]["values"]
                else:
                    query_embedding = raw_emb
            else:
                query_embedding = raw_emb

        except Exception as e:
            logger.exception("Failed to generate query embedding: %s. Falling back to direct chat.", e)
            return gemini_service.generate_reply(message), [], 0.0

        # 2. Retrieve top matches from FAISS (top-K chunks)
        results = vector_store.search(query_embedding, top_k=top_k)
        
        # Print temporary debug logs requested by user
        print(f"DEBUG: number of chunks retrieved: {len(results)}")
        print(f"DEBUG: source filenames returned: {[meta['filename'] for meta, score in results]}")

        # Add requested logs: Retrieved chunks and Similarity scores
        logger.info("Retrieved chunks: %s", [meta['chunk_id'] for meta, score in results])
        logger.info("Similarity scores: %s", [score for meta, score in results])

        if not results:
            logger.info("No matching chunks found in vector store. Calling Gemini directly.")
            return gemini_service.generate_reply(message), [], 0.0

        # Calculate confidence score based on the highest cosine similarity score (best match)
        best_similarity = results[0][1]
        confidence = min(100.0, max(0.0, best_similarity) * 100.0)
        confidence = round(confidence, 1)

        # 3. Format context blocks and compile citations
        context_chunks = []
        sources = []
        
        for idx, (meta, score) in enumerate(results):
            logger.info("Match #%d: doc=%s, page=%d, chunk=%s, score=%.4f", 
                        idx + 1, meta["filename"], meta.get("page_number", 1), meta["chunk_id"], score)
            context_chunks.append(f"Source: {meta['filename']} (Page {meta.get('page_number', 1)})\nContent: {meta['text']}")
            
            sources.append({
                "document_name": meta["filename"],
                "page_number": meta.get("page_number", 1),
                "chunk_id": meta["chunk_id"],
                "text": meta["text"],
                "similarity_score": round(score, 4)
            })

        context_block = "\n---\n".join(context_chunks)

        # 4. Construct context-aware prompt
        rag_prompt = (
            "You are a professional Enterprise AI Assistant. Use the following retrieved document context pieces to answer the user's question.\n"
            "Ground your answer strictly in the context. If the context does not contain enough information to answer, state that "
            "the information is not available in the uploaded documents. Do not utilize external information to make up facts.\n\n"
            "--- RETRIEVED CONTEXT ---\n"
            f"{context_block}\n"
            "-------------------------\n\n"
            f"User Question: {message}\n"
            "Assistant Answer:"
        )

        # 5. Generate content
        logger.info("Sending RAG-grounded prompt to Gemini (chunks=%d, sources=%d)", len(context_chunks), len(sources))
        response = self._model.generate_content(rag_prompt)
        reply = (response.text or "").strip()

        logger.info("RAG generation complete (reply chars=%d)", len(reply))
        return reply, sources, confidence


# Single shared instance
rag_service = RagService()
