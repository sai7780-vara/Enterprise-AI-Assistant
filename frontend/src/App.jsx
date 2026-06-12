// Chat page: holds message state, renders the conversation, sends input.
import { useState } from "react";
import { sendChatMessage } from "./api.js";
import ChatMessage from "./components/ChatMessage.jsx";
import KnowledgeManager from "./components/KnowledgeManager.jsx";

export default function App() {
  // messages: array of { role: "user" | "assistant", text: string, sources?: string[] }
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [useRag, setUseRag] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    // Show the user's message immediately.
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const response = await sendChatMessage(text, useRag);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: response.reply, sources: response.sources }
      ]);
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
    <div className={`app-container ${isSidebarOpen ? "sidebar-visible" : ""}`}>
      {/* Knowledge Sidebar Drawer */}
      <KnowledgeManager
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Sidebar Overlay Backdrop */}
      {isSidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setIsSidebarOpen(false)} />
      )}

      {/* Main Chat Area */}
      <div className="main-chat-area">
        <header className="app-header">
          <div className="header-titles">
            <h1>Enterprise AI Knowledge Assistant</h1>
            <p className="subtitle">Phase 2 — Local RAG with FAISS & Gemini</p>
          </div>
          <button
            className="sidebar-toggle-btn"
            onClick={() => setIsSidebarOpen(true)}
            title="Open Knowledge Base Settings"
          >
            📚 Knowledge Base
          </button>
        </header>

        <div className="chat-window">
          {messages.length === 0 && (
            <div className="empty-state">
              <span className="empty-icon">🤖</span>
              <p className="empty">Hello! Ask a question to get started.</p>
              <p className="empty-sub">
                Open the **Knowledge Base** at the top right to upload PDFs/TXT files for custom context.
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <ChatMessage key={i} role={m.role} text={m.text} sources={m.sources} />
          ))}
          {loading && <ChatMessage role="assistant" text="Thinking..." />}
        </div>

        {error && <p className="error">{error}</p>}

        <div className="controls-row">
          <label className="rag-toggle">
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
            />
            <span className="slider"></span>
            <span className="toggle-label">Search knowledge base (RAG)</span>
          </label>
        </div>

        <div className="input-row">
          <input
            className="input-box"
            value={input}
            placeholder={
              useRag
                ? "Ask something about your documents..."
                : "Ask anything (direct Gemini)..."
            }
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="send-btn" onClick={handleSend} disabled={loading}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
