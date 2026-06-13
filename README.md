# Enterprise AI Knowledge Assistant — Phase 4 (Agent Architecture)

A production-style multi-agent full-stack Retrieval-Augmented Generation (RAG) knowledge assistant. Users can upload multi-page PDF, TXT, and Markdown files to ground Gemini's responses in a custom local knowledge base, or communicate directly with specialized domain experts routed by a Supervisor Agent.

---

## Phases Overview

*   **Phase 1 (Gemini Chat):** Basic endpoint for querying the Gemini models directly without document grounding.
*   **Phase 2 (Local RAG):** Document parsing, page-by-page chunking, vector storage, and context retrieval matching.
*   **Phase 3 (Production RAG):** Cosine similarity search (via L2-normalized FAISS IndexFlatIP), dynamic top-k adjustment, page citations, confidence scoring, and expandable source citation UI cards.
*   **Phase 4 (Agent Architecture):** Multi-agent routing via a Supervisor Agent to distribute queries to specialized domain agents (HR Agent, Finance Agent, IT Agent, and RAG Agent) with automatic model rotation on rate-limiting.

---

## Architecture Flow

The execution trace of a query follows this multi-agent routing model:

```text
User → React UI → FastAPI Endpoint → Supervisor Agent
                                            │
           ┌────────────────┬───────────────┼───────────────┐
           ▼                ▼               ▼               ▼
      [HR Agent]     [Finance Agent]    [IT Agent]     [RAG Agent]
           │                │               │               │
       Gemini API       Gemini API      Gemini API     FAISS / RAG
           │                │               │               │
           └────────────────┴───────────────┼───────────────┘
                                            ▼
                                     React UI Display
```

1. **User Request**: The user enters a question in the React frontend.
2. **FastAPI Route**: The frontend triggers the `/api/chat` POST route in FastAPI.
3. **Supervisor Agent**: Evaluates the input string and classifies it into exactly one specialist category: `HR`, `FINANCE`, `IT`, or `RAG`.
4. **Specialist Sub-Agent**: The query is routed to the designated agent (e.g. `hr_agent.py` or `finance_agent.py`), which constructs its customized expert system prompt.
5. **Gemini Execution**: The sub-agent queries Gemini (rotating model selections if quota is exhausted) and returns the generated answer.
6. **Frontend Render**: The UI displays the response decorated with a badge indicating the resolving agent.

---

## Phase 4 Test Questions & Routing

The routing logic can be validated with these test cases:
*   **"What is the leave policy?"** → Routed to **HR Agent** (for leave, holidays, handbook, benefits).
*   **"How do I submit an expense report?"** → Routed to **Finance Agent** (for expense forms, reimbursements, invoicing).
*   **"My VPN is not working."** → Routed to **IT Agent** (for laptop provisioning, VPN configurations, tech support).
*   **"Summarize the uploaded PDF."** → Routed to **RAG Agent** (for custom local document searches and matching context blocks).

---

## Project Structure

```text
enterprise-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── finance_agent.py      # Finance Specialist
│   │   │   ├── hr_agent.py           # HR Specialist
│   │   │   ├── it_agent.py           # IT Specialist
│   │   │   ├── rag_agent.py          # RAG Retrieval Specialist
│   │   │   └── supervisor_agent.py   # Supervisor & Classifier Agent
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
│   ├── test_agents.py                # Local routing test script
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
   GEMINI_MODEL=gemini-3.5-flash
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

*   **POST `/api/documents`:** Ingest a file (PDF, TXT, MD) into the database.
*   **GET `/api/documents`:** List metadata of all ingested documents.
*   **DELETE `/api/documents/{doc_id}`:** Delete a document and rebuild the FAISS index.

### Chat

*   **POST `/api/chat`:** Chat with the AI (Direct or RAG-grounded).
    *   **Request Body:**
        ```json
        {
          "message": "What is the secret code word?",
          "use_rag": true,
          "top_k": 3
        }
        ```
    *   **Response Shape:**
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
