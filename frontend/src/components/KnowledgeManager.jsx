import { useState, useEffect } from "react";
import { getDocuments, uploadDocument, deleteDocument } from "../api";

export default function KnowledgeManager({ isOpen, onClose }) {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      loadDocuments();
    }
  }, [isOpen]);

  async function loadDocuments() {
    try {
      setError("");
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (err) {
      setError("Failed to fetch documents: " + err.message);
    }
  }

  async function handleFileSelection(file) {
    if (!file) return;
    
    // Simple validation
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "txt", "md", "markdown"].includes(ext)) {
      setError("Unsupported format. Please upload .pdf, .txt or .md files.");
      return;
    }

    setUploading(true);
    setError("");
    try {
      await uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      setError(err.message || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  }

  function handleFileChange(e) {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  }

  // Drag-and-drop handlers
  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  }

  async function handleDelete(docId) {
    if (!confirm("Are you sure you want to delete this document from the knowledge base?")) {
      return;
    }
    
    setError("");
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
    } catch (err) {
      setError(err.message || "Failed to delete file");
    }
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  function formatDate(dateStr) {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  }

  return (
    <div className={`knowledge-sidebar ${isOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <h2>Knowledge base</h2>
        <button className="close-btn" onClick={onClose} aria-label="Close sidebar">
          &times;
        </button>
      </div>

      <div className="sidebar-content">
        <p className="sidebar-desc">
          Add files to ground Gemini's responses in your custom documents.
        </p>

        {/* Drag & Drop Upload Zone */}
        <form
          className={`upload-zone ${dragActive ? "drag-active" : ""}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById("file-upload").click()}
        >
          <input
            id="file-upload"
            type="file"
            multiple={false}
            accept=".pdf,.txt,.md,.markdown"
            onChange={handleFileChange}
            style={{ display: "none" }}
          />
          <div className="upload-icon">📁</div>
          <p className="upload-text">
            {uploading ? (
              <span className="spinner-text">Vectorizing & Chunking...</span>
            ) : (
              "Drag & drop PDF, TXT, MD here or click to browse"
            )}
          </p>
        </form>

        {error && <div className="sidebar-error">{error}</div>}

        {/* Document Ingestion List */}
        <div className="document-list-container">
          <h3>Ingested Documents ({documents.length})</h3>
          {documents.length === 0 ? (
            <p className="empty-list">No documents uploaded yet.</p>
          ) : (
            <div className="document-list">
              {documents.map((doc) => (
                <div className="doc-card" key={doc.doc_id}>
                  <div className="doc-info">
                    <span className="doc-icon">📄</span>
                    <div className="doc-details">
                      <p className="doc-name" title={doc.filename}>
                        {doc.filename}
                      </p>
                      <p className="doc-meta">
                        {formatBytes(doc.size_bytes)} &bull; {formatDate(doc.uploaded_at)}
                      </p>
                    </div>
                  </div>
                  <button
                    className="delete-doc-btn"
                    onClick={() => handleDelete(doc.doc_id)}
                    title="Delete document"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
