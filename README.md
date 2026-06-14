# Enterprise AI Knowledge Assistant — Phase 6 (MCP + Tool Calling)

A production-style multi-agent full-stack Retrieval-Augmented Generation (RAG) knowledge assistant. Users can upload multi-page PDF, TXT, and Markdown files to ground Gemini's responses in a custom local knowledge base, communicate directly with specialized domain experts routed by a Supervisor Agent, or execute complex, multi-agent workflows orchestrated by LangGraph.

---

## Phases Overview

*   **Phase 1 (Gemini Chat):** A direct, isolated endpoint for communicating with Gemini models directly without any document grounding.
*   **Phase 2 (Local RAG):** Document page-by-page parsing, chunking, vector embeddings storage, and context retrieval matching.
*   **Phase 3 (Production RAG):** High-performance cosine similarity search (via L2-normalized FAISS IndexFlatIP), dynamic top-k retrieval slider, detailed page citations, confidence percentage metrics, and expandable source citation UI cards.
*   **Phase 4 (Agent Architecture):** Multi-agent routing via a Supervisor Agent to distribute queries to specialized domain agents (HR Agent, Finance Agent, IT Agent, and RAG Agent) with automatic model rotation on rate-limiting.
*   **Phase 5 (LangGraph + A2A):** Stateful, multi-agent orchestration via LangGraph. Implements Agent-to-Agent (A2A) communication through a shared state dictionary. Executes sequential, multi-department plans (onboarding, travel, cross-functional setups) while retaining Phase 4 routing for simple queries.
*   **Phase 6 (MCP + Tool Calling):** Standardized, decoupled integrations using Model Context Protocol (MCP) servers communicating over standard input/output (stdio) using JSON-RPC 2.0. Exposes SQLite databases (employees, tickets) and semantic vector indexes as tools with structured error handling.

---

## Phase 5 StateGraph Flow (Onboarding Example)

For multi-agent workflows, the query is executed through a cyclic LangGraph state machine:

```text
       ┌─────────────────────────── [ User Query ] ───────────────────────────┐
       │                                                                      │
       ▼                                                                      ▼
  Supervisor (Entry Node) ➜ Categorize ➜ "ONBOARDING"                         Supervisor (Synthesis Node)
       │                                                                      ▲
       ▼                                                                      │
   [HR Node] (Set up rules) ➜ State updated with hr_response                 [Finance Node] (Calculate budget)
       │                                                                      ▲
       ▼                                                                      │
   [IT Node] (Fetch HR rules from state & define setup) ➜ State updated with it_response
```

1. **User Request**: React frontend submits *"Create onboarding plan for a new employee"*.
2. **FastAPI Router**: FastAPI checks the classification. Since it's a multi-agent intent, it invokes the compiled LangGraph workflow.
3. **Supervisor Node**: Initializes the graph state, sets the workflow type to `"onboarding"`, and determines the node routing list: `["HR", "IT", "FINANCE"]`.
4. **HR Node**: Determines HR employee rules and writes `hr_response` into the state. Routes back to the Supervisor.
5. **IT Node**: Reads `state["hr_response"]` (A2A Communication) to tailor hardware/access allocations (e.g. laptop specs based on the hire profile), writes `it_response`, and routes back to the Supervisor.
6. **Finance Node**: Reads `state["hr_response"]` and `state["it_response"]` to calculate budget allowances, writes `finance_response`, and routes back to the Supervisor.
7. **Supervisor Synthesis**: The Supervisor detects `remaining_steps` is empty, reads the collected outputs, calls Gemini to synthesize a combined plan, and sets `next_agent="END"`.

---

## Agent-to-Agent (A2A) State Sharing

Sub-agents collaborate by reading from the shared `AgentState` object. For example, the **IT Agent** adjusts its instructions dynamically depending on prior decisions:

```python
# app/agents/it_agent.py
def handle_query(self, query: str, state: dict = None) -> str:
    hr_context = ""
    if state and state.get("hr_response"):
        # Access prior agent results from the shared State
        hr_context = f"\n\n--- HR ONBOARDING CONTEXT ---\n{state['hr_response']}\n-----------------------------"
```

---

## Phase 5 Routing & Test Cases

