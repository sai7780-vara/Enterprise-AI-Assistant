"""Pydantic models = the shape of data crossing the API boundary.

FastAPI uses these to validate incoming JSON and serialize outgoing JSON.
Defining them separately keeps API contracts explicit and self-documenting.
"""

from pydantic import BaseModel, Field


from typing import List, Optional

class SourceCitation(BaseModel):
    document_name: str = Field(..., description="Name of the source document")
    page_number: int = Field(..., description="Page number of the citation (1-indexed)")
    chunk_id: str = Field(..., description="Unique ID of the document chunk")
    text: str = Field(..., description="The matched text segment content")
    similarity_score: float = Field(..., description="Semantic similarity match score")


class ChatRequest(BaseModel):
    # The user's message. min_length=1 rejects empty strings automatically.
    message: str = Field(..., min_length=1, description="User message text")
    # Toggle for using the local vector database.
    use_rag: bool = Field(default=True, description="Whether to search local knowledge base")
    # Top-K chunks configuration
    top_k: int = Field(default=4, ge=1, le=10, description="Number of source chunks to retrieve")


class ChatResponse(BaseModel):
    # The assistant's reply produced by Gemini.
    reply: str
    # List of source citations used for context.
    sources: List[SourceCitation] = Field(default_factory=list, description="Documents used for context")
    # Retrieval confidence score.
    confidence: Optional[float] = Field(default=None, description="Retrieval confidence percentage")
    # The name of the agent that resolved the request.
    agent_name: Optional[str] = Field(default=None, description="The name of the agent that resolved this query")
    # The selected agent resolving the query (Phase 4).
    selected_agent: Optional[str] = Field(default=None, description="The name of the agent that resolved this query (selected_agent)")
    # The lowercase shortcode for the agent type (Phase 4).
    agent_type: Optional[str] = Field(default=None, description="The type of the agent (e.g. hr, finance, it, rag)")


