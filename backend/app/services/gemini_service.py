"""Gemini integration lives here, isolated from the web layer.

Clean architecture rule: the API layer should not know HOW we talk to
Gemini, only that it can ask for a reply. Swap this file later (RAG, agents)
without touching the endpoints.
"""

import google.generativeai as genai

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class GeminiService:
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            # Fail loud at startup rather than on first request.
            raise RuntimeError("GEMINI_API_KEY missing. Set it in backend/.env")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info("GeminiService ready (model=%s)", settings.GEMINI_MODEL)

    def generate_reply(self, message: str) -> str:
        """Send one user message to Gemini, return the text reply."""
        logger.info("Calling Gemini (chars=%d)", len(message))
        response = self._model.generate_content(message)
        reply = (response.text or "").strip()
        logger.info("Gemini replied (chars=%d)", len(reply))
        return reply


# One shared instance; created when the module is first imported.
gemini_service = GeminiService()