### A. Simple Queries (Phase 4 Router Fallback)
Simple questions bypass the LangGraph state compilation to maximize execution speed:
*   **"What is the leave policy?"** → Routed to **HR Agent** (`workflow_type: null`, `execution_path: []`)
*   **"How do I submit an expense report?"** → Routed to **Finance Agent**
*   **"My VPN is not working."** → Routed to **IT Agent**
*   **"Summarize the uploaded PDF."** → Routed to **RAG Agent**

### B. Multi-Agent Workflows (Phase 5 LangGraph)
Composite, multi-department queries invoke the LangGraph StateGraph engine:
*   **"Create onboarding plan for a new employee"**
    *   *Path:* `Supervisor Agent ➜ HR Agent ➜ IT Agent ➜ Finance Agent ➜ Supervisor Agent`
    *   *Workflow Type:* `onboarding`
*   **"Prepare travel reimbursement plan"**
    *   *Path:* `Supervisor Agent ➜ Finance Agent ➜ HR Agent ➜ Supervisor Agent`
    *   *Workflow Type:* `travel`

---

## Phase 6 — MCP & Tool Calling Architecture

Phase 6 introduces the Model Context Protocol (MCP) to decouple domain agents from local data stores and IT service databases.

### MCP Stdio Execution Path
```text
  Agent Node ➜ Python Tool Wrapper ➜ MCP Client ➜ JSON-RPC Stdio ➜ MCP Server (Subprocess) ➜ Database/FAISS Index
```
1. **Agent Node:** Specialist agents (HR, IT, Finance, RAG) identify user intent from queries (using regex patterns or capital-cased words).
2. **Python Tool Wrapper:** Triggers corresponding functions (e.g. `employee_tool.get_employee`).
3. **MCP Client Manager:** Spawns and manages standard stdio subprocess connections to servers using `sys.executable`. Communicates using line-buffered JSON-RPC 2.0 messages.
4. **MCP Server:** Runs in a separate process, loading tables or vector indexes. Directs all logging statements to standard error (`sys.stderr`) to safeguard standard output (`stdout`) from JSON-RPC frame pollution.
5. **Grounded Synthesis:** Injects tool outputs directly into the Gemini prompt template.

### Exposed MCP Servers & Tools
| Server Name | File Path | Tools Exposed |
| :--- | :--- | :--- |
| `employee-db-mcp` | `backend/app/mcp/employee_db_server.py` | `get_employee`, `search_employee`, `create_employee` (SQLite) |
| `ticket-mcp` | `backend/app/mcp/ticket_server.py` | `create_ticket`, `get_ticket_status` (SQLite) |
| `document-search-mcp` | `backend/app/mcp/document_server.py` | `search_documents`, `get_sources` (FAISS) |

---

## API Documentation (Phase 6 Specification)

### Chat Endpoint (`POST /api/chat`)

*   **Request Payload:**
    ```json
    {
      "message": "Create onboarding plan for a new employee",
      "use_rag": true,
      "top_k": 4
    }
    ```
*   **Multi-Agent Workflow Response (Phase 5):**
    ```json
    {
      "reply": "# Synthesis Onboarding Plan ...",
      "selected_agent": "Supervisor Agent",
      "agent_type": "supervisor",
      "sources": [],
      "confidence": null,
      "workflow_type": "onboarding",
      "execution_path": [
        "Supervisor Agent",
        "HR Agent",
        "IT Agent",
        "Finance Agent",
        "Supervisor Agent"
      ]
    }
    ```
*   **Simple Query Fallback Response (Phase 4):**
    ```json
    {
      "reply": "Standard leave rules ...",
      "selected_agent": "HR Agent",
      "agent_type": "hr",
      "sources": [],
      "confidence": null,
      "workflow_type": null,
      "execution_path": []
    }
    ```

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
2. Run local verification suite:
   ```bash
   python test_agents.py
   ```
3. Start development server:
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

---

## Learning Documentation

*   [Phase 5 Learning Guide](PHASE_5_LEARNING_GUIDE.md) — A comprehensive guide explaining LangGraph orchestration, StateGraph structure, Agent-to-Agent (A2A) communication, and multi-agent interview questions.
*   [Phase 6 Learning Guide](PHASE_6_MCP_LEARNING_GUIDE.md) — A comprehensive guide explaining the Model Context Protocol (MCP), stdio JSON-RPC subprocess servers, tool wrapping, structured error handling, and 20 interview Q&As.
