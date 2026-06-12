"""Application entry point. Builds the FastAPI app and wires everything.

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Enterprise AI Knowledge Assistant", version="0.1.0")

# CORS lets the React dev server (different port) call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routes under /api  ->  /api/health and /api/chat.
app.include_router(router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Backend started")
