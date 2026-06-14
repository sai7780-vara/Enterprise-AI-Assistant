# Phase 6 - Model Context Protocol (MCP) & Tool Calling

Welcome to the **Phase 6 Learning Guide**. In this phase, we took our multi-agent architecture to the next level by giving our agents "hands" to interact with the outside world. We implemented the **Model Context Protocol (MCP)** to separate our agents' reasoning capabilities from the physical tools they use to fetch employee data, log IT support tickets, and perform semantic document searches.

This guide provides a comprehensive breakdown of Phase 6 architecture, comparison tables, flow diagrams, future concepts, and 20 interview-style Q&As to help you master this technology.

---

## 1. Introduction to Model Context Protocol (MCP)

### What is MCP?
**Model Context Protocol (MCP)** is an open standard designed to standardize how Large Language Models (LLMs) connect to external data sources, developer tools, and APIs. Think of it as **USB-C for AI**. Just as USB-C replaced dozens of proprietary charging cables with a single standard plug, MCP replaces custom API integrations for AI agents with a standard JSON-RPC interface.

### Why was MCP created?
Before MCP, every developer building an AI assistant had to write bespoke glue code to connect their agents to databases, APIs, or filesystems:
* If they wanted to query a database, they had to write custom Python functions.
* If they wanted to query Jira, they wrote separate API integrations.
* If they wanted to read files, they wrote a new file utility.

This custom code was tightly coupled to the application. If they changed the LLM, modified the agent framework, or moved to a different backend, they had to rebuild the integrations.

MCP decouples the **AI application (client)** from the **data sources/tools (servers)**. By using a standard protocol, any client that supports MCP can instantly connect to any server that exposes MCP tools.

### What problem does MCP solve?
1. **Decoupling/Modular Development:** The LLM client doesn't need to know how to connect to SQLite, Postgres, or a vector database. It simply sends a JSON-RPC request to the MCP server.
2. **Context Standardization:** It standardizes how prompts, resources (like files/databases), and tools (like functions) are exposed to models.
3. **Security/Isolation:** Stdio-based MCP servers run as independent child processes. They can run with restricted permissions, sandboxed environments, or on separate hardware, protecting the host application from malicious code execution or database access.

---

## 2. Terminology: Decoupling Agents, Tools, Clients, and Servers

It is easy to get confused by the different components in a tool-calling system. Here is a clear breakdown:

| Concept | What it is | Example in Our Project |
| :--- | :--- | :--- |
| **Agent** | The brain. An LLM agent configured with a role (e.g. HR Agent, IT Agent) that decides *what* to do based on user requests and decides *when* to execute a tool. | [hr_agent.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/agents/hr_agent.py) |
| **Tool** | An action that the agent can perform. In our project, tools are standard Python function wrappers that wrap the client calls. | `employee_tool.get_employee` |
| **MCP Client** | The manager inside the main backend that handles launching, connecting to, and communicating with the MCP Servers. | `MCPClientManager` in [client.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/client.py) |
| **MCP Server** | A standalone subprocess (or service) that exposes resources, prompts, and tools over stdio/SSE using JSON-RPC 2.0. | `employee_db_server.py` |

---

## 3. Architecture & Execution Flow

We implemented a **beginner-friendly tool calling architecture**. Instead of implementing a complex, recursive loop where the Gemini model emits a function-calling payload, parses it, executes it, and feeds it back in a loop, we implement a clean, deterministic pipeline:

1. **Routing:** The request is routed to a specialist Agent (e.g., HR Agent).
2. **Deterministic Triggering:** The agent inspects the user query (e.g., matching IDs or name patterns).
3. **Subprocess Call:** The agent triggers the tool wrapper -> Client Manager -> spawns the stdio MCP Server.
4. **JSON-RPC Transaction:** The client sends a standard `tools/call` JSON payload via `stdin` to the server, and reads a JSON response back via `stdout`.
5. **Context Injection:** The tool result is injected directly into the LLM system prompt.
6. **Unified Response:** The LLM produces a grounded, professional response based on that injected context.

