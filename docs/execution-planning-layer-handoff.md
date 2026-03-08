# Execution / Translational Planning Layer — Handoff from Ingestion

This document describes exactly what the **future Execution / Translational Planning Layer** should consume from the ingestion layer and how to use it. The ingestion layer does **not** implement execution planning; it only produces the structured input below.

---

## Exact Schema: execution_planning_input

The ingestion API returns `execution_planning_input` with this shape (Pydantic / JSON):

| Field | Type | Meaning |
|-------|------|--------|
| `stage` | string | Program stage (e.g. resistance_mechanism_characterization, manufacturing_feasibility_review) |
| `stage_confidence` | float | 0–1 confidence in stage |
| `program_summary` | string | Short narrative summary of program, stage, entities/signals, and reasoning |
| `development_signals` | list[ExtractedSignal] | Signals relevant to development (e.g. synthesis_steps, evidence_completeness_pct, gmp_readiness_pct) |
| `missing_development_inputs` | list[string] | Missing-data flags and gaps (e.g. no_admet_data_detected, no_manufacturability_data_detected) |
| `readiness_constraints` | list[string] | High-level constraints (e.g. “CDMO not ready until ADMET + reproducibility package complete”) |
| `evidence_bundle` | EvidenceBundle | literature_refs, quantitative_claims, audit_refs, gap_refs, file_refs |

### ExtractedSignal (for development_signals)

- `kind`, `value`, `unit`, `source`, `evidence_ref` (same as in experiment_design_input).

### EvidenceBundle

- Same as in experiment_design_input: literature_refs, quantitative_claims, audit_refs, gap_refs, file_refs.

---

## How the Execution Layer Should Use Each Field

1. **stage / stage_confidence**  
   Drives which partner types and funding paths are relevant (e.g. early stage → discovery CROs, grants; later stage → CDMO, GMP readiness).

2. **program_summary**  
   Use as the main context for generating partner recommendations, funding narratives, and readiness assessments. Keep references to evidence_bundle for traceability.

3. **development_signals**  
   Use quantitative signals (e.g. evidence_completeness_pct, gmp_readiness_pct) to assess readiness and to recommend which development steps are next.

4. **missing_development_inputs**  
   Map these to **missing evidence package elements** (e.g. no_admet_data_detected → “ADMET package incomplete”; no_reproducibility_summary_detected → “Independent replication needed”). Use to suggest what must be in place before CRO/CDMO or funding.

5. **readiness_constraints**  
   These are ingestion-level constraints (deterministic). The Execution Layer can expand them with model-reasoned constraints and tie them to specific partner types or funding criteria.

6. **evidence_bundle**  
   All outputs (partner recommendations, funding paths, blockers) should remain **evidence-linked** via file_refs and quantitative_claims so users can trace back to ingested data.

---

## Examples of Outputs the Execution Layer Should Produce

- **Partner recommendations**: e.g. “Engage discovery CRO for MIC/time-kill (in-house capacity limited)”; “CDMO not recommended until GMP readiness > 50%.”
- **Funding paths**: e.g. “BARDA CARB-X fit for AMR discovery — up to $2M”; “SBIR Phase II applicable once lead is declared.”
- **Missing evidence package elements**: e.g. “Resistance mechanism characterized,” “MIC across ≥5 strains including WT,” “Target engagement (enzyme inhibition),” “Mammalian cytotoxicity counter-screen,” “Independent lab replication.”
- **Translational blockers**: e.g. “ADMET package incomplete”; “Reproducibility gap — single lab only.”
- **Early CDMO/GMP readiness signals**: e.g. “Synthesis route present → 25% GMP readiness; no analytical methods yet.”

These should be **model-reasoned** from the above inputs; ingestion only provides the structured handoff.

---

## Deterministic vs Model-Reasoned

- **Deterministic (ingestion)**: stage, program_summary, development_signals, missing_development_inputs, readiness_constraints, evidence_bundle. No recommendation of specific partners or grants.
- **Model-reasoned (Execution Layer)**: partner type recommendations (lab/CRO/CDMO), specific funding opportunities, prioritization of evidence gaps, GMP readiness score and next steps. All should consume the handoff and stay evidence-linked.

---

## Suggested Output Schema for the Execution Layer

The next layer can return something like:

```json
{
  "partner_recommendations": [
    {
      "partner_type": "CRO|CDMO|lab",
      "rationale": "string",
      "readiness_required": "string or null",
      "evidence_refs": []
    }
  ],
  "funding_opportunities": [
    {
      "name": "string",
      "amount": "string",
      "fit_rationale": "string",
      "deadline": "string or null",
      "evidence_refs": []
    }
  ],
  "missing_evidence_package_elements": [
    { "element": "string", "blocking_for": "string", "evidence_refs": [] }
  ],
  "translational_blockers": [
    { "blocker": "string", "severity": "high|medium|low", "evidence_refs": [] }
  ],
  "readiness_assessment": {
    "evidence_completeness_pct": "number or null",
    "gmp_readiness_pct": "number or null",
    "signals": [],
    "next_steps": ["string"]
  }
}
```

All `evidence_refs` should point into `evidence_bundle` so the chain from raw file → ingestion → execution planning remains traceable.
