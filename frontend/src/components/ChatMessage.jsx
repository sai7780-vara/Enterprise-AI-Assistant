import { useState } from "react";

const getAgentClass = (name) => {
  if (!name) return "";
  const lowerName = name.toLowerCase();
  if (lowerName.includes("hr")) return "hr-agent";
  if (lowerName.includes("finance")) return "finance-agent";
  if (lowerName.includes("it")) return "it-agent";
  if (lowerName.includes("rag")) return "rag-agent";
  return "";
};

const getAgentEmoji = (name) => {
  if (!name) return "👤";
  const lowerName = name.toLowerCase();
  if (lowerName.includes("hr")) return "👔";
  if (lowerName.includes("finance")) return "💰";
  if (lowerName.includes("it")) return "💻";
  if (lowerName.includes("rag")) return "🔍";
  return "👤";
};

// Presentational component: renders one message bubble.
// Styling differs by role (user vs assistant).
export default function ChatMessage({ role, text, sources, confidence, agentName }) {
  const [expandedSourceIdx, setExpandedSourceIdx] = useState(null);

  const toggleExpand = (idx) => {
    setExpandedSourceIdx(expandedSourceIdx === idx ? null : idx);
  };

  return (
    <div className={`message ${role}`}>
      <span className="role-label">{role === "user" ? "You" : "Assistant"}</span>
      <div className="bubble">
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
          {role === "assistant" && agentName && (
            <div className={`message-agent-badge ${getAgentClass(agentName)}`}>
              {getAgentEmoji(agentName)} Handled by: <span className="agent-value">{agentName}</span>
            </div>
          )}
          {role === "assistant" && confidence !== undefined && confidence > 0 && (
            <div className="message-confidence-badge">
              🎯 Retrieval Confidence: <span className="confidence-value">{confidence}%</span>
            </div>
          )}
        </div>

        <div className="message-content">{text}</div>
        {role === "assistant" && sources && sources.length > 0 && (
          <div className="message-sources">
            <span className="sources-label">Sources & Citations:</span>
            <div className="sources-list">
              {sources.map((src, idx) => {
                const isExpanded = expandedSourceIdx === idx;
                return (
                  <div key={idx} className={`source-citation-card ${isExpanded ? "expanded" : ""}`}>
                    <div className="source-citation-header" onClick={() => toggleExpand(idx)}>
                      <div className="source-citation-title">
                        📄 {src.document_name} <span className="source-page">Page {src.page_number}</span>
                      </div>
                      <div className="source-citation-meta">
                        <span className="source-score">Match: {Math.round(src.similarity_score * 100)}%</span>
                        <span className="expand-icon">{isExpanded ? "▲" : "▼"}</span>
                      </div>
                    </div>
                    {isExpanded && (
                      <div className="source-citation-body">
                        <p className="source-chunk-id">Chunk ID: <code>{src.chunk_id}</code></p>
                        <div className="source-text-box">
                          <p className="source-text">{src.text}</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
