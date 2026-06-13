"""Local Vector Store service using FAISS-cpu and a pickle-based metadata storage.

Features:
- Completely self-contained and local.
- Cosine similarity search using FAISS IndexFlatIP (Inner Product) with normalized vectors.
- Supports adding, listing, and deleting documents.
- Automatic serialization of embeddings and texts to disk.
"""

import os
import pickle
from datetime import datetime
from typing import Dict, List, Tuple

import faiss
import numpy as np

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class LocalVectorStore:
    def __init__(self) -> None:
        self.kb_dir = settings.KNOWLEDGE_BASE_DIR
        os.makedirs(self.kb_dir, exist_ok=True)
        self.store_path = os.path.join(self.kb_dir, "knowledge_store.pkl")

        # Core data structure:
        # {
        #   "documents": {
        #       "doc_id": {
        #           "filename": str,
        #           "size_bytes": int,
        #           "uploaded_at": datetime,
        #           "chunks": [{"text": str, "vector": List[float]}]
        #       }
        #   }
        # }
        self.documents: Dict[str, Dict] = {"documents": {}}
        self.faiss_index = None
        self.chunk_metadata_map: List[Dict] = []
        self.dimension = 3072  # gemini-embedding-001 output dimension

        self.load()

    def load(self) -> None:
        """Load document store from disk and rebuild FAISS index."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "rb") as f:
                    self.documents = pickle.load(f)
                logger.info("Loaded document store with %d documents", len(self.documents.get("documents", {})))
            except Exception as e:
                logger.exception("Failed to load vector store pickle, starting empty: %s", e)
                self.documents = {"documents": {}}
        else:
            self.documents = {"documents": {}}

        self._rebuild_index()

    def save(self) -> None:
        """Serialize document store containing texts and embeddings to disk."""
        try:
            with open(self.store_path, "wb") as f:
                pickle.dump(self.documents, f)
            logger.info("Saved vector store to %s", self.store_path)
        except Exception as e:
            logger.exception("Failed to save vector store pickle: %s", e)

    def _rebuild_index(self) -> None:
        """Reconstruct the in-memory FAISS index and mapping list from the document store."""
        logger.info("Rebuilding FAISS index...")
        self.faiss_index = faiss.IndexFlatIP(self.dimension)
        self.chunk_metadata_map = []

        docs = self.documents.get("documents", {})
        all_vectors = []

        for doc_id, doc_meta in docs.items():
            filename = doc_meta["filename"]
            uploaded_at = doc_meta.get("uploaded_at", datetime.now())
            uploaded_at_str = uploaded_at.isoformat() if isinstance(uploaded_at, datetime) else str(uploaded_at)

            for idx, chunk in enumerate(doc_meta["chunks"]):
                text = chunk["text"]
                vector = chunk["vector"]

                # Track context metadata corresponding to index IDs
                meta = chunk.get("metadata", {})
                self.chunk_metadata_map.append({
                    "doc_id": doc_id,
                    "filename": filename,
                    "text": text,
                    "page_number": meta.get("page_number", 1),
                    "chunk_id": meta.get("chunk_id", f"{doc_id}_p1_c{idx}"),
                    "upload_timestamp": meta.get("upload_timestamp", uploaded_at_str)
                })
                all_vectors.append(vector)

        if all_vectors:
            vectors_np = np.array(all_vectors, dtype=np.float32)
            # Normalize vectors for Cosine Similarity (FlatIP + normalized = Cosine Similarity)
            faiss.normalize_L2(vectors_np)
            self.faiss_index.add(vectors_np)
            logger.info("FAISS index rebuilt with %d chunks", len(all_vectors))
        else:
            logger.info("FAISS index is empty (no documents loaded)")

    def add_document(self, doc_id: str, filename: str, size_bytes: int, chunks: List[str], embeddings: List[List[float]], metadatas: List[Dict]) -> None:
        """Ingest a new document, add its embeddings to FAISS, and save to disk."""
        if len(chunks) != len(embeddings) or len(chunks) != len(metadatas):
            raise ValueError("Mismatched counts between chunks, embeddings, and metadatas")

        doc_data = {
            "filename": filename,
            "size_bytes": size_bytes,
            "uploaded_at": datetime.now(),
            "chunks": [
                {
                    "text": chunks[i],
                    "vector": embeddings[i],
                    "metadata": metadatas[i]
                } for i in range(len(chunks))
            ]
        }

        self.documents["documents"][doc_id] = doc_data
        self.save()
        self._rebuild_index()

    def delete_document(self, doc_id: str) -> bool:
        """Delete document from store, rebuild FAISS index, and save to disk."""
        if doc_id in self.documents.get("documents", {}):
            del self.documents["documents"][doc_id]
            self.save()
            self._rebuild_index()
            return True
        return False

    def list_documents(self) -> List[Dict]:
        """Return high-level metadata for all ingested documents."""
        docs = self.documents.get("documents", {})
        result = []
        for doc_id, doc in docs.items():
            result.append({
                "doc_id": doc_id,
                "filename": doc["filename"],
                "size_bytes": doc["size_bytes"],
                "uploaded_at": doc.get("uploaded_at", datetime.now()),
                "chunk_count": len(doc["chunks"])
            })
        return result

    def search(self, query_embedding: List[float], top_k: int = 4) -> List[Tuple[Dict, float]]:
        """Semantic search in FAISS. Returns List of (metadata_dict, score) tuples."""
        if not self.chunk_metadata_map or self.faiss_index is None or self.faiss_index.ntotal == 0:
            return []

        # Vector preparation
        query_np = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_np)

        # Cap top_k to total index size
        k = min(top_k, self.faiss_index.ntotal)

        # Search index
        scores, indices = self.faiss_index.search(query_np, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.chunk_metadata_map):
                results.append((self.chunk_metadata_map[idx], float(score)))

        return results


# Single shared instance created on import
vector_store = LocalVectorStore()
