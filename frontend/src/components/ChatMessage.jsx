import { useState } from "react";

// Presentational component: renders one message bubble.
// Styling differs by role (user vs assistant).
export default function ChatMessage({ role, text, sources, confidence }) {
  const [expandedSourceIdx, setExpandedSourceIdx] = useState(null);

  const toggleExpand = (idx) => {
    setExpandedSourceIdx(expandedSourceIdx === idx ? null : idx);
  };

  return (
    <div className={`message ${role}`}>
      <span className="role-label">{role === "user" ? "You" : "Assistant"}</span>
      <div className="bubble">
        {role === "assistant" && confidence !== undefined && confidence > 0 && (
          <div className="message-confidence-badge">
            🎯 Retrieval Confidence: <span className="confidence-value">{confidence}%</span>
          </div>
        )}
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
