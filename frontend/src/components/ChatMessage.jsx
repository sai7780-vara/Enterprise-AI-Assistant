// Presentational component: renders one message bubble.
// Styling differs by role (user vs assistant).
// Presentational component: renders one message bubble.
// Styling differs by role (user vs assistant).
export default function ChatMessage({ role, text, sources }) {
  return (
    <div className={`message ${role}`}>
      <span className="role-label">{role === "user" ? "You" : "Assistant"}</span>
      <div className="bubble">
        <div className="message-content">{text}</div>
        {role === "assistant" && sources && sources.length > 0 && (
          <div className="message-sources">
            <span className="sources-label">Sources:</span>
            <div className="sources-list">
              {sources.map((src, idx) => (
                <span key={idx} className="source-badge" title={src}>
                  📄 {src}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
