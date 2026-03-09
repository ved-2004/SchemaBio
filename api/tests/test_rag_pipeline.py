"""
End-to-end RAG pipeline tests: ingestion layer output → RAG query.

Covers:
  1. Full demo program state (gyrA D87N / parC S80I / Compound-14)
  2. Edge: empty program state (no entities, no signals)
  3. Edge: unknown gene not in any database
  4. Edge: organism-only entity (no explicit gene)
  5. Edge: different resistance class (MRSA / mecA)
  6. Edge: signal-only state (no entity block)
  7. Edge: stage estimate drives queries even with sparse entities

Run:
  cd SchemaBio/backend
  python -m pytest tests/test_rag_pipeline.py -v --tb=short
or simply:
  python tests/test_rag_pipeline.py
"""
from __future__ import annotations

import asyncio
import sys
import shutil
import tempfile
from pathlib import Path

# ── Bootstrap path so we can run as a script too ─────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.rag.rag_service import ensure_indexed_and_query, index_for_program_state, query_rag
from api.rag.vector_store import VectorStore, COLLECTIONS
from api.rag.query_builder import build_queries, extract_genes


# ── Shared test fixtures ──────────────────────────────────────────────────────

DEMO_PROGRAM_STATE = {
    "program_id": "DEMO01",
    "status": "ok",
    "entities": [
        {"type": "organism", "value": "E. coli (ATCC 25922 + clinical isolates)", "source": "gyrase_resistance.csv", "confidence": 0.97},
        {"type": "target",   "value": "GyrA",    "source": "gyra_variants.vcf",      "confidence": 0.98},
        {"type": "variant",  "value": "GyrA D87N","source": "gyra_variants.vcf",      "confidence": 0.95},
        {"type": "variant",  "value": "parC S80I","source": "gyra_variants.vcf",      "confidence": 0.93},
        {"type": "compound", "value": "Compound-14","source": "compound14_screen.csv","confidence": 0.96},
        {"type": "assay_type","value": "MIC",    "source": "gyrase_resistance.csv",   "confidence": 0.99},
    ],
    "signals": [
        {"kind": "resistance_fold_shift",       "value": 64,             "unit": "×",   "source": "gyrase_resistance.csv"},
        {"kind": "compound_hit",                "value": "Compound-14",                 "source": "compound14_screen.csv"},
        {"kind": "lead_ic50_nm",                "value": 32,             "unit": "nM",  "source": "compound14_screen.csv"},
        {"kind": "top_hit_count",               "value": 3,                             "source": "compound14_screen.csv"},
        {"kind": "variant_count",               "value": 3,              "unit": "variants","source": "gyra_variants.vcf"},
        {"kind": "resistance_associated_variant","value": "GyrA D87N",                  "source": "gyra_variants.vcf"},
    ],
    "stage_estimate": {
        "name": "resistance_mechanism_characterization",
        "confidence": 0.93,
        "reasoning_basis": ["Variant data + resistance assay + compound hit data present."],
    },
    "missing_data_flags": ["no_vehicle_control_detected", "no_admet_data_detected"],
    "warnings": ["No vehicle/DMSO control in compound screen"],
}

MRSA_PROGRAM_STATE = {
    "program_id": "MRSA01",
    "status": "ok",
    "entities": [
        {"type": "organism", "value": "Staphylococcus aureus MRSA",    "source": "mrsa_assay.csv", "confidence": 0.97},
        {"type": "target",   "value": "mecA",                          "source": "mrsa_variants.vcf","confidence": 0.98},
        {"type": "drug_class","value": "beta-lactam",                  "source": "mrsa_assay.csv", "confidence": 0.95},
        {"type": "assay_type","value": "MIC",                          "source": "mrsa_assay.csv", "confidence": 0.99},
    ],
    "signals": [
        {"kind": "resistance_fold_shift", "value": 512, "unit": "×", "source": "mrsa_assay.csv"},
    ],
    "stage_estimate": {
        "name": "resistance_mechanism_characterization",
        "confidence": 0.88,
        "reasoning_basis": ["mecA present, resistance assay present."],
    },
    "missing_data_flags": [],
    "warnings": [],
}

EMPTY_PROGRAM_STATE = {
    "program_id": "EMPTY01",
    "status": "ok",
    "entities": [],
    "signals": [],
    "stage_estimate": {"name": "", "confidence": 0.0, "reasoning_basis": []},
    "missing_data_flags": [],
    "warnings": [],
}