### Execution Path Diagram

```
User Request
    │
    ▼
[Supervisor / API Route]
    │
    ▼
[Specialist Agent] (e.g., HR Agent)
    │
    ├─► 1. Detect query intent (e.g., ID 101)
    │
    ├─► 2. Execute Python Tool Wrapper: employee_tool.get_employee(101)
    │        │
    │        ▼
    │   [MCPClientManager] (in backend)
    │        │
    │        ├─► Spawns Server script via Subprocess (sys.executable)
    │        │
    │        ├─► Writes JSON-RPC to stdin:
    │        │   {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_employee", "arguments": {"id": 101}}}
    │        │
    │        └─► Reads response from stdout:
    │            {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": "{\"name\": \"Sai Kiran\", ...}"}]}}
    │
    ├─► 3. Grounding: Injects JSON result into Gemini's system prompt
    │
    └─► 4. Generation: Gemini returns grounded answer to Supervisor / API Router
```

---

## 4. Phase 5 vs. Phase 6

| Metric | Phase 5: LangGraph A2A | Phase 6: MCP + Tool Calling |
| :--- | :--- | :--- |
| **Primary Goal** | Route multi-step tasks across specialist agents (HR, IT, Finance) using a state-machine graph. | Give agents access to live external systems (databases, ticket logs, vector databases) via a standardized protocol. |
| **Data Source** | Pure LLM knowledge + raw vector store embeddings in a single process. | SQLite databases and RAG FAISS indexes queried dynamically over JSON-RPC. |
| **Flow Control** | State nodes routing to specialist agents in a LangGraph workflow. | Agent executes tool wrappers locally -> communicates with external stdio processes -> returns results to LLM context. |
| **Error Handling** | Graph routing failures or fallback nodes. | Structured JSON tool error schema returning `success: false`, `error`, `selected_tool`, and `mcp_server`. |

### Why LangGraph alone is not enough
LangGraph is a workflow orchestration tool—it maintains state, coordinates transitions, and structures the agent network. However, it does not standardize how those agents talk to external databases or software applications. MCP provides that standard communication protocol. Combining the two gives you **structured agent workflows (LangGraph)** that can **interact with external software systems (MCP)**.

---

## 5. Implementation Deep-Dive

### A. The Stdio JSON-RPC MCP servers
We created three standalone MCP servers inside `backend/app/mcp/`:
1. **[employee_db_server.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/employee_db_server.py)**: Manages an `employee.db` SQLite database with `get_employee`, `search_employee`, and `create_employee` tools.
2. **[ticket_server.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/ticket_server.py)**: Manages a `ticket.db` SQLite database with `create_ticket` and `get_ticket_status` tools.
3. **[document_server.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/document_server.py)**: Integrates directly with our local FAISS vector store to search files over JSON-RPC.

To prevent log contamination, all three servers pre-configure logging to direct outputs to `sys.stderr` and set `app_logger._configured = True`. This ensures that standard logs never write to `sys.stdout`, which is strictly reserved for JSON-RPC messages.

### B. Python Tool Wrappers and Structured Error Handling
Each tool wrapper (e.g. `backend/app/tools/employee_tool.py`) calls the `mcp_client_manager` inside a `try-except` block. If the server fails, it catches the error and returns a dictionary:
```python
{
    "success": False,
    "error": "Error message details",
    "mcp_server": "employee-db-mcp",
    "selected_tool": "get_employee"
}
```
This structured format ensures the LLM receives details of the error and can inform the user gracefully instead of raising a server crash.

### C. Agent Integration
Inside our specialist agent code, we run intent classifiers to query the tool if necessary. For example, in `hr_agent.py`:
```python
# Check if looking up by employee ID
id_match = re.search(r'\b(?:employee\s+)?(\d{3,})\b', query)
if id_match:
    emp_id = int(id_match.group(1))
    res = employee_tool.get_employee(emp_id)
    if state is not None:
        state["selected_tool"] = res.get("selected_tool")
        state["mcp_server"] = res.get("mcp_server")
    tool_info = f"\n\n--- Employee DB Tool Result ---\n{json.dumps(res)}\n---------------------------------"
```
This tool result is appended directly to the system prompt, providing ground truth data.

