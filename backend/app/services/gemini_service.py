"""Gemini integration lives here, isolated from the web layer.

Clean architecture rule: the API layer should not know HOW we talk to
Gemini, only that it can ask for a reply. Swap this file later (RAG, agents)
without touching the endpoints.
"""

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class GeminiService:
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY missing. Set it in backend/.env")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.models = [
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro",
            "gemini-2.0-flash-lite"
        ]
        self.current_model_idx = self.models.index(settings.GEMINI_MODEL) if settings.GEMINI_MODEL in self.models else 0
        self._model = genai.GenerativeModel(self.models[self.current_model_idx])
        logger.info("GeminiService ready (model=%s)", self.models[self.current_model_idx])

    def generate_reply(self, message: str) -> str:
        """Send one user message to Gemini, return the text reply. Rotates models on ResourceExhausted with backoff."""
        import time
        attempts = 0
        max_attempts = len(self.models) * 2
        backoff = 2.0
        while attempts < max_attempts:
            model_name = self.models[self.current_model_idx]
            logger.info("Calling Gemini with model %s (chars=%d)", model_name, len(message))
            try:
                response = self._model.generate_content(message)
                reply = (response.text or "").strip()
                logger.info("Gemini replied (chars=%d)", len(reply))
                return reply
            except ResourceExhausted as e:
                attempts += 1
                logger.warning(
                    "ResourceExhausted on model %s. Sleeping %s seconds and rotating model...",
                    model_name,
                    backoff
                )
                time.sleep(backoff)
                backoff = min(backoff * 2.0, 30.0)
                self.current_model_idx = (self.current_model_idx + 1) % len(self.models)
                next_model = self.models[self.current_model_idx]
                self._model = genai.GenerativeModel(next_model)
                logger.info("Rotated to model %s (attempt %d/%d)", next_model, attempts, max_attempts)
                if attempts >= max_attempts:
                    logger.error("All models exhausted. Raising quota exception.")
                    raise e
        return ""


# One shared instance; created when the module is first imported.
gemini_service = GeminiService()

