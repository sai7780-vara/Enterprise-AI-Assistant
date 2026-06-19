# Phase 8 Kubernetes Technical Architecture Guide

This document describes the Kubernetes cluster architecture for the **Enterprise AI Knowledge Assistant** deployed locally on Minikube.

---

## 1. Request Flow and Integration Diagram

The diagram below details the path of a user's request from the browser, through the Ingress controller, and into the pods, illustrating where storage mounts and tool invocations occur.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant Ingress as Ingress Controller (Nginx)
    participant FE as frontend Pod (Port 80)
    participant BE as backend Pod (Port 8000)
    participant MCPEmp as employee-db-mcp Pod (Port 8001)
    participant MCPTck as ticket-mcp Pod (Port 8002)
    participant MCPDoc as document-mcp Pod (Port 8003)
    database VolFaiss as faiss-pvc Volume
    database VolEmp as employee-db-pvc Volume
    database VolTck as ticket-db-pvc Volume

    %% Frontend request
    User->>Ingress: Access http://ai-assistant.local/
    Ingress->>FE: Route to frontend-service:80
    FE-->>User: Return React App bundle

    %% Chat request
    User->>Ingress: Chat Request: http://ai-assistant.local/api/chat
    Ingress->>BE: Route to backend-service:8000
    
    %% RAG search
    Note over BE: Supervisor targets Agent Node
    BE->>MCPDoc: HTTP POST JSON-RPC (search_documents)
    Note over MCPDoc: Reloads FAISS index
    MCPDoc->>VolFaiss: Read knowledge_store.pkl
    VolFaiss-->>MCPDoc: Return embeddings
    MCPDoc-->>BE: Return search chunks

    %% Database SQL searches
    BE->>MCPEmp: HTTP POST JSON-RPC (get_employee)
    MCPEmp->>VolEmp: Query SQLite database
    VolEmp-->>MCPEmp: Return record
    MCPEmp-->>BE: Return employee data

    %% Ticket creation
    BE->>MCPTck: HTTP POST JSON-RPC (create_ticket)
    MCPTck->>VolTck: Insert SQL support ticket
    VolTck-->>MCPTck: Confirm save
    MCPTck-->>BE: Return ticket details

    BE-->>User: Return synthesized reply to Browser
```

---

## 2. Ingress and Routing Pathways

Traffic routing is controlled via the `ai-assistant-ingress` controller (backed by Nginx):
*   **Default Route (`/`):** Forwards static asset requests to the `frontend` service (container port `80`).
*   **API Path (`/api`):** Forwards backend calls to the `backend` service (container port `8000`).

This ensures that the browser only communicates with a single endpoint (`http://ai-assistant.local`), eliminating CORS limitations.

---

## 3. Deployment Manifest Details

Each deployment manifest specifies pod replication, container commands, resource bounds, and environment mappings.

### A. `k8s/configmap.yaml`
Acts as a central repository for application parameters. Key parameters include:
*   `GEMINI_MODEL`: Model engine target.
*   `EMPLOYEE_DB_MCP_URL`, `TICKET_MCP_URL`, `DOCUMENT_MCP_URL`: DNS host mappings that translate to cluster service names (e.g. `http://ticket-mcp:8002`).

### B. `k8s/secret.yaml`
Provides opaque data mapping. It declares the `GEMINI_API_KEY` placeholder. Under the hood, Pods map this Secret as an environment variable using `valueFrom.secretKeyRef`.

### C. `k8s/mcp-employee-db.yaml` & `k8s/mcp-ticket.yaml`
*   **Image:** `ai-assistant-backend:latest`
*   **Command Override:** Starts Python explicitly with `python app/mcp/employee_db_server.py` or `python app/mcp/ticket_server.py`.
*   **Storage Mount:** Mounts its respective PVC (`employee-db-pvc` or `ticket-db-pvc`) to `/data` in read-write mode. This is where the SQLite databases are persisted.
*   **Service:** `ClusterIP` routing on ports `8001` and `8002`.

### D. `k8s/mcp-document.yaml`
*   **Image:** `ai-assistant-backend:latest`
*   **Command Override:** Starts Python with `python app/mcp/document_server.py`.
*   **Storage Mount:** Mounts the shared `faiss-pvc` volume at `/app/app/data`.
*   **API Secrets:** Injects `GEMINI_API_KEY` from the Secret to authenticate with Google's embedding endpoint.
*   **Service:** `ClusterIP` routing on port `8003`.

### E. `k8s/backend.yaml`
*   **Image:** `ai-assistant-backend:latest`
*   **Command:** Runs the default image entrypoint (Uvicorn running FastAPI).
*   **Storage Mount:** Mounts `faiss-pvc` at `/app/app/data`. This allows the API to write uploaded files to the same volume that the `document-mcp` service reads.
*   **Service:** NodePort mapping port `8000` internally to port `30000` externally.

### F. `k8s/frontend.yaml`
*   **Image:** `ai-assistant-frontend:latest`
*   **Service:** NodePort mapping port `80` internally to port `30080` externally.

---

## 4. Volume Mounting and Synchronization

To share RAG indexes between the `backend` and `document-mcp` pods:
*   We define a single `PersistentVolumeClaim` named `faiss-pvc`.
*   In the `backend` Pod template, `faiss-pvc` is mounted to `/app/app/data`.
*   In the `document-mcp` Pod template, `faiss-pvc` is also mounted to `/app/app/data`.
*   Since both pods execute on the same Minikube node, the hostPath engine mounts the same folder to both pods.
*   When a file is uploaded, the backend writes to `/app/app/data/knowledge_store.pkl`. Because `document-mcp` reloads the store on each search call, it accesses the modified file instantly.
