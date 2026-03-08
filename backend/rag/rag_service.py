"""
RAG Service — main orchestration layer.

Flow:
  1. Layer 1 (ingestion) produces IngestionResponse.program_state
  2. rag_service.ensure_indexed_and_query(program_state) is called by Layers 2 & 3
  3. Service checks vector store; indexes from CARD/AlphaFold/IMGT if empty
  4. Builds semantic queries from entities/signals/stage
  5. Retrieves top-k documents per source collection
  6. Returns RAGContextBundle dict consumed by experiment_design and execution_planning

Public API:
  ensure_indexed_and_query(program_state, top_k)  ← main entry point
  index_for_program_state(program_state, force)   ← explicit re-index
  query_rag(program_state, top_k)                 ← query only (no auto-index)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .vector_store import VectorStore, COLLECTIONS
from .query_builder import build_queries, extract_genes, extract_drug_classes
from .fetchers.card_fetcher import fetch_card_documents
from .fetchers.alphafold_fetcher import fetch_alphafold_documents
from .fetchers.imgt_fetcher import fetch_imgt_documents

logger = logging.getLogger(__name__)

# ── Module-level singleton vector store ──────────────────────────────────────
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


# ── Indexing ──────────────────────────────────────────────────────────────────

async def index_for_program_state(
    program_state: dict[str, Any],
    force_refresh: bool = False,
) -> dict[str, int]:
    """
    Fetch documents from CARD, AlphaFold, and IMGT for the given program_state
    and add them to the vector store.

    Args:
        program_state: dict matching IngestionResponse.program_state schema.
        force_refresh: if True, clears all collections before re-indexing.

    Returns:
        {"CARD": n, "AlphaFold": n, "IMGT": n} — new documents added per source.
    """
    store = get_vector_store()

    if force_refresh:
        for coll in COLLECTIONS.values():
            store.clear_collection(coll)
        logger.info("Vector store cleared for forced refresh.")

    genes = extract_genes(program_state)
    drug_classes = extract_drug_classes(program_state)
    logger.info("Indexing RAG — genes=%s drug_classes=%s", genes, drug_classes)

    # Fetch all three sources concurrently
    results = await asyncio.gather(
        fetch_card_documents(target_genes=genes, drug_classes=drug_classes),
        fetch_alphafold_documents(target_genes=genes),
        fetch_imgt_documents(target_genes=genes),
        return_exceptions=True,
    )

    card_docs, af_docs, imgt_docs = results
    counts: dict[str, int] = {}

    if isinstance(card_docs, list):
        counts["CARD"] = store.add_documents(COLLECTIONS["card"], card_docs)
        logger.info("CARD: %d new documents indexed.", counts["CARD"])
    else:
        logger.error("CARD fetch error: %s", card_docs)
        counts["CARD"] = 0

    if isinstance(af_docs, list):
        counts["AlphaFold"] = store.add_documents(COLLECTIONS["alphafold"], af_docs)
        logger.info("AlphaFold: %d new documents indexed.", counts["AlphaFold"])
    else:
        logger.error("AlphaFold fetch error: %s", af_docs)
        counts["AlphaFold"] = 0

    if isinstance(imgt_docs, list):
        counts["IMGT"] = store.add_documents(COLLECTIONS["imgt"], imgt_docs)
        logger.info("IMGT: %d new documents indexed.", counts["IMGT"])
    else:
        logger.error("IMGT fetch error: %s", imgt_docs)
        counts["IMGT"] = 0

    return counts


# ── Querying ──────────────────────────────────────────────────────────────────

def _retrieve_from(store: VectorStore, key: str, source_name: str, queries: list[str], top_k: int) -> list[dict]:
    """Query one collection and format results as RAGDocument-compatible dicts."""
    coll_name = COLLECTIONS[key]
    if store.collection_count(coll_name) == 0:
        return []

    raw = store.query(coll_name, query_texts=queries, n_results=top_k)
    docs = []
    for r in raw:
        meta = r["metadata"]
        docs.append(
            {
                "doc_id": f"{source_name}_{meta.get('gene', meta.get('doc_type', 'doc'))}",
                "source_db": source_name,
                "text": r["text"],
                "metadata": meta,
                "relevance_score": r["relevance_score"],
                "source_url": meta.get("source_url", ""),
            }
        )
    return docs


async def query_rag(
    program_state: dict[str, Any],
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Query the RAG vector store for context relevant to the given program_state.
    Does NOT auto-index — call index_for_program_state first if needed.

    Returns a RAGContextBundle dict:
    {
      "query_entities": [...],
      "card_documents": [...],
      "alphafold_documents": [...],
      "imgt_documents": [...],
      "total_documents": int,
      "index_stats": {"CARD": n, "AlphaFold": n, "IMGT": n},
    }
    """
    store = get_vector_store()
    queries = build_queries(program_state)
    if not queries:
        queries = ["antibiotic resistance mechanism drug discovery AMR gyrase"]

    # Use top 5 queries for retrieval to balance recall vs noise
    search_queries = queries[:5]

    card_docs = _retrieve_from(store, "card", "CARD", search_queries, top_k)
    af_docs = _retrieve_from(store, "alphafold", "AlphaFold", search_queries, top_k)
    imgt_docs = _retrieve_from(store, "imgt", "IMGT", search_queries, top_k)

    return {
        "query_entities": [e.get("value", "") for e in program_state.get("entities", [])],
        "queries_used": search_queries,
        "card_documents": card_docs,
        "alphafold_documents": af_docs,
        "imgt_documents": imgt_docs,
        "total_documents": len(card_docs) + len(af_docs) + len(imgt_docs),
        "index_stats": {
            "CARD": store.collection_count(COLLECTIONS["card"]),
            "AlphaFold": store.collection_count(COLLECTIONS["alphafold"]),
            "IMGT": store.collection_count(COLLECTIONS["imgt"]),
        },
    }


# ── Combined convenience entry point ─────────────────────────────────────────

async def ensure_indexed_and_query(
    program_state: dict[str, Any],
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Main entry point for Layers 2 and 3.

    Ensures the vector store is populated for the current program context,
    then returns the RAGContextBundle.

    Auto-indexes on first call (when collections are empty); subsequent calls
    only query the existing index.
    """
    store = get_vector_store()
    is_empty = all(
        store.collection_count(coll) == 0 for coll in COLLECTIONS.values()
    )
    if is_empty:
        logger.info("Vector store empty — triggering initial index from CARD/AlphaFold/IMGT.")
        await index_for_program_state(program_state)

    return await query_rag(program_state, top_k=top_k)