---

## 6. Phase 7 Concepts: Where We Go From Here

Phase 6 built stdio-based servers running as python subprocesses. In **Phase 7**, you can explore more advanced enterprise patterns:

1. **Recursive LLM Tool-Calling Loops:** Instead of hardcoded regex or keyword detection, configure the Gemini model using its native `tools` configuration. The model emits a `FunctionCall` event, the client runs it, and feeds back a `FunctionResponse` until the model is satisfied.
2. **Server-Sent Events (SSE) Transport:** Instead of running the MCP server as a local stdio child process, run it as a standalone remote microservice. The client connects over HTTP using Server-Sent Events (SSE) for server-to-client streaming, and sends commands via POST requests.
3. **Multi-Server Orchestration & Routing:** Create an MCP gateway that aggregates hundreds of servers dynamically. The gateway reads the list of tools from all servers and uses semantic routing to dispatch requests to the correct server.
4. **Security Sandbox (MCP Sandbox):** Running arbitrary MCP servers locally poses security risks. Using sandboxes (like Docker or gVisor) to run the servers ensures they cannot access the main server's filesystem or network.

---

## 7. 20 Interview Questions & Answers (Q&A)

Here are 20 questions and answers covering MCP, JSON-RPC, stdio pipes, tool wrapping, and agent integrations to test your knowledge:

### Q1: What is MCP and how does it differ from traditional tool calling?
**A:** MCP (Model Context Protocol) is an open standard protocol specifying how AI clients and servers exchange information (prompts, resources, and tools) via JSON-RPC. Traditional tool calling is proprietary and custom-coded per application; MCP decouples integrations so any client supporting MCP can use any MCP-compliant server.

### Q2: Why do we use stdin and stdout for stdio-based MCP servers?
**A:** Stdio (standard input and standard output) is the simplest, lowest-latency channel for inter-process communication (IPC) on a single machine. The host application writes to the child process's `stdin` and reads JSON-RPC responses from the child's `stdout`.

### Q3: Why is logging to sys.stdout fatal for stdio MCP servers, and how do we prevent it?
**A:** Stdio servers expect `stdout` to contain *only* valid JSON-RPC message frames. If standard application loggers print text (like `2026-06-13 | INFO | Loaded database`) to `stdout`, the client's JSON parser crashes. To prevent this, we redirect all logging outputs to `sys.stderr`, which the client handles separately or ignores.

### Q4: Explain the differences between the initialize, tools/list, and tools/call methods in MCP.
**A:** 
* `initialize`: Handshake exchange sent by the client to negotiate capabilities and protocol versions.
* `tools/list`: Sent by the client to query all tools the server exposes along with their input validation schemas.
* `tools/call`: Sent by the client to execute a specific tool with parameter arguments.

### Q5: How does a client validate arguments before calling an MCP tool?
**A:** The client reads the JSON Schema returned by the server during the `tools/list` handshake. It can validate the input dictionary against this schema locally (using libraries like `jsonschema`) before making the IPC call.

### Q6: What is the benefit of spawning MCP servers via sys.executable in a Python application?
**A:** Using `sys.executable` ensures that the spawned child subprocess uses the exact same Python interpreter and virtual environment virtual env as the parent process. This guarantees that all required libraries (like `fastapi`, `google-generativeai`, `faiss`) are available inside the child server.

### Q7: How does Phase 6 preserve Phase 5 LangGraph workflow states?
**A:** The LangGraph state schema is updated to include `selected_tool` and `mcp_server`. Within the specialist graph nodes (e.g. `hr_node`), we extract the message, run the tool, update a local copy of the state dictionary, and return the modified state containing the executed tool details.

