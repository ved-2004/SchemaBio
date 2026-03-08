# SchemaBio Frontend Replacement — Summary

## What Changed

1. **Frontend replaced**  
   The previous single-page React (JS) app (`App.jsx`, inline styles, Recharts-only) was replaced by the Lovable-generated frontend: **Vite + React 18 + TypeScript**, **shadcn UI** (Radix), **Tailwind**, **react-router-dom**, and the existing SchemaBio-themed layout and components.

2. **Backend untouched**  
   `backend/` was not modified. FastAPI, parsers, agents, and `DrugProgram` remain the source of truth for the future ingestion/analyze API.

3. **Routing and pages**  
   - **Landing** (`/`) — marketing/landing  
   - **Program Dashboard** (`/dashboard`) — program overview, workflow stepper, actions, risks, readiness, recent uploads, agent trace, evidence card  
   - **Ingestion** (`/ingestion`) — upload zone, uploaded files list, parse preview (entities), ProgramState summary (signals, stage estimate, missing data flags), downstream inputs preview  
   - **Experiment Design** (`/experiments`) — recommendations, hypotheses, bioinformatics, control suggestions  
   - **Execution Planning** (`/execution`) — readiness, CRO types, funding, evidence checklist, manufacturability flags  
   - **Literature & Evidence** (`/literature`) — paper cards, search, evidence graph placeholder  
   - **Reports** (`/reports`) — executive summary, key entities, readiness, next experiments, translational roadmap, blockers  
   - **404** (`*`) — NotFound

4. **Ingestion contracts and mock data**  
   - **Types**: `frontend/src/types/ingestion.ts` defines `ProgramState`, `ExperimentDesignInput`, `ExecutionPlanningInput`, `IngestionResponse`, and supporting types (`UploadedFileInfo`, `ExtractedEntity`, `IngestedSignal`, `StageEstimate`, `EvidenceBundle`).  
   - **Mock**: `frontend/src/lib/mockIngestionResponse.ts` exports `MOCK_INGESTION_RESPONSE` — one antibiotic resistance demo (GyrA D87N, Compound-14, E. coli, 64× fold-shift) matching the three-layer outputs.  
   - **Context**: `frontend/src/contexts/IngestionContext.tsx` holds `IngestionResponse | null` and `setIngestionResponse` so Ingestion and Dashboard share the same state.

5. **Wiring**  
   - **Ingestion page**: "Load demo program (mock)" sets the context to `MOCK_INGESTION_RESPONSE`. The page renders `program_state` (uploaded_files, entities, signals, stage_estimate, missing_data_flags) and a short preview of `experiment_design_input` / `execution_planning_input`. A TODO in the drop zone points to wiring real file upload to the backend.  
   - **Dashboard**: Uses `useIngestion()`; if context is null it falls back to `MOCK_INGESTION_RESPONSE` so the dashboard always shows the demo. Program hero, recent uploads, and evidence card text are derived from the ingestion response. "Upload Data" links to `/ingestion`, "Generate Report" to `/reports`.

6. **Cleanup**  
   - Removed unused `Index.tsx`.  
   - Sidebar simplified: one "Program Dashboard", "Ingestion", "Experiment Design", "Execution Planning", "Literature & Evidence", "Reports", and "Settings".  
   - Removed `lovable-tagger` from the Vite config and package.json.  
   - Vite proxy added: `/api` → `http://localhost:8000` for future backend calls.  
   - Port set to `5173` to match the original frontend.

---

## Files That Matter Most

| Path | Purpose |
|------|--------|
| `frontend/src/types/ingestion.ts` | **Ingestion layer contracts** — keep in sync with backend response. |
| `frontend/src/lib/mockIngestionResponse.ts` | **Demo data** — replace usage with API once backend is ready. |
| `frontend/src/contexts/IngestionContext.tsx` | **Shared ingestion state** — used by Ingestion and Dashboard. |
| `frontend/src/lib/api.ts` | **Placeholder API module** — implement `postIngest(FormData)` here when backend exists. |
| `frontend/src/pages/Ingestion.tsx` | **Ingestion UI** — upload + ProgramState + downstream preview; where to call `postIngest` and `setIngestionResponse`. |
| `frontend/src/pages/Dashboard.tsx` | **Program dashboard** — reads from `useIngestion()` and derives hero, uploads, evidence. |
| `frontend/src/App.tsx` | **Root** — routes + `IngestionProvider`. |
| `frontend/src/components/layout/AppSidebar.tsx` | **Nav** — Program Dashboard, Ingestion, Experiment Design, Execution, Literature, Reports. |
| `frontend/vite.config.ts` | **Dev server** — port 5173, proxy `/api` to backend. |

---

## Where the Ingestion API Should Connect Next

1. **Backend**  
   Implement an ingestion endpoint that:  
   - Accepts uploads (e.g. `vcf_file`, `csv_files[]`, `pdf_file`, `txt_file`).  
   - Runs the existing parsers (and any new ones) to build a structured result.  
   - Returns JSON that matches **`IngestionResponse`**:  
     - `program_state`: `ProgramState`  
     - `experiment_design_input`: `ExperimentDesignInput`  
     - `execution_planning_input`: `ExecutionPlanningInput`  

   You can align the backend response type with `frontend/src/types/ingestion.ts` (or export from backend and reuse in frontend).

2. **Frontend**  
   - In `frontend/src/lib/api.ts`: implement `postIngest(formData)` to `POST /api/ingest` (or `/api/analyze`) and return `IngestionResponse`.  
   - In `frontend/src/pages/Ingestion.tsx`: on real file selection/submit, call `postIngest(formData)`, then `setIngestionResponse(data)`.  
   - Remove or keep "Load demo" as a fallback that sets `MOCK_INGESTION_RESPONSE` when the API is unavailable.

3. **Optional**  
   - Use the same `IngestionResponse` (or a subset) for Experiment Design and Execution pages so they read from context or from a dedicated API that returns `experiment_design_input` / `execution_planning_input` for a given program.

---

## How to Run

```bash
# Backend (unchanged)
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# Frontend (new)
cd frontend && npm install && npm run dev
# → http://localhost:5173
```

Landing at `/`, then "Open Workspace" or "View Demo Program" to go to the dashboard. Open "Ingestion", click "Load demo program (mock)" to populate shared state; Dashboard and Ingestion both reflect the mock ingestion response.
