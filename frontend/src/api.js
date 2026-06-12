// All backend calls live here, separate from UI components.
// One place to change if the API URL or shape changes.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Send a user message to POST /api/chat, return the reply string.
export async function sendChatMessage(message) {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    throw new Error(`Backend error (${res.status})`);
  }

  const data = await res.json();
  return data.reply; // matches ChatResponse on the backend
}
