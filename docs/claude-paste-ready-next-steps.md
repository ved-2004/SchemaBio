# SchemaBio — Paste-Ready Context for Claude (Next Steps)

**Use this block as context when asking Claude to design or implement the Experiment Design Layer and the Execution / Translational Planning Layer.**

---

## What SchemaBio Is

SchemaBio is an **AI-driven scientific workflow platform** for **antibiotic resistance drug discovery and translational execution**. The app has three layers:

1. **Ingestion Layer** (implemented) — Source of truth. Parses files deterministically, extracts entities/signals, estimates stage, outputs structured JSON only. No LLM.
2. **Experiment Design Layer** (to build) — Consumes ingestion output; recommends next experiments, controls, hypothesis/target/compound prioritization; literature-backed reasoning; bioinformatics suggestions.
3. **Execution / Translational Planning Layer** (to build) — Consumes ingestion output; recommends partner types (lab/CRO/CDMO); identifies missing evidence package elements; suggests grants/funding paths; shows translational blockers; assesses early CDMO/GMP readiness.

**Rule:** The ingestion layer is the source of truth. Do not change ingestion contracts; the next two layers must consume the exact handoff described below.

---

## What the Ingestion Layer Does Now

- **Supported inputs**: Resistance assay CSV, compound screen CSV, VCF, PDF/notes (text extraction or mocked fallback).
- **Behavior**: Detects file type, parses schema deterministically, extracts entities (organism, target, compound, variant, assay_type, drug_class, pathway) and signals (e.g. resistance_associated_variant, compound_hit, target_signal, assay_pattern, mechanism_hint), estimates program stage (hit_discovery, resistance_mechanism_characterization, experimental_validation_planning, preclinical_package_gap_analysis, manufacturing_feasibility_review), flags missing data, attaches evidence links.
- **Output**: A single JSON response with three top-level objects: `program_state`, `experiment_design_input`, `execution_planning_input`. See `/docs/examples/example_ingestion_response.json` and `/docs/ingestion-layer-summary.md` for full schema.

---

## Exact Outputs of Ingestion (Contracts to Honor)

**program_state** includes: program_id, status, uploaded_files (each with file_id, filename, detected_type, schema_confidence, parse_status, extracted_fields, warnings), entities, signals, stage_estimate (name, confidence, reasoning_basis), missing_data_flags, warnings, evidence_index.

**experiment_design_input** includes: stage, stage_confidence, biological_context, assay_context, priority_signals, missing_experiment_context, evidence_bundle. This is the **clean handoff to the Experiment Design Layer**. See `/docs/experiment-design-layer-handoff.md` for field meanings, usage, and suggested output schema for that layer.

**execution_planning_input** includes: stage, stage_confidence, program_summary, development_signals, missing_development_inputs, readiness_constraints, evidence_bundle. This is the **clean handoff to the Execution Layer**. See `/docs/execution-planning-layer-handoff.md` for field meanings, usage, and suggested output schema for that layer.

---

## What the Next Two Layers Need to Do

- **Experiment Design Layer**: Read `experiment_design_input` from the ingestion response (or from context/store). Use stage, biological_context, assay_context, priority_signals, missing_experiment_context, and evidence_bundle to recommend experiments, suggest controls, prioritize hypotheses/targets/compounds, and suggest bioinformatics analyses. All outputs should remain evidence-linked (reference file_refs, quantitative_claims, etc.). Prefer a typed output schema (see experiment-design-layer-handoff.md).
- **Execution / Translational Planning Layer**: Read `execution_planning_input` from the same source. Use stage, program_summary, development_signals, missing_development_inputs, readiness_constraints, and evidence_bundle to recommend partner types, funding paths, missing evidence package elements, translational blockers, and CDMO/GMP readiness. All outputs should remain evidence-linked. Prefer a typed output schema (see execution-planning-layer-handoff.md).

---

## What UI / Frontend Already Exists

- **Stack**: React 18, Vite, TypeScript, shadcn/Tailwind. Routes: Landing, Dashboard, Ingestion, Experiments, Execution, Literature, Reports.
- **Ingestion page**: Load demo (GET /api/demo-ingestion), upload & parse (POST /api/upload-and-parse). Displays uploaded files, detected types, parse confidence, entities, signals, stage estimate, missing data flags, and short previews of experiment_design_input and execution_planning_input. State is in IngestionContext (IngestionResponse).
- **Dashboard**: Consumes ingestion response from context (or mock). Shows program hero (title, stage, confidence, summary, entities), workflow stepper, next actions, missing controls, readiness meters, risk flags, recent uploads, agent trace, evidence card. Data is derived from program_state, experiment_design_input, execution_planning_input.
- **Experiments page** and **Execution page**: Exist but are not yet wired to real Experiment Design or Execution layer outputs. They are the natural place to render recommendations and handoff-driven UI.

---

## What Backend Is Already Implemented

- **Ingestion API**: FastAPI app in `backend/`. Routes: POST /api/upload-and-parse, GET /api/demo-ingestion, POST /api/program-state, GET /api/health. Models in `backend/models/ingestion.py`. Service in `backend/services/ingestion_service.py`, stage logic in `backend/services/stage_estimator.py`, parser adapter in `backend/services/parser_adapter.py`. Parsers in `backend/parsers/` (vcf, assay, compound, pdf; universal_parser for legacy DrugProgram).
- **Legacy AIDEN routes** (optional): /api/demo, POST /api/analyze (SSE), GET /api/program/{id}. These are separate from the ingestion layer; the frontend uses the ingestion routes and IngestionResponse.

---

## What Claude Should Help Design Next

1. **Experiment Design Layer**:  
   - Input: `experiment_design_input` (and optionally full `program_state`).  
   - Output: Recommended experiments, suggested controls, priority hypotheses, bioinformatics suggestions (typed schema as in experiment-design-layer-handoff.md).  
   - Implementation: Can be a new backend service + route (e.g. POST /api/experiment-design/recommend) that returns the suggested schema, and/or integration into an agent pipeline. Keep evidence_refs in every recommendation.

2. **Execution / Translational Planning Layer**:  
   - Input: `execution_planning_input` (and optionally full `program_state`).  
   - Output: Partner recommendations, funding opportunities, missing evidence package elements, translational blockers, readiness assessment (typed schema as in execution-planning-layer-handoff.md).  
   - Implementation: Can be a new backend service + route (e.g. POST /api/execution-planning/recommend). Keep evidence_refs in every output.

3. **Frontend wiring**:  
   - Experiments page: Call Experiment Design API and display recommended experiments, controls, and hypotheses.  
   - Execution page: Call Execution Planning API and display partner recommendations, funding paths, blockers, readiness.

Use the handoff docs and example JSONs in `/docs` and `/docs/examples` as the single source of truth for contracts.
