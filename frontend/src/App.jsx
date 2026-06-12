// Chat page: holds message state, renders the conversation, sends input.
import { useState } from "react";
import { sendChatMessage } from "./api.js";
import ChatMessage from "./components/ChatMessage.jsx";

export default function App() {
  // messages: array of { role: "user" | "assistant", text: string }
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    // Show the user's message immediately.
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const reply = await sendChatMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Enter sends; Shift+Enter could be added later for newlines.
  function handleKeyDown(e) {
    if (e.key === "Enter") handleSend();
  }

  return (
    <div className="app">
      <h1>Enterprise AI Knowledge Assistant</h1>
      <p className="subtitle">Phase 1 — FastAPI + React + Gemini</p>

      <div className="chat-window">
        {messages.length === 0 && (
          <p className="empty">Ask something to start.</p>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} role={m.role} text={m.text} />
        ))}
        {loading && <ChatMessage role="assistant" text="Thinking..." />}
      </div>

      {error && <p className="error">{error}</p>}

      <div className="input-row">
        <input
          className="input-box"
          value={input}
          placeholder="Type a message..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="send-btn" onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}