SIGNAL_ONLY_STATE = {
    "program_id": "SIG01",
    "status": "ok",
    "entities": [],
    "signals": [
        {"kind": "resistance_fold_shift",       "value": 128, "unit": "×"},
        {"kind": "resistance_associated_variant","value": "gyrB D426N"},
        {"kind": "lead_ic50_nm",                "value": 15,  "unit": "nM"},
    ],
    "stage_estimate": {
        "name": "experimental_validation_planning",
        "confidence": 0.70,
        "reasoning_basis": ["Signal data only."],
    },
    "missing_data_flags": [],
    "warnings": [],
}

UNKNOWN_GENE_STATE = {
    "program_id": "UNK01",
    "status": "ok",
    "entities": [
        {"type": "target",  "value": "xylR",  "source": "hypothetical.vcf", "confidence": 0.60},
        {"type": "variant", "value": "xylR G102D","source": "hypothetical.vcf","confidence": 0.55},
    ],
    "signals": [],
    "stage_estimate": {
        "name": "hit_discovery",
        "confidence": 0.55,
        "reasoning_basis": ["Novel target."],
    },
    "missing_data_flags": [],
    "warnings": [],
}

ORGANISM_ONLY_STATE = {
    "program_id": "ORG01",
    "status": "ok",
    "entities": [
        {"type": "organism", "value": "Klebsiella pneumoniae KPC",    "source": "kpc_assay.csv","confidence": 0.97},
        {"type": "drug_class","value": "carbapenem",                  "source": "kpc_assay.csv","confidence": 0.96},
    ],
    "signals": [
        {"kind": "resistance_fold_shift", "value": 256, "unit": "×"},
    ],
    "stage_estimate": {
        "name": "resistance_mechanism_characterization",
        "confidence": 0.85,
        "reasoning_basis": ["KPC carbapenem resistance."],
    },
    "missing_data_flags": [],
    "warnings": [],
}


# ── Assertion helpers ─────────────────────────────────────────────────────────

def _check_bundle(bundle: dict, label: str) -> dict[str, int]:
    """Validate RAGContextBundle structure and return doc counts."""
    assert isinstance(bundle, dict), f"[{label}] bundle not a dict"
    for key in ("query_entities", "card_documents", "alphafold_documents", "imgt_documents", "total_documents", "index_stats"):
        assert key in bundle, f"[{label}] missing key '{key}'"
    assert isinstance(bundle["card_documents"], list),      f"[{label}] card_documents not list"
    assert isinstance(bundle["alphafold_documents"], list), f"[{label}] alphafold_documents not list"
    assert isinstance(bundle["imgt_documents"], list),      f"[{label}] imgt_documents not list"
    assert bundle["total_documents"] == (
        len(bundle["card_documents"]) + len(bundle["alphafold_documents"]) + len(bundle["imgt_documents"])
    ), f"[{label}] total_documents mismatch"
    return {
        "CARD":      len(bundle["card_documents"]),
        "AlphaFold": len(bundle["alphafold_documents"]),
        "IMGT":      len(bundle["imgt_documents"]),
        "total":     bundle["total_documents"],
    }


def _check_doc(doc: dict, label: str):
    """Validate a single RAGDocument dict."""
    for field in ("doc_id", "source_db", "text", "metadata", "relevance_score"):
        assert field in doc, f"[{label}] doc missing field '{field}'"
    assert isinstance(doc["text"], str) and len(doc["text"]) > 10, f"[{label}] doc text too short"
    assert 0.0 <= doc["relevance_score"] <= 1.0, f"[{label}] relevance_score out of range"


# ── Test runner ───────────────────────────────────────────────────────────────

