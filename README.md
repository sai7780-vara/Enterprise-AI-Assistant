# Enterprise AI Knowledge Assistant — Phase 4 (Agent Architecture)

A production-style multi-agent full-stack Retrieval-Augmented Generation (RAG) knowledge assistant. Users can upload multi-page PDF, TXT, and Markdown files to ground Gemini's responses in a custom local knowledge base, or communicate directly with specialized domain experts routed by a Supervisor Agent.

---

## Completed Phases

*   **Phase 1 (Gemini Chat):** A direct, isolated endpoint for communicating with Gemini models without any document grounding.
*   **Phase 2 (Local RAG):** Document page-by-page parsing, chunking, vector embeddings storage, and context retrieval matching.
*   **Phase 3 (Production RAG):** High-performance cosine similarity search (via L2-normalized FAISS IndexFlatIP), dynamic top-k retrieval slider, detailed page citations, confidence percentage metrics, and expandable source citation UI cards.
*   **Phase 4 (Agent Architecture):** Multi-agent routing via a Supervisor Agent to distribute queries to specialized domain agents (HR Agent, Finance Agent, IT Agent, and RAG Agent) with automatic model rotation on rate-limiting.

---

## Phase 4 Architecture & Flow

The execution trace of a query follows this multi-agent routing model:

```text
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
Supervisor Agent
  ↓
[HR Agent] or [Finance Agent] or [IT Agent] or [RAG Agent]
  ↓
Gemini API or RAG Service
  ↓
Response
```

1. **User Request**: The user enters a question in the React frontend.
2. **FastAPI Route**: The frontend triggers the `/api/chat` POST route in FastAPI.
3. **Supervisor Agent**: Evaluates the input string and classifies it into exactly one specialist category: `HR`, `FINANCE`, `IT`, or `RAG`.
4. **Specialist Sub-Agent**: The query is routed to the designated agent (e.g. `hr_agent.py` or `finance_agent.py`), which constructs its customized expert system prompt.
5. **Gemini Execution**: The sub-agent queries Gemini (rotating model selections if quota is exhausted) and returns the generated answer.
6. **Frontend Render**: The UI displays the response decorated with a badge indicating the resolving agent.

---

## Specialist Agents & Responsibilities

*   **Supervisor Agent (`supervisor_agent.py`):** Acts as the central traffic controller. It uses a zero-shot classification system prompt to determine which subject-matter expert is best suited to resolve the user's request.
*   **HR Agent (`hr_agent.py`):** Handles Human Resources protocols. Specialized in leave policies, employee benefits, holidays, and employee handbook queries.
*   **Finance Agent (`finance_agent.py`):** Handles financial questions, invoicing procedures, expense reports, reimbursements, and budgets.
*   **IT Agent (`it_agent.py`):** Handles hardware provisioning (such as laptop requests), VPN credentials, password resets, systems access, and technical support.
*   **RAG Agent (`rag_agent.py`):** Specialized in document retrieval. If a query is classified as a document search or requests summarizing/parsing of custom uploaded files, it invokes the Phase 3 `rag_service` to run a semantic FAISS search.

---

## Phase 4 Test Questions & Routing

The routing logic can be validated with these test cases:
*   **"What is the leave policy?"** → Routed to **HR Agent**
*   **"How do I submit an expense report?"** → Routed to **Finance Agent**
*   **"My VPN is not working."** → Routed to **IT Agent**
*   **"Summarize the uploaded PDF."** → Routed to **RAG Agent**

---

## API Documentation (Phase 4 Specification)

### Documents Endpoints

*   **POST `/api/documents`:** Ingest a file (PDF, TXT, MD) into the database.
*   **GET `/api/documents`:** List metadata of all ingested documents.
*   **DELETE `/api/documents/{doc_id}`:** Delete a document and rebuild the FAISS index.

### Chat Endpoint

*   **POST `/api/chat`:** Chat with the Agent Architecture.
    *   **Request Payload:**
        ```json
        {
          "message": "How do I submit an expense report?",
          "use_rag": true,
          "top_k": 4
        }
        ```
    *   **Standard Domain Agent Response (e.g., Finance, HR, IT):**
        ```json
        {
          "reply": "To submit an expense report, go to the expense dashboard, fill out the reimbursement forms, and attach all receipts...",
          "selected_agent": "Finance Agent",
          "agent_type": "finance",
          "sources": [],
          "confidence": null
        }
        ```
    *   **RAG Agent Response (Searching Uploaded PDFs):**
        ```json
        {
          "reply": "Based on page 4 of the guidelines, you can request travel refunds...",
          "selected_agent": "RAG Agent",
          "agent_type": "rag",
          "sources": [
            {
              "document_name": "expense-guide.pdf",
              "page_number": 4,
              "chunk_id": "doc_p4_c1",
              "text": "Travel reimbursement claims must be filed within 30 days.",
              "similarity_score": 0.8143
            }
          ],
          "confidence": 81.4
        }
        ```

---

## Architectural Explanations

### What is an Agent?
An agent is an autonomous software entity that uses a Large Language Model (LLM) as its central engine, coupled with a specialized identity (system instructions/prompt) and a narrow boundary of operation, to complete specific tasks or resolve queries within a defined domain of expertise.

### What is Supervisor Routing?
Supervisor routing is an architectural pattern where a central "supervisor" or "coordinator" agent receives the raw user input, analyzes the intent, and assigns it to a specialist agent. This separates the operational logic of various departments, ensuring that the specialized agents are not distracted by irrelevant instructions, leading to higher output accuracy and fewer token errors.

### Phase 3 RAG vs. Phase 4 Multi-Agent Architecture
*   **Phase 3 RAG** was a single-path system: every prompt was sent directly to a retrieval loop that performed a search on the vector DB, compiled the top chunks, and returned a grounded response.
*   **Phase 4 Agent Architecture** introduces branching pathways. It evaluates user intent first. If the user asks general procedural questions (like HR benefits or VPN access), it bypasses the expensive database retrieval completely and routes to a specialized agent.

### Why RAG is now One Agent
Under a multi-agent framework, RAG is no longer the entire system; it is treated as a specialized tool or sub-agent. The RAG Agent is called only when the supervisor decides that a query requires searching custom files, keeping document indexing decoupled from general conversation.

### Why this is not LangGraph yet (LangGraph in Phase 5)
In Phase 4, the routing and agent communication are written in pure, native Python code (using static conditionals and linear routing paths). While highly performant for this level of complexity, it does not support cyclic loops, state persistence across complex multi-step tasks, or advanced human-in-the-loop overrides. Phase 5 will transition the architecture to a stateful, graph-based framework using **LangGraph** to allow complex cycles, memory, and advanced agent coordination.

---

## Development Setup

### Backend Setup
1. Navigate to backend:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate       # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Configure `.env`:
   Create a `.env` file from `.env.example` and set your API key:
   ```text
   GEMINI_API_KEY=your-api-key-here
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_EMBEDDING_MODEL=gemini-embedding-001
   FRONTEND_ORIGIN=http://localhost:5173
   ```
3. Run:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open **http://localhost:5173** to run the app.
