// All backend calls live here, separate from UI components.
// One place to change if the API URL or shape changes.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Send a user message to POST /api/chat.
 * Returns an object containing the response text and referenced source documents.
 */
export async function sendChatMessage(message, useRag = true, topK = 4) {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, use_rag: useRag, top_k: topK }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Backend error (${res.status})`);
  }

  return await res.json(); // returns { reply: str, sources: Array, confidence: float }
}

/**
 * Upload a document to the knowledge base (POST /api/documents).
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/api/documents`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Upload failed (${res.status})`);
  }

  return await res.json();
}

/**
 * Retrieve list of active knowledge base documents (GET /api/documents).
 */
export async function getDocuments() {
  const res = await fetch(`${BASE_URL}/api/documents`);
  if (!res.ok) {
    throw new Error(`Failed to list documents (${res.status})`);
  }

  const data = await res.json();
  return data.documents; // Array of DocumentMetadata
}

/**
 * Delete a document from the index by its ID (DELETE /api/documents/{id}).
 */
export async function deleteDocument(docId) {
  const res = await fetch(`${BASE_URL}/api/documents/${docId}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Delete failed (${res.status})`);
  }

  return await res.json();
}
