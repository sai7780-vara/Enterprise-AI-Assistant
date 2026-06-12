"""Pydantic models = the shape of data crossing the API boundary.

FastAPI uses these to validate incoming JSON and serialize outgoing JSON.
Defining them separately keeps API contracts explicit and self-documenting.
"""

from pydantic import BaseModel, Field


from typing import List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # The user's message. min_length=1 rejects empty strings automatically.
    message: str = Field(..., min_length=1, description="User message text")
    # Toggle for using the local vector database.
    use_rag: bool = Field(default=True, description="Whether to search local knowledge base")


class ChatResponse(BaseModel):
    # The assistant's reply produced by Gemini.
    reply: str
    # List of source document names referenced to answer this query.
    sources: List[str] = Field(default_factory=list, description="Documents used for context")
