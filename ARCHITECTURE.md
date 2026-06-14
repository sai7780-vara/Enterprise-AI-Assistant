# Phase 1 Architecture — Minimal Full-Stack Chat App

This document outlines the architecture, flow diagrams, data paths, and file breakdown for Phase 1 of the Enterprise AI Knowledge Assistant.

---

## 1. Overall Architecture

Phase 1 uses a classic client-server model. The application consists of two main decoupled tiers:
1. **Frontend (React / Vite):** The user interface providing a chat feed and text inputs.
2. **Backend (FastAPI):** A lightweight web server routing user messages directly to the Gemini API.

```
┌──────────────┐                  ┌──────────────┐                  ┌──────────────┐
│  React App   │ ──(HTTP POST)──► │ FastAPI App  │ ──(Python SDK)─► │  Gemini API  │
│  (Port 5173) │ ◄──(JSON Resp)── │ (Port 8000)  │ ◄──(Gen Text)─── │ (Remote Model│
└──────────────┘                  └──────────────┘                  └──────────────┘
```

---

## 2. Execution Flow & Data Movement

### A. Frontend Data Flow
1. **User Action:** The user types a query in the input text area and hits `Send`.
2. **State Transition:** The message is added locally to the messages list in `App.jsx`, and a loading state (`isSending = true`) is triggered.
3. **API Dispatch:** `App.jsx` calls `sendChatMessage(text)` in `src/api.js`.
4. **Network Request:** `api.js` submits an HTTP `POST` to `http://localhost:8000/api/chat` with JSON body:
   ```json
   { "message": "What is 2+2?" }
   ```
5. **UI Update:** Once the response arrives, the reply is added to the messages list, and the loader is hidden.

### B. Backend Data Flow
1. **HTTP Listener:** FastAPI receives the request on `/api/chat`.
2. **Validation:** The incoming payload is validated against `ChatRequest` schema.
3. **Route Dispatcher:** `routes.py` calls the service method `gemini_service.generate_reply(message)`.
4. **Gemini Invocation:** `gemini_service` forwards the message to Google Gemini API via `model.generate_content(message)`.
5. **Output Marshalling:** The response is returned to `routes.py` which wraps it in `ChatResponse` schema:
   ```json
   { "reply": "2 + 2 is 4." }
   ```
6. **HTTP Serialization:** FastAPI returns a `200 OK` status with the JSON response to the browser.

---

## 3. Important Files & What They Do

### A. Backend (`backend/`)
* **[app/main.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/main.py):** Initializes the FastAPI application, sets up CORS permissions, and mounts `/api` routes.
* **[app/api/routes.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/api/routes.py):** Defines REST endpoints `/api/health` and `/api/chat`. Contains error catching so that exceptions return clean HTTP 502/500 responses.
* **[app/services/gemini_service.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/services/gemini_service.py):** Instantiates the Gemini SDK client using settings and calls the AI model.
* **[app/schemas/chat.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/schemas/chat.py):** Declares Pydantic models `ChatRequest` and `ChatResponse`.
* **[app/core/config.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/core/config.py):** Stores app settings (model name, API keys) read from environmental variables.
* **[app/core/logger.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/core/logger.py):** Standardizes console logging across the backend.

### B. Frontend (`frontend/`)
* **[src/App.jsx](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/frontend/src/App.jsx):** Controls the overall page state, input fields, and lists of messages.
* **[src/components/ChatMessage.jsx](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/frontend/src/components/ChatMessage.jsx):** Renders individual chat message bubbles differently depending on the sender ("user" vs. "bot").
* **[src/api.js](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/frontend/src/api.js):** Contains helper functions to call the FastAPI server backend.
* **[src/styles.css](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/frontend/src/styles.css):** Contains basic layouts, bubble alignments, and theme coloring.
