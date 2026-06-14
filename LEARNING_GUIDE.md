# Phase 1 Learning Guide — Minimal Full-Stack Chat App

## 1. What Problem Was Not Solved in the Previous Phase
This is the very first phase (Phase 1) of the project. There is no previous phase. We start by building a clean, simple base with direct communication between the client, backend, and the LLM, without any grounding or advanced states.

## 2. Why This Phase Was Needed
Before implementing advanced Retrieval-Augmented Generation (RAG) or multi-agent networks, we need a robust, clean, and decoupling-focused foundation. Building a simple full-stack app first ensures that:
- The React frontend and FastAPI backend are properly configured to talk to each other.
- Cross-Origin Resource Sharing (CORS) is set up and working.
- The Gemini API integration works without extra layers of complexity.
- We establish a "Clean Architecture" design patterns early on, so future additions are modular.

## 3. Technical Skills Used in This Phase
* **React State & Hook Management:** Using standard `useState` and `useEffect` in React to manage chat messages, loading states, and text inputs.
* **FastAPI Web Framework:** Building high-performance, asynchronous REST APIs with auto-generated documentation (`/docs`).
* **Pydantic Validation:** Using Pydantic models to strictly enforce the schema of data coming in and out of our API.
* **Google Generative AI SDK:** Interfacing with Gemini models (`gemini-1.5-flash`) programmatically using the Python SDK.
* **Environment Variables Integration:** Isolating secrets (API keys) in `.env` files using `python-dotenv` on the backend and Vite env capabilities on the frontend.

## 4. What Was Implemented in This Phase
* **React Chat Interface:** A responsive chat bubble layout with user inputs, send buttons, and scrollable chat feeds.
* **FastAPI Router:** Two core endpoints:
  - `GET /api/health` — A health check to verify backend status.
  - `POST /api/chat` — The main chat endpoint.
* **Gemini Service Integration:** A decoupled service (`gemini_service.py`) that initializes the model client and manages API requests.
* **CORS Settings:** Enabled middleware in FastAPI to allow the Vite server (port `5173`) to call the API (port `8000`).

## 5. What This Phase Still Cannot Do
* **No Memory:** The chatbot has no conversation memory (history). Every message sent is treated as a completely isolated single-turn query.
* **No Document Grounding (RAG):** The system cannot read or answer questions based on uploaded files (PDFs, text files).
* **No Agent Capabilities:** It cannot route queries, search databases, or execute tools.

## 6. What is Moved to the Next Phase
In **Phase 2 (Local RAG)**, we will solve the document-grounding problem by:
- Creating a PDF/Text document ingestion pipeline.
- Implementing local chunking and vector embedding generation.
- Storing vectors locally in memory and searching them using cosine similarity.
- Grounding Gemini's replies in the retrieved document context.

---

## 7. Beginner-Friendly Questions & Answers

### Q1: What is CORS, and why does the browser block my requests if it is missing?
**A:** CORS stands for Cross-Origin Resource Sharing. It is a security feature enforced by web browsers. If your React app is running on `http://localhost:5173` and tries to fetch data from `http://localhost:8000`, they are on different "origins" (ports). By default, browsers block these cross-origin requests unless the backend explicitly sends a header (`Access-Control-Allow-Origin`) giving permission.

### Q2: Why do we use Pydantic schemas in the FastAPI routes?
**A:** Pydantic validates incoming HTTP request payloads. If a client sends invalid JSON (e.g. misses the `"message"` key or sends an integer instead of a string), Pydantic automatically rejects it with a `422 Unprocessable Entity` response before running any of our backend logic. It also generates interactive Swagger docs.

### Q3: Why is it important to separate Gemini service code from API route code?
**A:** This is called Clean Architecture or Separation of Concerns. The API routes file should only handle HTTP concerns (reading requests, calling services, returning responses). It should not care *how* Gemini generates text. That way, if we swap Gemini for a local LLM or add RAG retrieval later, we only change the service file, keeping the HTTP routes completely untouched.

### Q4: How do we keep the Gemini API key secure?
**A:** We never hardcode the API key in the source code. Instead, we save it in a `.env` file which is added to `.gitignore` so it is never committed to GitHub. The backend loads it dynamically at runtime using `python-dotenv`.

### Q5: What does the `--reload` flag do in uvicorn?
**A:** The `--reload` flag tells the Uvicorn ASGI server to watch files for changes and automatically reload the server whenever you save a file. This is highly useful for local development but should be turned off in production.
