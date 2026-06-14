# Phase 2 Architecture — Local RAG

This document outlines the architecture, flow diagrams, data paths, and file breakdown for Phase 2 of the Enterprise AI Knowledge Assistant.

---

## 1. Overall Architecture

Phase 2 builds upon the client-server architecture of Phase 1 by introducing a local document processing pipeline and vector store search engine:

```
                  ┌──────────────────────────────────────────────┐
                  │               FastAPI Backend                │
                  │                                              │
                  │   ┌──────────────┐       ┌───────────────┐   │
                  │   │  routes.py   │ ◄───► │  rag_service  │   │
                  │   └──────┬───────┘       └───────┬───────┘   │
                  │          │                       │           │
                  │          ▼                       ▼           │
┌──────────────┐  │   ┌──────────────┐       ┌───────────────┐   │   ┌──────────────┐
│  React UI    │ ─┼─► │  doc_service │       │  vector_store │ ──┼──►│  Gemini API  │
│  (Port 5173) │ ◄┼── └──────────────┘       └───────┬───────┘   │   │ (Embeddings  │
└──────────────┘  │                                  │           │   │  & Chat)     │
                  └──────────────────────────────────┼───────────┘   └──────────────┘
                                                     ▼
                                            [ knowledge_store.pkl ]
                                            [ (Pickle DB & FAISS) ]
```

---

## 2. Ingestion Flow (Document Upload)

When a user uploads a file through the UI:
1. **API Endpoint:** The file is POSTed to `/api/documents`.
2. **Ingestion Manager:** `document_service.ingest_document(filename, content)` checks the file extension (PDF, TXT, MD).
3. **Text Parsing:**
   - TXT/MD files are decoded directly as text strings.
   - PDF files are read using the `pypdf.PdfReader` library to extract raw text page-by-page.
4. **Text Chunking:** Chunks are created by splitting text into segments of roughly 1000 characters with a 200-character overlap to preserve semantic context across borders.
5. **Embedding Generation:** The service loops through all text chunks and calls `gemini-embedding-001` via the Gemini API to get a float array vector of size 3072.
6. **Index Insertion & Serialization:** Chunks and embeddings are stored inside a serialized dictionary mapping in `knowledge_store.pkl`. The FAISS `IndexFlatIP` index is completely rebuilt in-memory, normalizing all vectors to L2 norm for cosine similarity calculations.

---

## 3. Retrieval & Grounding Flow (Conversational Chat)

When a user submits a chat message:
1. **API Endpoint:** The query and `use_rag` flag are POSTed to `/api/chat`.
2. **State Router:** If `use_rag` is `True`, `rag_service.generate_reply_with_context` is invoked.
3. **Query Embedding:** The user's message is converted into a vector of size 3072.
4. **Similarity Search:** The vector is searched against the FAISS index. The index returns the top-4 closest chunks sorted by cosine similarity scores.
5. **Prompt Augmentation:** The text segments from the top matching chunks are formatted and injected directly into the Gemini prompt template.
6. **Synthesis:** Gemini receives the context-augmented prompt and produces a grounded reply.

---

## 4. Important Files & What They Do

### A. Backend Services (`backend/app/services/`)
* **[vector_store.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/services/vector_store.py):** Manages the core FAISS index and Pickle storage lifecycle. Rebuilds the index from serialized data on startup.
* **[document_service.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/services/document_service.py):** Responsible for parsing PDFs/texts, chunking algorithms, calling the Gemini embedding models, and registering the results with `vector_store`.
* **[rag_service.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/services/rag_service.py):** Combines vector retrieval with Gemini text generation to ground replies.

### B. Endpoints & Schemas (`backend/app/`)
* **[api/routes.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/api/routes.py):** Standard API controller exposing `/api/chat`, `/api/documents` upload, list, and deletion endpoints.
* **[schemas/document.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/schemas/document.py):** Declares Pydantic schemas `UploadResponse`, `DocumentInfo`, and `DocumentListResponse` for documents.
