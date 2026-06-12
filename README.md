# Enterprise AI Knowledge Assistant — Phase 1

A minimal full-stack chat app: **React frontend** talks to a **FastAPI backend**,
which calls the **Google Gemini API** and returns the reply.

This is **Phase 1 only**. No RAG, agents, MCP, Docker, Kubernetes, or Azure yet —
those come in later phases. The goal here is a clean, beginner-friendly base.

---

## Project structure

```
enterprise-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # HTTP endpoints: /api/health, /api/chat
│   │   ├── core/
│   │   │   ├── config.py          # Reads env vars into one Settings object
│   │   │   └── logger.py          # Central logging setup
│   │   ├── schemas/
│   │   │   └── chat.py            # Request/response models (Pydantic)
│   │   ├── services/
│   │   │   └── gemini_service.py  # Talks to Gemini; isolated from web layer
│   │   └── main.py               # Builds FastAPI app, CORS, mounts routes
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── ChatMessage.jsx    # One message bubble (presentational)
    │   ├── api.js                # All backend calls in one place
    │   ├── App.jsx               # Chat page: state + input + render
    │   ├── main.jsx              # React entry point
    │   └── styles.css
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env.example
    └── .gitignore
```

### Why this layout (clean architecture)

Each folder has one job, so you can change one part without breaking others:

- **api/** — thin HTTP layer. Validates input, calls a service, returns output. No logic.
- **core/** — cross-cutting setup: config and logging. Nothing else reads env vars directly.
- **schemas/** — the exact shape of data crossing the API. FastAPI validates against these.
- **services/** — business logic and external calls (Gemini). The web layer doesn't know *how* Gemini works, only that it can ask for a reply. In Phase 2+ you swap this file for RAG/agents without touching the endpoints.

---

## Backend setup

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env from the example, then add your real key
cp .env.example .env
#   edit .env  ->  GEMINI_API_KEY=...   (get one at https://aistudio.google.com/apikey)

# 4. Run the server
uvicorn app.main:app --reload
```

Backend now runs at **http://localhost:8000**.
Check it: open **http://localhost:8000/api/health** → `{"status":"ok"}`.
Interactive API docs: **http://localhost:8000/docs**.

---

## Frontend setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. (optional) copy env example if you changed the backend port
cp .env.example .env

# 3. Run the dev server
npm run dev
```

Frontend runs at **http://localhost:5173**. Open it and chat.

---

## How the frontend talks to the backend

1. You type a message and click **Send** (or press Enter) in `App.jsx`.
2. `App.jsx` calls `sendChatMessage(text)` in `src/api.js`.
3. `api.js` does a `POST` to `http://localhost:8000/api/chat` with JSON body
   `{ "message": "your text" }`.
4. FastAPI receives it in `routes.py`, validated against the `ChatRequest` schema.
5. The backend returns JSON `{ "reply": "..." }`, which React renders as a bubble.

CORS is enabled in `main.py` so the browser (port 5173) is allowed to call the
API (port 8000). Without CORS the browser would block the request.

---

## How the Gemini API is called

All Gemini logic lives in `backend/app/services/gemini_service.py`:

1. On startup, `GeminiService` reads `GEMINI_API_KEY` from the environment
   (loaded from `.env` by `config.py`) and configures the `google-generativeai` client.
2. It creates a model handle for `GEMINI_MODEL` (default `gemini-1.5-flash`).
3. On each request, `generate_reply(message)` calls `model.generate_content(message)`
   and returns the response text.
4. `routes.py` wraps that call in try/except: real errors are logged server-side,
   and the client gets a clean `502` instead of a stack trace.

---

## Endpoints

| Method | Path          | Purpose                          |
|--------|---------------|----------------------------------|
| GET    | `/api/health` | Liveness check                   |
| POST   | `/api/chat`   | Send a message, get Gemini reply |

`POST /api/chat` request body:
```json
{ "message": "Hello!" }
```
Response:
```json
{ "reply": "Hi! How can I help?" }
```

---

## Next phases (not included yet)

Phase 2+ will layer on RAG, agents, MCP servers, A2A, Docker, Kubernetes,
CI/CD, and Azure — each on top of this clean base.
