// Presentational component: renders one message bubble.
// Styling differs by role (user vs assistant).
export default function ChatMessage({ role, text }) {
  return (
    <div className={`message ${role}`}>
      <span className="role-label">{role === "user" ? "You" : "Assistant"}</span>
      <div className="bubble">{text}</div>
    </div>
  );
}
