# Phase 3 Architecture — Production-Style RAG

This document outlines the architecture, flow diagrams, data paths, and file breakdown for Phase 3 of the Enterprise AI Knowledge Assistant.

---

## 1. Overall Architecture

Phase 3 introduces user-controlled retrieval parameters and a metadata-enriched citation flow from the backend straight through to the frontend React UI:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              React Frontend                            │
│                                                                        │
│   ┌───────────────┐      ┌─────────────┐       ┌───────────────┐       │
│   │ App.jsx       │ ───► │ Slider UI   │ ───►  │ ChatMessage   │       │
│   │ (State/Hooks) │      │ (top_k=1-10)│       │ (Source Cards)│       │
│   └───────┬───────┘      └─────────────┘       └───────▲───────┘       │
└───────────┼────────────────────────────────────────────┼───────────────┘
            │ (HTTP POST /api/chat with top_k)           │
            ▼                                            │
┌────────────────────────────────────────────────────────┼───────────────┐
│                            FastAPI Backend             │ (JSON Response│
│                                                        │  with Sources)│
│   ┌───────────────┐      ┌─────────────────┐    ┌──────┴───────┐       │
│   │ routes.py     │ ───► │ rag_service.py  │ ──►│ ChatResponse │       │
│   └───────────────┘      └────────┬────────┘    └──────────────┘       │
│                                   │                                    │
│                                   ▼                                    │
│                          ┌─────────────────┐                           │
│                          │ vector_store.py │                           │
│                          │ (FAISS FlatIP)  │                           │
│                          └─────────────────┘                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Dynamic Retrieval & Grounding Flow

1. **User Selection:** The user adjusts the `top_k` slider on the React panel (e.g. settings `top_k = 3`).
2. **Payload Construction:** The frontend packages the request:
   ```json
   {
     "message": "Explain our vacation policy",
     "use_rag": true,
     "top_k": 3
   }
   ```
3. **API Routing:** FastAPI routes this to `chat` in `routes.py`.
4. **Vector Database Query:**
   - `rag_service` uses `gemini-embedding-001` to generate a 3072-dimension query vector.
   - It invokes `vector_store.search(query_embedding, top_k=3)`.
   - `vector_store` performs a cosine similarity lookup against normalized vectors in FAISS.
5. **Metadata Retrieval:** The FAISS index match indices map to text segments inside `knowledge_store.pkl`. The server retrieves matching texts and structured metadata (`document_name`, `page_number`, `chunk_id`).
6. **Prompt Formatting:** The text snippets are formatted and injected as a system instruction into the Gemini model.
7. **Score Conversion & Synthesis:**
   - The highest similarity score is multiplied by 100 to yield a confidence rating.
   - Gemini generates a grounded response.
   - The backend returns the synthesized `reply`, `sources` array (containing text, filename, page, score), and `confidence` percentage.
8. **UI Rendering:** React parses the response:
   - Displays the reply text.
   - Shows the confidence percentage.
   - Renders a row of expandable "Source Citation Cards". When clicked, they slide open to show the exact retrieved chunk text.

---

## 3. Important Files & What They Do

### A. Frontend Components (`frontend/src/`)
* **[App.jsx](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/frontend/src/App.jsx):** Controls global states, sidebar layouts, dynamic slider states, and triggers.
* **[components/ChatMessage.jsx](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/frontend/src/components/ChatMessage.jsx):** Standard message bubble component updated with a layout of source citation cards that expand when clicked.
* **[components/KnowledgeManager.jsx](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/frontend/src/components/KnowledgeManager.jsx):** Handles uploading new files and displays a list of currently indexed documents with the ability to delete them.

### B. Backend Services (`backend/app/services/`)
* **[document_service.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/services/document_service.py):** Upgraded to read PDF files page-by-page. Appends `_p{page_number}_c{chunk_index}` to the metadata structure.
* **[vector_store.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/services/vector_store.py):** Manages the FAISS Index. Normalizes vectors for accurate inner-product cosine similarity searches.
* **[rag_service.py](file:///c:/Users/rukka/OneDrive/Desktop/AI%20Tools/enterprise-ai-assistant/enterprise-ai-assistant/backend/app/services/rag_service.py):** Orchestrates the generation pipeline, constructs context prompt headers, filters retrieval counts dynamically using the API's `top_k` parameter, and calculates the similarity-based confidence percentage.