### Q8: What is structured error handling in a tool wrapper, and why is it important?
**A:** Instead of letting exceptions crash the application, tool wrappers catch exceptions and return a unified result format: `{"success": False, "error": "...", "mcp_server": "...", "selected_tool": "..."}`. This allows the agent and the supervisor to read the error and respond gracefully to the user.

### Q9: Why is standard sqlite3 thread-safe, but why is it still important to handle database initialization properly?
**A:** SQLite allows multiple threads to read from a database, but writes lock the file. We run database initialization (`init_db`) on server startup to ensure tables exist, and we open and close connections within short, discrete transactions during tool calls to prevent file locking issues.

### Q10: How does the document search MCP server translate text queries into vector database searches?
**A:** The server receives the text query via JSON-RPC, uses the `google-generativeai` SDK to call the embedding model (e.g., `gemini-embedding-001`), extracts the vector float array, and queries our FAISS index to return the top-k matched documents and their similarity scores.

### Q11: In what scenario would you choose HTTP/SSE transport over stdio transport in MCP?
**A:** Use HTTP/SSE when the MCP server is hosted on a separate remote machine, runs in a dockerized container, or needs to serve multiple client applications concurrently. Stdio is restricted to processes running on the same local machine.

### Q12: Why is recursive tool calling sometimes preferred over intent classification?
**A:** Intent classification (e.g., regex/keywords) is deterministic but fragile; it breaks if the query uses unexpected phrasing. Recursive tool calling allows the LLM to dynamically formulate tool arguments and determine multiple steps of execution itself.

### Q13: What does the client do if an MCP server subprocess hangs?
**A:** The client manager sets timeouts on standard stream reads. If a write or read takes longer than the timeout threshold, it throws a `TimeoutError`, terminates the child subprocess, and returns a structured failure dictionary.

### Q14: How does a supervisor agent synthesize answers from multiple specialist agent responses?
**A:** In a multi-agent LangGraph workflow, the supervisor node waits until all specialist nodes have run and populated their response slots (`hr_response`, `it_response`, `finance_response`). It then formats a prompt containing all responses and calls the LLM to output a single, cohesive final report.

### Q15: Why is JSON-RPC 2.0 chosen as the messaging format in MCP?
**A:** JSON-RPC 2.0 is a lightweight, widely adopted, transport-agnostic remote procedure call protocol. It cleanly structures requests, notifications, responses, and errors, making it ideal for standardizing agent-tool communications.

### Q16: How do we update the React frontend dynamically to display tool execution paths?
**A:** The backend FastAPI endpoint responds with a `ChatResponse` payload including `selected_tool` and `mcp_server`. The React frontend stores this in state and renders structured badges (`🔧 Tool: ...` and `📡 Server: ...`) next to the message in the chat feed.

### Q17: What is a resource in MCP terms, and how does it differ from a tool?
**A:** A tool is an executable function that performs actions or mutates state (e.g., `create_employee`). A resource is static read-only data exposed by the server (such as file contents, raw logs, or DB configurations) that the client can subscribe to or read.

### Q18: What is a prompt template in MCP, and how is it used?
**A:** Prompts are pre-defined templates exposed by the server (e.g., "Analyze code quality"). The client can fetch these templates, fill in the arguments, and feed the resulting system prompt to the LLM.

### Q19: How does the Python `subprocess.Popen` communicate in real-time?
**A:** By setting `bufsize=1` (line-buffered) or `universal_newlines=True` (text mode), we ensure that lines written to `stdin` are immediately flushed through the OS pipe, preventing buffering delays and keeping communication real-time.

### Q20: Explain the importance of testing tools in isolation before testing agent integration.
**A:** Isolating tool tests (like `test_mcp_tools.py`) allows developers to verify JSON-RPC serialization, database schemas, and subprocess connections independently of LLM reasoning. This makes it trivial to distinguish between a broken database connection and an LLM routing error.

---
*Created as part of the Phase 6 Implementation of the Enterprise AI Assistant.*
