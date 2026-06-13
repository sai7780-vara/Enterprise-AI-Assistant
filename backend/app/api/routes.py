from fastapi import APIRouter, HTTPException, File, UploadFile

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import UploadResponse, DocumentListResponse
from app.services.rag_service import rag_service
from app.services.document_service import document_service
from app.services.vector_store import vector_store
from app.core.logger import get_logger

logger = get_logger(__name__)

# All routes in this file get the /api prefix (set in main.py).
router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Liveness check. Returns 200 if the app is up."""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """Take a user message, retrieve context if enabled, and return Gemini's reply."""
    try:
        reply, sources, confidence = rag_service.generate_reply_with_context(
            message=payload.message,
            use_rag=payload.use_rag,
            top_k=payload.top_k
        )
        return ChatResponse(reply=reply, sources=sources, confidence=confidence)
    except Exception as exc:  # noqa: BLE001
        # Log the real error server-side, send a clean message to the client.
        logger.exception("Chat failed: %s", exc)
        raise HTTPException(status_code=502, detail="Gemini request failed")


@router.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """Ingest a new text or PDF document into the local knowledge base."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file: missing name.")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ("pdf", "txt", "md", "markdown"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF, TXT, and MD files are allowed."
        )

    try:
        content = await file.read()
        result = document_service.ingest_document(file.filename, content)
        return UploadResponse(
            status="success",
            message=f"Document '{file.filename}' successfully ingested and vectorized.",
            document=result
        )
    except ValueError as ve:
        logger.warning("Document parsing failed: %s", ve)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Unexpected error during ingestion: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {e}")


@router.get("/documents", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    """List all documents currently ingested in the knowledge base."""
    try:
        docs = vector_store.list_documents()
        return DocumentListResponse(documents=docs)
    except Exception as e:
        logger.exception("Failed to list documents: %s", e)
        raise HTTPException(status_code=500, detail="Could not retrieve documents list.")


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str) -> dict:
    """Delete a document from the local database and rebuild vector index."""
    try:
        success = vector_store.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found.")
        return {"status": "success", "message": "Document successfully deleted."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete document: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {e}")
