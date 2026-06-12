"""Document ingestion service.

Extracts text from uploaded files (PDF, text, Markdown),
splits the text into semantically cohesive chunks,
generates embeddings via Google Gemini,
and inserts them into the local FAISS vector store.
"""

import io
import uuid
from datetime import datetime
from typing import List

import google.generativeai as genai
import pypdf

from app.core.config import settings
from app.core.logger import get_logger
from app.services.vector_store import vector_store

logger = get_logger(__name__)


def parse_file(content: bytes, filename: str) -> str:
    """Extract text from the uploaded file based on its extension."""
    ext = filename.split(".")[-1].lower()
    logger.info("Parsing file %s (type=%s, size=%d bytes)", filename, ext, len(content))

    if ext == "pdf":
        text = ""
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            logger.info("Successfully extracted %d characters from PDF", len(text))
        except Exception as e:
            logger.exception("Failed to parse PDF file: %s", e)
            raise ValueError(f"Could not parse PDF file: {e}") from e
        return text

    elif ext in ("txt", "md", "markdown"):
        try:
            return content.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.exception("Failed to decode text file: %s", e)
            raise ValueError(f"Could not decode text file: {e}") from e

    else:
        raise ValueError(f"Unsupported file type: .{ext}. Only PDF, TXT, and MD are supported.")


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[str]:
    """Split text into chunks aiming to respect sentence boundaries and spaces."""
    if not text or not text.strip():
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Look for sentence boundaries/newlines in the overlap zone to split cleanly
        if end < text_len:
            overlap_zone = max(start, end - chunk_overlap)
            
            # Search order: paragraph (newline), sentence (period), word (space)
            newline_idx = text.rfind("\n", overlap_zone, end)
            period_idx = text.rfind(".", overlap_zone, end)
            space_idx = text.rfind(" ", overlap_zone, end)

            if newline_idx != -1 and newline_idx > overlap_zone:
                end = newline_idx + 1
            elif period_idx != -1 and period_idx > overlap_zone:
                end = period_idx + 1
            elif space_idx != -1 and space_idx > overlap_zone:
                end = space_idx + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Safeguard: ensure start advances to prevent infinite loops
        next_start = max(start + 1, end - chunk_overlap)
        if next_start <= start:
            next_start = start + chunk_size - chunk_overlap

        start = next_start
        if end >= text_len:
            break

    return chunks


class DocumentService:
    def __init__(self) -> None:
        # Prepend models/ if missing for the generativeai SDK
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        if not self.embedding_model.startswith("models/"):
            self.embedding_model = f"models/{self.embedding_model}"

        # Initialize the API configure
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY missing. Set it in backend/.env")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("DocumentService initialized with embedding model %s", self.embedding_model)

    def ingest_document(self, filename: str, content: bytes) -> dict:
        """Parse, chunk, embed, and store a document in the vector database."""
        # 1. Parse text
        text = parse_file(content, filename)
        if not text.strip():
            raise ValueError("Document has no readable text content.")

        # 2. Chunk text
        chunks = split_text(text)
        logger.info("Split document %s into %d chunks", filename, len(chunks))

        # 3. Generate Embeddings (in batches of 50 to avoid request body size limits)
        embeddings = []
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            try:
                response = genai.embed_content(
                    model=self.embedding_model,
                    content=batch,
                    task_type="retrieval_document",
                )
                
                # The response contains {'embedding': [{'values': [...]}, ...]} or direct lists
                raw_embeddings = response.get("embedding", [])
                for emb in raw_embeddings:
                    if isinstance(emb, dict) and "values" in emb:
                        embeddings.append(emb["values"])
                    elif isinstance(emb, list):
                        embeddings.append(emb)
                    else:
                        # Fallback for alternative SDK object representations
                        embeddings.append(getattr(emb, "values", emb))

            except Exception as e:
                logger.exception("Gemini Embedding API call failed: %s", e)
                raise RuntimeError(f"Embedding generation failed: {e}") from e

        # 4. Save to Vector Store
        doc_id = uuid.uuid4().hex
        vector_store.add_document(
            doc_id=doc_id,
            filename=filename,
            size_bytes=len(content),
            chunks=chunks,
            embeddings=embeddings,
        )

        stored_doc = vector_store.documents["documents"][doc_id]

        return {
            "doc_id": doc_id,
            "filename": filename,
            "size_bytes": len(content),
            "uploaded_at": stored_doc.get("uploaded_at", datetime.now()),
            "chunk_count": len(chunks),
        }


# Single shared instance
document_service = DocumentService()
