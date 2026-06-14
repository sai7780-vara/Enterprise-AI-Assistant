# Enterprise AI Knowledge Assistant — Phase 2 (Local RAG)

A full-stack RAG (Retrieval-Augmented Generation) knowledge assistant. Users can upload multi-page PDF, TXT, and Markdown files to ground Gemini's responses in a custom local knowledge base.

---

## What This Phase Does
Phase 2 layers document processing and vector embedding retrieval on top of Phase 1:
* **Local Document Ingestion:** Users upload PDF, TXT, or MD files via the UI.
* **Semantic Chunking:** Text is automatically split into semantic chunks with overlapping boundaries.
* **Vector Embeddings:** Chunks are translated into numerical representations using Gemini's `text-embedding-001`.
* **FAISS Search:** An in-memory similarity search matching queries against unit-normalized vectors.
* **Context Injected Generation:** Custom prompts feed matching text chunks directly to Gemini to generate factual responses.

---

## Project Structure

```
enterprise-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # /api/chat, /api/documents (upload, list, delete)
│   │   ├── core/
│   │   │   ├── config.py          # Config loader
│   │   │   └── logger.py          # Central logger
│   │   ├── schemas/
│   │   │   ├── chat.py            # Pydantic schemas for chat
│   │   │   └── document.py        # Pydantic schemas for documents
│   │   ├── services/
│   │   │   ├── document_service.py # Preprocessing, PDF parsing, chunking
│   │   │   ├── gemini_service.py  # Standard model caller
│   │   │   ├── rag_service.py     # Integrates semantic retrieval + grounding
│   │   │   └── vector_store.py    # Local FAISS index & Pickle persistence
│   │   └── main.py                # App entrypoint
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── ChatMessage.jsx
    │   ├── api.js                 # API wrappers for endpoints
    │   ├── App.jsx                # UI state & document upload fields
    │   ├── main.jsx
    │   └── styles.css
```

---

## Environment Variables

Create `backend/.env` with the following variables:
* `GEMINI_API_KEY`: API key from Google AI Studio.
* `KNOWLEDGE_BASE_DIR`: Directory where `knowledge_store.pkl` will be serialized (defaults to `app/data`).

---

## Backend Setup

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies (make sure faiss-cpu is installed)
pip install -r requirements.txt

# 3. Setup environment variables
cp .env.example .env
# Edit .env and enter GEMINI_API_KEY

# 4. Run the development server
uvicorn app.main:app --reload
```

## Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start Vite dev server
npm run dev
```

---

## Common Errors & Fixes

### 1. `ModuleNotFoundError: No module named 'faiss'`
* **Cause**: The `faiss-cpu` dependency failed to install or is missing from requirements.
* **Fix**: Run `pip install faiss-cpu` manually inside your activated virtual environment.

### 2. PDF Parsing Failing
* **Cause**: Document is empty, corrupt, or uses unsupported non-standard fonts/OCR.
* **Fix**: Ensure the PDF contains parseable text (not just scans/images). If scanned, run OCR on it first.

---

## GitHub Branch Information
* **Branch Name**: `phase-2-local-rag`
* **Next Branch**: `phase-3`
