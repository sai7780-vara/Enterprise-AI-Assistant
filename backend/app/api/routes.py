"""HTTP endpoints. Thin layer: validate input, call a service, return output.

No business logic here. That keeps endpoints readable and testable.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import gemini_service
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
    """Take a user message, return Gemini's reply."""
    try:
        reply = gemini_service.generate_reply(payload.message)
        return ChatResponse(reply=reply)
    except Exception as exc:  # noqa: BLE001
        # Log the real error server-side, send a clean message to the client.
        logger.exception("Chat failed: %s", exc)
        raise HTTPException(status_code=502, detail="Gemini request failed")
