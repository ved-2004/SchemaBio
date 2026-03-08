# Experiment Design Layer — Handoff from Ingestion

This document describes exactly what the **future Experiment Design Layer** should consume from the ingestion layer and how to use it. The ingestion layer does **not** implement experiment design; it only produces the structured input below.

---

## Exact Schema: experiment_design_input

The ingestion API returns `experiment_design_input` with this shape (Pydantic / JSON):

| Field | Type | Meaning |
|-------|------|--------|
| `stage` | string | Program stage name (e.g. `resistance_mechanism_characterization`, `hit_discovery`) |
| `stage_confidence` | float | 0–1 confidence in stage |
| `biological_context` | string | Human-readable summary of organisms, targets, variants, lead compound (semicolon-separated or similar) |
| `assay_context` | list[string] | Assay types present (e.g. MIC, compound screen, variant calling) |
| `priority_signals` | list[ExtractedSignal] | Signals the ingestion layer considers high priority (e.g. resistance_fold_shift, compound_hit) |
| `missing_experiment_context` | list[string] | Gaps that affect experiment design (e.g. missing controls, missing strain coverage, missing mechanism data) |
| `evidence_bundle` | EvidenceBundle | literature_refs, quantitative_claims, audit_refs, gap_refs, file_refs |

### ExtractedSignal (for priority_signals)

- `kind`: string (e.g. resistance_fold_shift, compound_hit, lead_ic50_nm, variant_count)
- `value`: string | number | boolean
- `unit`: optional string (e.g. "×", "nM")
- `source`: optional filename
- `evidence_ref`: optional file_id for evidence linking

### EvidenceBundle

- `literature_refs`: list of IDs (e.g. PMIDs)
- `quantitative_claims`: list of `{ type, value, unit?, target? }`
- `audit_refs`, `gap_refs`: list of ref IDs
- `file_refs`: list of ingestion file_id values

---

## How the Experiment Design Layer Should Use Each Field

1. **stage / stage_confidence**  
   Use to tailor recommendations (e.g. hit discovery → more screening/validation; resistance_mechanism_characterization → mechanism experiments, controls).

2. **biological_context**  
   Use as the main text summary of the program for reasoning (organisms, targets, variants, lead compound). Keep citations to `evidence_bundle.file_refs` and `quantitative_claims` where possible.

3. **assay_context**  
   Know what assays are already present; recommend *complementary* assays (e.g. time-kill if only MIC; enzyme assays if only cell-based).

4. **priority_signals**  
   These are the most important quantitative/qualitative findings. Use them to prioritize which experiments to recommend first (e.g. if resistance_fold_shift is high, recommend mechanism experiments).

5. **missing_experiment_context**  
   Direct list of gaps. The Experiment Design Layer should recommend experiments or controls that **fill** these (e.g. “Efflux vs target mutation mechanism” → recommend efflux assay + enzyme inhibition).

6. **evidence_bundle**  
   All recommendations should remain **evidence-linked**: tie each recommendation to a file_ref, quantitative_claim, or audit_ref so users can trace back to source data.

---

## Examples of Outputs the Experiment Design Layer Should Produce

- **Experiment recommendations**: e.g. “Run efflux assay (e.g. CCCP + MIC) to distinguish efflux vs target mutation,” “Run enzyme inhibition (WT vs D87N GyrA) to confirm target engagement.”
- **Controls**: e.g. “Wildtype susceptible strain control (ATCC reference),” “Solvent-only vehicle control for lead compound,” “Positive control antibiotic (e.g. ciprofloxacin).”
- **Hypothesis/target prioritization**: e.g. “Prioritize GyrA D87N mechanism characterization before scaling screening.”
- **Bioinformatics suggestions**: e.g. “Variant annotation enrichment; compare to QRDR database.”

These should be **model-reasoned** (LLM or rules) from the above inputs; ingestion does not generate them.

---

## Deterministic vs Model-Reasoned

- **Deterministic (ingestion)**: stage name, biological_context string, assay_context list, priority_signals, missing_experiment_context list, evidence_bundle. No interpretation of “what experiment to do next.”
- **Model-reasoned (Experiment Design Layer)**: ranked list of next experiments, suggested controls, prioritization of hypotheses/targets/compounds, literature-backed reasoning, bioinformatics analyses. All of these should consume the deterministic handoff and stay evidence-linked via evidence_bundle.

---

## Suggested Output Schema for the Experiment Design Layer

The next layer can return something like:

```json
{
  "recommended_experiments": [
    {
      "title": "string",
      "rationale": "string",
      "priority": "high|medium|low",
      "evidence_refs": ["file_id or claim_id"],
      "controls_included": ["string"],
      "estimated_effort": "string or null"
    }
  ],
  "suggested_controls": [
    { "control": "string", "reason": "string", "evidence_refs": [] }
  ],
  "priority_hypotheses": [
    { "hypothesis": "string", "confidence": "number", "evidence_refs": [] }
  ],
  "bioinformatics_suggestions": ["string"],
  "warnings": ["string"]
}
```

All `evidence_refs` should point into `evidence_bundle` (file_refs, quantitative_claims, audit_refs, gap_refs) so the chain from raw file → ingestion → experiment design remains traceable.