async def run_tests():
    passed = 0
    failed = 0
    results: list[str] = []

    # Use a temporary ChromaDB directory so tests don't pollute production store
    tmp_dir = Path(tempfile.mkdtemp(prefix="rag_test_"))

    def _fresh_store() -> VectorStore:
        """Return a fresh VectorStore backed by a temp dir."""
        return VectorStore(persist_path=tmp_dir / "chroma")

    print("=" * 70)
    print("RAG PIPELINE END-TO-END TESTS (ingestion -> vector store -> query)")
    print("=" * 70)

    # ─────────────────────────────────────────────────────────────────────────
    # UNIT: query builder
    # ─────────────────────────────────────────────────────────────────────────
    label = "TC-01  query_builder — demo state"
    try:
        queries = build_queries(DEMO_PROGRAM_STATE)
        assert isinstance(queries, list) and len(queries) > 0, "no queries generated"
        assert any("gyrA" in q or "gyra" in q.lower() or "D87N" in q for q in queries), \
            f"GyrA D87N not referenced in queries: {queries}"
        assert any("fluoroquinolone" in q.lower() or "resistance" in q.lower() for q in queries), \
            "no resistance/fluoroquinolone term in queries"
        genes = extract_genes(DEMO_PROGRAM_STATE)
        assert "gyra" in genes, f"gyrA not in extracted genes: {genes}"
        results.append(f"  PASS  {label}  (queries={len(queries)}, genes={genes})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-02  query_builder — empty state"
    try:
        queries = build_queries(EMPTY_PROGRAM_STATE)
        assert isinstance(queries, list), "should return list even when empty"
        # empty state may produce 0 entity queries but still stage queries (empty stage → default)
        results.append(f"  PASS  {label}  (queries={len(queries)})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-03  query_builder — signal-only state"
    try:
        queries = build_queries(SIGNAL_ONLY_STATE)
        assert any("fold" in q.lower() or "resistance" in q.lower() or "128" in q for q in queries), \
            f"fold-shift signal not reflected in queries: {queries}"
        results.append(f"  PASS  {label}  (queries={len(queries)})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    # ─────────────────────────────────────────────────────────────────────────
    # INTEGRATION: index + query (using temp vector store)
    # ─────────────────────────────────────────────────────────────────────────

    # Monkey-patch get_vector_store to use our temp store for this test session
    import api.rag.rag_service as rag_svc
    temp_store = _fresh_store()
    rag_svc._store = temp_store

    label = "TC-04  index_for_program_state — demo (gyrA/parC/fluoroquinolone)"
    try:
        counts = await index_for_program_state(DEMO_PROGRAM_STATE, force_refresh=True)
        assert counts.get("CARD", 0) > 0,       f"CARD indexed 0 docs: {counts}"
        assert counts.get("AlphaFold", 0) > 0,   f"AlphaFold indexed 0 docs: {counts}"
        assert counts.get("IMGT", 0) > 0,        f"IMGT indexed 0 docs: {counts}"
        results.append(f"  PASS  {label}  {counts}")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-05  query_rag — demo state (store already indexed)"
    try:
        bundle = await query_rag(DEMO_PROGRAM_STATE, top_k=5)
        counts = _check_bundle(bundle, label)
        assert counts["total"] > 0, "no documents retrieved"
        # Every returned doc must be well-formed
        for doc in bundle["card_documents"] + bundle["alphafold_documents"] + bundle["imgt_documents"]:
            _check_doc(doc, label)
        # At least one CARD doc should mention gyrase/fluoroquinolone
        card_texts = " ".join(d["text"].lower() for d in bundle["card_documents"])
        assert "gyra" in card_texts or "gyrase" in card_texts or "fluoroquinolone" in card_texts, \
            "No gyrase/fluoroquinolone context in CARD results"
        results.append(f"  PASS  {label}  {counts}")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-06  ensure_indexed_and_query — empty program state"
    try:
        # Empty state should return a bundle without crashing (may have 0 docs in AF/IMGT target queries)
        rag_svc._store = _fresh_store()
        bundle = await ensure_indexed_and_query(EMPTY_PROGRAM_STATE, top_k=3)
        _check_bundle(bundle, label)
        results.append(f"  PASS  {label}  (total={bundle['total_documents']})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-07  ensure_indexed_and_query — MRSA / mecA / beta-lactam"
    try:
        rag_svc._store = _fresh_store()
        bundle = await ensure_indexed_and_query(MRSA_PROGRAM_STATE, top_k=5)
        counts = _check_bundle(bundle, label)
        card_texts = " ".join(d["text"].lower() for d in bundle["card_documents"])
        assert "meca" in card_texts or "beta-lactam" in card_texts or "methicillin" in card_texts, \
            f"No mecA/beta-lactam context in CARD results.\ncard_texts[:300]={card_texts[:300]}"
        results.append(f"  PASS  {label}  {counts}")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-08  ensure_indexed_and_query — unknown gene (xylR)"
    try:
        rag_svc._store = _fresh_store()
        bundle = await ensure_indexed_and_query(UNKNOWN_GENE_STATE, top_k=5)
        _check_bundle(bundle, label)
        # AlphaFold won't have xylR — should return 0 AF docs but not crash
        assert bundle["alphafold_documents"] == [] or all(
            d["metadata"]["gene"] != "xylR" for d in bundle["alphafold_documents"]
        ), "AlphaFold returned unexpected entry for unknown gene xylR"
        results.append(f"  PASS  {label}  (AF docs={len(bundle['alphafold_documents'])})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-09  ensure_indexed_and_query — organism-only (KPC / carbapenem)"
    try:
        rag_svc._store = _fresh_store()
        bundle = await ensure_indexed_and_query(ORGANISM_ONLY_STATE, top_k=5)
        counts = _check_bundle(bundle, label)
        card_texts = " ".join(d["text"].lower() for d in bundle["card_documents"])
        assert "carbapenem" in card_texts or "kpc" in card_texts or "beta-lactam" in card_texts, \
            f"No KPC/carbapenem context in CARD results.\ncard_texts[:300]={card_texts[:300]}"
        results.append(f"  PASS  {label}  {counts}")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-10  ensure_indexed_and_query — signal-only state (no entities)"
    try:
        rag_svc._store = _fresh_store()
        bundle = await ensure_indexed_and_query(SIGNAL_ONLY_STATE, top_k=5)
        _check_bundle(bundle, label)
        results.append(f"  PASS  {label}  (total={bundle['total_documents']})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-11  idempotency — double index does not duplicate docs"
    try:
        rag_svc._store = _fresh_store()
        c1 = await index_for_program_state(DEMO_PROGRAM_STATE)
        c2 = await index_for_program_state(DEMO_PROGRAM_STATE)   # second call same state
        # Second index call must add 0 new docs (all already present)
        assert c2.get("CARD", -1) == 0,       f"CARD added docs on re-index: {c2}"
        assert c2.get("AlphaFold", -1) == 0,  f"AlphaFold added docs on re-index: {c2}"
        assert c2.get("IMGT", -1) == 0,       f"IMGT added docs on re-index: {c2}"
        results.append(f"  PASS  {label}  (1st={c1}, 2nd={c2})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-12  force_refresh clears and re-indexes"
    try:
        rag_svc._store = _fresh_store()
        c1 = await index_for_program_state(DEMO_PROGRAM_STATE)
        c2 = await index_for_program_state(DEMO_PROGRAM_STATE, force_refresh=True)
        assert c2.get("CARD", 0) > 0,      f"CARD empty after force_refresh: {c2}"
        assert c2.get("AlphaFold", 0) > 0, f"AlphaFold empty after force_refresh: {c2}"
        results.append(f"  PASS  {label}  (after refresh={c2})")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-13  relevance_score in [0,1] for all returned docs"
    try:
        rag_svc._store = _fresh_store()
        await index_for_program_state(DEMO_PROGRAM_STATE)
        bundle = await query_rag(DEMO_PROGRAM_STATE, top_k=5)
        all_docs = bundle["card_documents"] + bundle["alphafold_documents"] + bundle["imgt_documents"]
        bad = [d for d in all_docs if not (0.0 <= d["relevance_score"] <= 1.0)]
        assert not bad, f"docs with out-of-range relevance_score: {[d['relevance_score'] for d in bad]}"
        scores = sorted([d["relevance_score"] for d in all_docs], reverse=True)
        results.append(f"  PASS  {label}  scores={scores}")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    label = "TC-14  top_k=1 returns at most 1 doc per collection"
    try:
        rag_svc._store = _fresh_store()
        await index_for_program_state(DEMO_PROGRAM_STATE)
        bundle = await query_rag(DEMO_PROGRAM_STATE, top_k=1)
        assert len(bundle["card_documents"])      <= 1, f"card > 1: {len(bundle['card_documents'])}"
        assert len(bundle["alphafold_documents"]) <= 1, f"af > 1: {len(bundle['alphafold_documents'])}"
        assert len(bundle["imgt_documents"])      <= 1, f"imgt > 1: {len(bundle['imgt_documents'])}"
        results.append(f"  PASS  {label}")
        passed += 1
    except Exception as e:
        results.append(f"  FAIL  {label}  — {e}")
        failed += 1

    # ── Teardown ──────────────────────────────────────────────────────────────
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # ── Report ────────────────────────────────────────────────────────────────
    print()
    for r in results:
        print(r)
    print()
    print("=" * 70)
    print(f"  {passed} passed   {failed} failed   {passed + failed} total")
    print("=" * 70)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
