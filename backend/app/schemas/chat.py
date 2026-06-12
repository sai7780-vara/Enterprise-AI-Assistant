"""Pydantic models = the shape of data crossing the API boundary.

FastAPI uses these to validate incoming JSON and serialize outgoing JSON.
Defining them separately keeps API contracts explicit and self-documenting.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # The user's message. min_length=1 rejects empty strings automatically.
    message: str = Field(..., min_length=1, description="User message text")


class ChatResponse(BaseModel):
    # The assistant's reply produced by Gemini.
    reply: str
