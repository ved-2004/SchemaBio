# SchemaBio Frontend Replacement — Implementation Plan

## Phase 1 Summary: Repository Understanding

### Current SchemaBio Repo

| Area | Finding |
|------|--------|
| **Frontend** | Single-page React 18 + Vite (JS), no router. One `App.jsx` (~520 lines) with inline styles, Recharts. Demo data in `lib/demo_data.js`. Hook `useAIDENStream.js` for SSE. No shadcn, no Tailwind. |
| **Backend** | FastAPI in `backend/`. `main.py` exposes `/api/health`, `/api/demo`, `POST /api/analyze`, `GET /api/program/{id}`. Models in `backend/models/drug_program.py` (DrugProgram anchor object). Parsers in `backend/parsers/`, agents in `backend/agents/`, prompts in `backend/prompts/`. |
| **Architecture docs** | README.md, CURSOR_GUIDE.md describe AIDEN (rebrand to SchemaBio): Ingestion → Stage/Audit/Lit/Contradiction/Gaps → Translational → Action. Three layers: Ingestion, Experiment Design, Execution. |
| **Product** | AI-driven scientific workflow for antibiotic resistance drug discovery. MVP inputs: resistance CSV, compound screen CSV, VCF, PDF. Outputs: program_state, experiment_design_input, execution_planning_input. |

### Lovable Repo (schemabio-workspace)

| Area | Finding |
|------|--------|
| **Stack** | Vite + React 18 + TypeScript. Shadcn UI (Radix), Tailwind, react-router-dom. Framer Motion, Recharts, TanStack Query. |
| **Pages** | Landing, Dashboard, Ingestion, Experiments, Execution, Literature, Reports, NotFound. Index.tsx exists but unused (blank). |
| **Layout** | AppLayout (SidebarProvider + AppSidebar + TopNav + Outlet), AppSidebar (Workspace / Workflow / Insights / System), CommandMenu. |
| **Components** | 50+ shadcn components in `components/ui/`. SchemaBio-specific: ProgramHeroCard, WorkflowStepper, UploadFileCard, StageBadge, RiskFlagCard, RecommendationCard, ReadinessMeter, ChartCard, DataTableCard, AgentTracePanel, EvidenceCard, LitPaperCard, etc. |
| **Branding** | Already "SchemaBio" and "Drug Discovery OS" in sidebar and landing. |

### Alignment to User-Specified Architecture

- **Ingestion** → page exists; will add typed `program_state`, `experiment_design_input`, `execution_planning_input` and mock wiring.
- **Experiment Design** → Experiments page; keep and optionally label "Experiment Design" in nav.
- **Execution** → Execution page.
- **Literature / Evidence** → Literature page.
- **Reports** → Reports page.
- **Program Dashboard** → Dashboard page.

---

## Phases 2–7 Execution Plan

1. **Replace frontend**: Copy Lovable app (src, public, configs) into `frontend/`, preserve backend. Use TS + path alias `@/`. Configure Vite proxy to `http://localhost:8000` for `/api`.
2. **Align nav/routes**: Ensure all 8 screens present; sidebar labels: Program Dashboard, Ingestion, Experiment Design, Execution, Literature, Reports. Remove or repurpose redundant links (e.g. "Analysis", "Recommendations" duplicate). Keep one "Programs" or "Dashboard" entry.
3. **Ingestion types**: Add `frontend/src/types/ingestion.ts` with `ProgramState`, `ExperimentDesignInput`, `ExecutionPlanningInput`, `IngestionResponse`.
4. **Mock data**: Add `frontend/src/lib/mockIngestionResponse.ts` (one antibiotic resistance demo) and optional `mockProgramState.ts` etc. that match the new types.
5. **Wire ingestion & dashboard**: Ingestion page: after "upload" (or demo), set ingestion response in state/context and render program_state / experiment_design_input / execution_planning_input. Dashboard: consume same mock or context. Add clear `// TODO: replace with POST /api/ingest` (or equivalent) where backend will plug in.
6. **Cleanup**: Remove `Index.tsx` usage if any; remove generic "Welcome to Your Blank App"; trim redundant sidebar items; keep premium shell and all schemabio components.
7. **Deliver**: IMPLEMENTATION_SUMMARY.md with changes, key files, and ingestion API connection points.

---

*Generated before frontend replacement. Execute phases 2–7 next.*
