# SchemaBio Ingestion Layer — Summary

## Purpose

The ingestion layer is the **source of truth** for SchemaBio. It:

- Takes whatever scientific context the user has (files)
- Parses it **deterministically** (no LLM in this layer)
- Normalizes and detects file schemas
- Extracts meaningful biological/drug-discovery entities and signals
- Estimates program/workflow stage
- Flags missing data
- Attaches evidence links to source files
- Outputs **evidence-linked structured context** only (JSON)

## Supported File Types (MVP)

| Input | Parser | What is parsed deterministically |
|-------|--------|----------------------------------|
| **Resistance assay CSV** | `assay_parser` + adapter | strain_id, isolate_id, compound_name, MIC, fold_shift, replicate, assay_type; resistant/sensitive strains; fold-shifts |
| **Compound screen CSV** | `compound_parser` + adapter | compound_name, IC50/z_score, hit flag, target if present; lead compound; vehicle/replicate flags |
| **VCF** | `vcf_parser` + adapter | chrom, pos, ref, alt, gene, impact, clinvar if present; resistance-relevant genes; QRDR hotspots |
| **PDF / notes / target rationale** | `pdf_parser` + adapter | Text extraction (PyMuPDF/pdfminer); title, target references, organism references, drug class, mechanism keywords; optional mocked fallback if extraction fails |

## What Is Parsed vs Inferred

- **Deterministic parsing**: Column detection, numeric extraction, gene/variant annotation from VCF INFO, PDF text and regex for genes/organisms/mechanisms. All of this is rule-based.
- **Inferred**: Stage estimate (heuristics from which files and signals are present). Missing-data flags (from absence of certain data or parser warnings). No LLM is used.

## Stage Estimation Logic

Implemented in `backend/services/stage_estimator.py`. Supported stage names:

- `hit_discovery`
- `resistance_mechanism_characterization`
- `experimental_validation_planning`
- `preclinical_package_gap_analysis`
- `manufacturing_feasibility_review`

**Examples of rules:**

- Variant + resistance assay + compound hit data → `resistance_mechanism_characterization`
- Strong compound screen + target rationale, weak validation → `hit_discovery` or `experimental_validation_planning`
- Manufacturing/ADMET/GMP terms in missing-data flags or signals → `preclinical_package_gap_analysis` or `manufacturing_feasibility_review`

Stage estimate includes `name`, `confidence` (0–1), and `reasoning_basis` (list of short strings) so the logic is interpretable.

## Response Schema (Top Level)

The ingestion API returns exactly:

```json
{
  "program_state": { ... },
  "experiment_design_input": { ... },
  "execution_planning_input": { ... }
}
```

### program_state

- `program_id`, `status`
- `uploaded_files`: list of `UploadedFileDescriptor` (file_id, filename, detected_type, schema_confidence, parse_status, extracted_fields, warnings)
- `entities`: list of `ExtractedEntity` (type, value, source, confidence, metadata)
- `signals`: list of `ExtractedSignal` (kind, value, unit, source, evidence_ref)
- `stage_estimate`: `StageEstimate` (name, confidence, reasoning_basis)
- `missing_data_flags`: list of string codes (e.g. no_admet_data_detected, no_vehicle_control_detected)
- `warnings`: list of free-text warnings from parsers
- `evidence_index`: map file_id → list of refs (entity/signal identifiers)

### experiment_design_input

- `stage`, `stage_confidence`
- `biological_context` (string summary)
- `assay_context` (list of strings)
- `priority_signals`, `missing_experiment_context`
- `evidence_bundle` (literature_refs, quantitative_claims, audit_refs, gap_refs, file_refs)

### execution_planning_input

- `stage`, `stage_confidence`
- `program_summary`
- `development_signals`, `missing_development_inputs`, `readiness_constraints`
- `evidence_bundle`

## How the Frontend Consumes It

- **Ingestion page**: Calls `GET /api/demo-ingestion` (demo) or `POST /api/upload-and-parse` (real upload). Stores `IngestionResponse` in `IngestionContext`. Renders uploaded files, detected types, parse confidence, entities, signals, stage estimate, missing data flags, and short previews of experiment_design_input and execution_planning_input.
- **Dashboard**: Reads `ingestionResponse` from context (or mock). Derives program hero (title, stage, confidence, summary, entities) and recent uploads from `program_state`; uses `experiment_design_input` and `execution_planning_input` for downstream sections.

## API Routes

- `POST /api/upload-and-parse` — form-data `files[]`; returns `IngestionResponse`
- `GET /api/demo-ingestion` — returns fully mocked `IngestionResponse`
- `POST /api/program-state` — optional; returns normalized `ProgramState` from provided test input or demo
- `GET /api/health` — health check

## Key Backend Paths

- **Models**: `backend/models/ingestion.py` (Pydantic contracts)
- **Stage logic**: `backend/services/stage_estimator.py`
- **Orchestration**: `backend/services/ingestion_service.py`
- **Parser adapter**: `backend/services/parser_adapter.py` (maps parsers → entities/signals/descriptors)
- **Parsers**: `backend/parsers/` (vcf_parser, assay_parser, compound_parser, pdf_parser; universal_parser for DrugProgram legacy)
- **Routes**: `backend/routers/ingestion.py`
