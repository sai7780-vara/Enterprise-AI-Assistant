# Phase 6 Architecture — MCP & Tool Calling

This document outlines the architecture, flow diagrams, data paths, and file breakdown for Phase 6 of the Enterprise AI Knowledge Assistant.

---

## 1. Overall Architecture

Phase 6 introduces the **Model Context Protocol (MCP)**, decoupling the specialist agents from direct database connections and search libraries. The agents run tool wrappers that communicate over standard input/output (stdio) streams with decoupled, standalone MCP Server subprocesses using JSON-RPC 2.0.

```mermaid
graph TD
    User([User]) <--> React[React Frontend App.jsx]
    React <-->|HTTP POST /api/chat| FastAPI[FastAPI Backend routes.py]
    FastAPI <--> Supervisor[Supervisor Agent]
    
    subgraph Agent Cluster
        Supervisor -->|routes| HR[HR Agent]
        Supervisor -->|routes| IT[IT Agent]
        Supervisor -->|routes| Finance[Finance Agent]
        Supervisor -->|routes| RAG[RAG Agent]
    end

    subgraph Tool Wrapper Layer
        HR -->|calls| ET[employee_tool.py]
        IT -->|calls| TT[ticket_tool.py]
        Finance -->|calls| TT
        RAG -->|calls| DT[document_tool.py]
    end

    subgraph MCP Client (Host Process)
        ET -->|execute| Manager[MCPClientManager client.py]
        TT -->|execute| Manager
        DT -->|execute| Manager
    end

    subgraph MCP Servers (Subprocesses)
        Manager <-->|stdio / JSON-RPC| S1[employee_db_server.py]
        Manager <-->|stdio / JSON-RPC| S2[ticket_server.py]
        Manager <-->|stdio / JSON-RPC| S3[document_server.py]
    end

    S1 <--> DB1[(employee.db SQLite)]
    S2 <--> DB2[(ticket.db SQLite)]
    S3 <--> VS[(FAISS Vector DB)]
```

---

## 2. In-Depth Execution Flow & JSON-RPC

### A. Communication Flow
1. **Agent Intent Trigger:** A specialist agent (e.g. `hr_agent.py`) intercepts a request mentioning an employee ID (e.g., `"Get details for employee 101"`).
2. **Tool Execution:** The agent calls the Python tool wrapper: `employee_tool.get_employee(101)`.
3. **Client Subprocess Launch:**
   - The `MCPClientManager` checks if the target server (`employee_db_server.py`) is running.
   - If not, it spawns it as a background child subprocess using `sys.executable`.
4. **JSON-RPC Transaction:**
   - The client writes a standard JSON-RPC 2.0 request frame to the child's `stdin` and flushes the buffer:
     ```json
     {
       "jsonrpc": "2.0",
       "method": "tools/call",
       "params": {
         "name": "get_employee",
         "arguments": {
           "id": 101
         }
       },
       "id": 1
     }
     ```
   - The MCP Server process runs the query on `employee.db`, captures the row, and writes the JSON-RPC response back to its `stdout`:
     ```json
     {
       "jsonrpc": "2.0",
       "result": {
         "content": [
           {
             "type": "text",
             "text": "{\"id\": 101, \"name\": \"Sai Kiran\", \"department\": \"Engineering\"}"
           }
         ]
       },
       "id": 1
     }
     ```
5. **Logging Safety:** To avoid contaminating standard output (`stdout`), all logs inside the server scripts are explicitly routed to standard error (`sys.stderr`).
6. **Structured Exception Catching:** If a subprocess exits or times out, the tool wrapper catches the exception and returns a structured dictionary:
   ```json
   {
     "success": false,
     "error": "Timeout or connection lost",
     "selected_tool": "get_employee",
     "mcp_server": "employee-db-mcp"
   }
   ```
7. **Synthesis:** The successful tool result or error dict is appended to the agent's prompt context, allowing Gemini to output a grounded answer.

---

## 3. Important Files & What They Do

### A. MCP Servers (`backend/app/mcp/`)
* **[client.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/client.py):** Spawns stdio subprocesses, controls standard read/write streams, runs JSON handshakes, handles time-outs, and terminates connections on backend shutdown.
* **[employee_db_server.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/employee_db_server.py):** Exposes `get_employee`, `search_employee`, and `create_employee` tools querying the `employee.db` SQLite database.
* **[ticket_server.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/ticket_server.py):** Exposes `create_ticket` and `get_ticket_status` tools querying the `ticket.db` SQLite database.
* **[document_server.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/mcp/document_server.py):** Integrates with the RAG FAISS indexes over JSON-RPC.

### B. Tool Wrappers (`backend/app/tools/`)
* **[employee_tool.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/tools/employee_tool.py):** Python wrapper connecting `hr_agent` with the `employee-db-mcp` client connection.
* **[ticket_tool.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/tools/ticket_tool.py):** Python wrapper exposing IT support ticket creators and trackers.
* **[document_tool.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/tools/document_tool.py):** Python wrapper exposing document FAISS search functionalities.

### C. Test Suites (`backend/`)
* **[test_mcp_tools.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/test_mcp_tools.py):** Directly verifies JSON-RPC stdio handshakes, database locks, and FAISS RAG servers in isolation.
