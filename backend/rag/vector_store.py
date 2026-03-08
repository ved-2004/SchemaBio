"""
ChromaDB-based persistent vector store for RAG documents.
Three collections: card_resistance, imgt_sequences, alphafold_structures.

ChromaDB is imported lazily so the app can start without it; RAG/Layer 2 will
fail at first use with a clear error if chromadb is not installed.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

CHROMA_PATH = Path(__file__).parent.parent / "data" / "chromadb"

COLLECTIONS = {
    "card": "card_resistance",
    "imgt": "imgt_sequences",
    "alphafold": "alphafold_structures",
}


def _import_chromadb() -> Any:
    """Deferred import so backend can start without chromadb installed."""
    try:
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        return chromadb, DefaultEmbeddingFunction
    except ImportError as e:
        raise ImportError(
            "chromadb is required for RAG (Layer 2). Install with: pip install chromadb"
        ) from e


class VectorStore:
    """ChromaDB persistent vector store with cosine similarity search."""

    def __init__(self, persist_path: Optional[Path] = None):
        chromadb, DefaultEmbeddingFunction = _import_chromadb()
        self._chromadb = chromadb
        self.persist_path = persist_path or CHROMA_PATH
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.persist_path))
        self._embedding_fn = DefaultEmbeddingFunction()
        self._collections: dict[str, Any] = {}

    def _get_collection(self, name: str) -> Any:
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    # ChromaDB hard limit per batch call
    _CHROMA_BATCH_LIMIT = 5000

    def add_documents(self, collection_name: str, documents: list[dict]) -> int:
        """
        Add documents to a collection. Skips already-indexed IDs.
        documents: list of {"id": str, "text": str, "metadata": dict}
        Returns number of new documents added.
        Large document sets are chunked to stay under ChromaDB's batch size limit.
        """
        if not documents:
            return 0

        collection = self._get_collection(collection_name)

        # Dedup check — chunked to avoid batch limit on .get()
        all_ids = [d["id"] for d in documents]
        existing: set[str] = set()
        for i in range(0, len(all_ids), self._CHROMA_BATCH_LIMIT):
            chunk_ids = all_ids[i : i + self._CHROMA_BATCH_LIMIT]
            existing.update(collection.get(ids=chunk_ids)["ids"])

        new = [(d["id"], d["text"], d.get("metadata", {})) for d in documents if d["id"] not in existing]
        if not new:
            return 0

        # Insert in chunks to stay under ChromaDB's max batch size
        added = 0
        for i in range(0, len(new), self._CHROMA_BATCH_LIMIT):
            chunk = new[i : i + self._CHROMA_BATCH_LIMIT]
            chunk_ids, chunk_texts, chunk_metas = zip(*chunk)
            collection.add(
                ids=list(chunk_ids),
                documents=list(chunk_texts),
                metadatas=list(chunk_metas),
            )
            added += len(chunk)

        return added

    def query(
        self,
        collection_name: str,
        query_texts: list[str],
        n_results: int = 5,
    ) -> list[dict]:
        """
        Query collection with one or more query strings.
        Merges and deduplicates results across queries, sorted by relevance.
        Returns list of {"text", "metadata", "distance", "relevance_score"}.
        """
        collection = self._get_collection(collection_name)
        count = collection.count()
        if count == 0:
            return []

        n = min(n_results, count)
        results = collection.query(query_texts=query_texts, n_results=n)

        # Merge results from all queries; keep lowest distance per unique text
        seen: dict[str, dict] = {}
        for qi in range(len(query_texts)):
            docs = results["documents"][qi]
            metas = results["metadatas"][qi]
            dists = results["distances"][qi]
            for doc, meta, dist in zip(docs, metas, dists):
                if doc not in seen or dist < seen[doc]["distance"]:
                    seen[doc] = {"text": doc, "metadata": meta, "distance": dist}

        sorted_docs = sorted(seen.values(), key=lambda x: x["distance"])
        return [
            {
                "text": r["text"],
                "metadata": r["metadata"],
                "distance": r["distance"],
                "relevance_score": round(max(0.0, 1.0 - r["distance"]), 4),
            }
            for r in sorted_docs[:n_results]
        ]

    def collection_count(self, collection_name: str) -> int:
        try:
            return self._get_collection(collection_name).count()
        except Exception:
            return 0

    def clear_collection(self, collection_name: str) -> None:
        try:
            self._client.delete_collection(collection_name)
            self._collections.pop(collection_name, None)
        except Exception:
            pass
