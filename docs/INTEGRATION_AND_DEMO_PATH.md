# SchemaBio Full-System Integration & Demo Path

After the GitHub pull that added Layer 2, Layer 3, and RAG, this doc summarizes the integrated flow and the exact demo path for the hackathon.

## Data flow (end-to-end)

```
1. INGESTION (Layer 1)
   User: Ingestion page → "Load demo (API)" or "Upload & parse" or "Load demo (mock)"
   Backend: GET /api/demo-ingestion or POST /api/upload-and-parse
   Returns: IngestionResponse { program_state, experiment_design_input, execution_planning_input }

2. FRONTEND CONTEXT
   setIngestionResponse(data) is called with the ingestion result.
   IngestionContext then:
   - Stores ingestionResponse
   - Calls runExperimentDesign(data.experiment_design_input, data.program_state)
   - Then calls runExecutionPlanning(data.execution_planning_input, l2Result?._layer2_output)

3. LAYER 2 — Experiment Design
   Frontend: POST /api/experiment-design/run
   Body: { experiment_design_input, program_state }
   Backend: RAG ensure_indexed_and_query(program_state) → then Layer 2 pipeline (LLM)
   Returns: { recommendations, hypotheses, bioinfTasks, controlSuggestions, stageConfirmed, keyHypothesis, literatureQueries, pipelineNotes, status, _layer2_output }

4. LAYER 3 — Execution Planning
   Frontend: POST /api/execution-planning/run
   Body: { execution_planning_input, experiment_design_output: _layer2_output }
   Backend: run_layer3(epi, layer2_output) → Drug-to-Market engine + FDA agent
   Returns: { readinessItems, croTypes, grants, evidenceChecklist, manufacturingFlags, fdaPathway, ... }

5. UI
   Dashboard: uses ingestionResponse (program_state, experiment_design_input, execution_planning_input)
   Experiments: uses experimentDesignResponse from context (Layer 2)
   Execution: uses executionPlanningResponse from context (Layer 3)
```

## Routes confirmed

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/demo-ingestion | Return mocked IngestionResponse (no upload) |
| POST | /api/upload-and-parse | Upload files → run ingestion → return IngestionResponse |
| POST | /api/program-state | Optional: return ProgramState (demo or override) |
| POST | /api/experiment-design/run | Layer 2: experiment_design_input + program_state → recommendations, etc. |
| POST | /api/execution-planning/run | Layer 3: execution_planning_input + optional _layer2_output → readiness, CROs, grants, etc. |
| POST | /api/rag/query | RAG query (used internally by Layer 2) |
| POST | /api/rag/index | RAG index (CARD/AlphaFold/IMGT) |
| GET | /api/health | Health check |

## What is real vs mocked

- **Ingestion**: Real when using POST /api/upload-and-parse with real files. Mock when using GET /api/demo-ingestion or frontend "Load demo (mock)" (mock data only in frontend, no backend call for mock).
- **Layer 2**: Real when ANTHROPIC_API_KEY is set and ingestion has run; uses real RAG (CARD/AlphaFold/IMGT) and real LLM. If API key missing or LLM fails, the route returns 500.
- **Layer 3**: Real when called; uses internal engine + FDA agent (openFDA). No API key required for Layer 3.
- **RAG**: Real when collections are populated (first Layer 2 run triggers index). Uses ChromaDB and external fetchers.

## Exact demo path (live)

1. **Start backend** (from repo root):
   ```bash
   pip install -r backend/requirements.txt
   uv run uvicorn backend.main:app --reload --port 8000
   ```
   Or: `python3 -m uvicorn backend.main:app --reload --port 8000` if venv is active.

2. **Start frontend**:
   ```bash
   cd frontend && npm install && npm run dev
   ```
   App at http://localhost:5173; API proxy to http://localhost:8000.

3. **Run the pipeline**:
   - Open **Ingestion**.
   - Click **Load demo (API)** to get demo ingestion from backend, then Layers 2 and 3 run automatically in context.
   - Or click **Load demo (mock)** to use frontend-only mock and still trigger Layer 2 + 3 (they will be called with mock ingestion payload).
   - Or **Upload & parse** with files from `demo_data/burkholderia_flipping_program/` (if present) or any supported CSV/VCF/PDF/TXT.

4. **View results**:
   - **Dashboard**: Program state, stage, entities, signals from ingestion.
   - **Experiment Design**: Layer 2 recommendations, hypotheses, bioinf tasks, controls.
   - **Execution Planning**: Layer 3 readiness, CRO types, grants, evidence checklist, manufacturing flags.

## Requirements

- **Layer 2 (Experiment Design)**: `ANTHROPIC_API_KEY` in env or `.env` for LLM. If missing, POST /api/experiment-design/run will fail (500).
- **Layer 3**: No extra env; openFDA calls are unauthenticated.
- **RAG**: ChromaDB (in-memory/sqlite); CARD/AlphaFold/IMGT fetchers may need network on first index.

## Caveats

- Ingestion is synchronous; large uploads can block the request.
- Layer 2 prompt is loaded from `backend/prompts/experiment_design.txt` at import.
- File-stack / workspace readiness (file_stack, progression_status) from the previous implementation is not in the current GitHub main; ingestion returns the three main blobs only (program_state, experiment_design_input, execution_planning_input).
