"""Pydantic schemas for Knowledge Base Document management.

Used for validation of API request and response data structures.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata representing an ingested file in the system."""
    doc_id: str = Field(..., description="Unique ID for the document (UUID or hash)")
    filename: str = Field(..., description="Original name of the uploaded file")
    size_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Timestamp of when the document was uploaded")
    chunk_count: int = Field(..., description="Number of text chunks created from this document")


class UploadResponse(BaseModel):
    """API response returned after successful document ingestion."""
    status: str = Field("success", description="Ingestion status indicator")
    message: str = Field(..., description="Informational message")
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    """API response returning all currently indexed documents."""
    documents: List[DocumentMetadata]
