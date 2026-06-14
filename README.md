# Enterprise AI Knowledge Assistant — Phase 3 (Production-Style RAG)

A production-style full-stack Retrieval-Augmented Generation (RAG) knowledge assistant. Users can upload multi-page PDF, TXT, and Markdown files to ground Gemini's responses in a custom local knowledge base.

---

## Key Features

1. **Gemini Integration:** Isolated generative model API connector utilizing `gemini-2.5-flash` for answers and `gemini-embedding-001` for semantic vector embeddings.
2. **Page-by-Page Document Ingestion:** Custom parsing of PDF files page-by-page, chunking each page cleanly while tracking page boundaries and indexing metadata.
3. **Local Vector Database (FAISS):** High-performance vector index using `FAISS-cpu` and cosine similarity (FlatIP with L2-normalized embeddings) to match chunks.
4. **Structured Metadata Support:** Every chunk is indexed with metadata: `document_name`, `page_number`, `chunk_id`, and `upload_timestamp`.
5. **Configurable Top-K Retrieval:** Dynamically adjust the number of context chunks retrieved ($K$ between 1 and 10) using a slider control in the UI.
6. **Detailed Citations & Source Chunks:** Every response bubble displays the document source list, page numbers, and unique snippet IDs.
7. **Similarity-based Confidence Scores:** Calculates a retrieval confidence percentage based on the cosine similarity score of the best-matching chunk.
8. **Premium Expandable UI:** Expand citation cards to view the exact text excerpts retrieved from the source documents.

---

## Project Structure

```text
enterprise-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py             # HTTP endpoints: /chat, /documents, etc.
│   │   ├── core/
│   │   │   ├── config.py             # Reads settings (API keys, defaults, models)
│   │   │   └── logger.py             # Central logging setup
│   │   ├── schemas/
│   │   │   ├── chat.py               # Pydantic models (ChatRequest, SourceCitation, etc.)
│   │   │   └── document.py           # Document schemas (UploadResponse, etc.)
│   │   ├── services/
│   │   │   ├── document_service.py   # Page-by-page parsing, chunking, and embedding
│   │   │   ├── gemini_service.py     # Simple Gemini API chat connector
│   │   │   ├── rag_service.py        # RAG orchestrator, prompt grounding, confidence scoring
│   │   │   └── vector_store.py       # FAISS database interface, pickle indexing
│   │   └── main.py                  # CORS setup, FastAPI app builder
│   ├── requirements.txt
│   └── .gitignore
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ChatMessage.jsx       # Message bubble with expandable source citation cards
    │   │   └── KnowledgeManager.jsx  # Knowledge base sidebar drawer & upload manager
    │   ├── api.js                   # API connector (sendChatMessage, uploadDocument, etc.)
    │   ├── App.jsx                  # Main interface: sidebar triggers, RAG configurations, slider
    │   ├── main.jsx                 # Vite entrypoint
    │   └── styles.css               # premium stylesheets & glassmorphic aesthetics
    ├── index.html
    └── package.json
```

---

## Backend Setup

1. **Navigate to backend and build environment:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate       # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment variables:**
   Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your Gemini API key:
   ```text
   GEMINI_API_KEY=your-api-key-here
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_EMBEDDING_MODEL=gemini-embedding-001
   FRONTEND_ORIGIN=http://localhost:5173
   ```

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   * Backend runs at **http://localhost:8000**.
   * Interactive OpenAPI swagger docs: **http://localhost:8000/docs**.

---

## Frontend Setup

1. **Navigate to frontend and run Dev server:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   * Frontend runs at **http://localhost:5173**. Open this URL in your web browser.

---

## API Endpoints

### Documents

* **POST `/api/documents`:** Ingest a file (PDF, TXT, MD) into the database.
* **GET `/api/documents`:** List metadata of all ingested documents.
* **DELETE `/api/documents/{doc_id}`:** Delete a document and rebuild the FAISS index.

### Chat

* **POST `/api/chat`:** Chat with the AI (Direct or RAG-grounded).
  * **Request Body:**
    ```json
    {
      "message": "What is the secret code word?",
      "use_rag": true,
      "top_k": 3
    }
    ```
  * **Response Shape:**
    ```json
    {
      "reply": "The secret code word is BANANA.",
      "sources": [
        {
          "document_name": "test_phase_3.txt",
          "page_number": 1,
          "chunk_id": "b3ad6bb7_p1_c0",
          "text": "The secret code word is BANANA. This is snippet 1.",
          "similarity_score": 0.7378
        }
      ],
      "confidence": 73.8
    }
    ```

---

## Environment Variables

The following environment variables are required to run the backend:
* `GEMINI_API_KEY`: The API key to access Google Gemini models.
* `GEMINI_MODEL`: The model used for generation (defaults to `gemini-2.5-flash`).
* `GEMINI_EMBEDDING_MODEL`: The model used for generating embeddings (defaults to `gemini-embedding-001`).
* `FRONTEND_ORIGIN`: The client address allowed by CORS (defaults to `http://localhost:5173`).

---

## Common Errors & Fixes

### 1. `IndexFlatIP` Assertions and Dimension Mismatches
* **Error**: `AssertionError: dimension mismatch` when adding or searching documents.
* **Fix**: Ensure that the vector dimension matches the embedding model output. `gemini-embedding-001` outputs vectors of size 3072. If you change models, you must delete `knowledge_store.pkl` and re-ingest files.

### 2. High Memory Usage or Slow Starts
* **Error**: App takes a long time to start or runs out of memory.
* **Fix**: Because vectors are cached in-memory using Pickle and FAISS CPU, massive libraries of documents will increase RAM footprint. Persist index builds by making sure `knowledge_store.pkl` is saved properly, or split uploads into smaller batches.

### 3. Missing Citations in UI
* **Error**: Answers are generated, but no source cards are visible.
* **Fix**: Ensure `use_rag` is checked in the UI. If checked but cards are still empty, the model might not have retrieved any document chunks with similarity scores high enough to count as relevant context.

---

## GitHub Branch Information
* **Branch Name**: `phase-3`
* **Next Branch**: `phase-4`

