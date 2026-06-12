"""Application configuration.

Reads environment variables (from .env via python-dotenv) into a single
Settings object the rest of the app imports. Keeping config in one place
is part of clean architecture: nothing else touches os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file in the backend root into os.environ.
load_dotenv()


class Settings:
    # Gemini API key. Never hard-code secrets; read from the environment.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Which Gemini model to call.
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # CORS: which frontend origin may call this API.
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Where local vector index & uploaded documents are stored.
    KNOWLEDGE_BASE_DIR: str = os.getenv(
        "KNOWLEDGE_BASE_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    )

    # Gemini embedding model to use.
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")


# Single shared instance imported everywhere.
settings = Settings()
