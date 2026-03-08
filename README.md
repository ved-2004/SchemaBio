# AIDEN — AI Drug Program Navigator
### Autonomous Investigator for Data-to-Experiment Navigation

> **Bio × AI Hackathon 2026 · Built for Cursor**

---

## What AIDEN Does

AIDEN is an AI principal investigator that takes **any evidence you have today**
and tells you **exactly what to do next** to move your drug program forward.

It is not a chatbot. It is not a database. It is a **decision orchestration layer**.

```
Upload whatever you have → AIDEN detects stage → Audits assumptions →
Pulls literature → Detects contradictions → Maps knowledge gaps →
Generates ranked evidence-linked actions → Shows manufacturing feasibility
```

The drug is the anchor object. The AI reasons around it.

---

## The Five Pillars

```
1. INGEST         Any file type: VCF, resistance CSV, compound screen CSV, PDF, notes
2. CLASSIFY       Detects program stage (T1 Target ID → T8 CDMO Evaluation)  
3. AUDIT          Catches methodological errors BEFORE action plan
4. REASON         Evidence-linked ranked next actions (experiment → regulatory → manufacturing)
5. TRANSLATE      GMP readiness, CDMO suitability, funding paths, CRO recommendations
```

---

## Tech Stack

### Backend
- **FastAPI** — SSE streaming API, file upload endpoints
- **Anthropic Claude Sonnet 4** — stage classification, contradiction detection, action generation
- **cyvcf2 + pandas + PyMuPDF** — deterministic parsers (LLM never sees raw files)
- **PubMed E-utilities** — live literature retrieval with demo cache fallback
- **ChEMBL REST API** — scaffold artifact detection, ADMET flags
- **Semantic Scholar** — citation count queries for epistemic gap map

### Frontend
- **React 18 + Vite** — SSE consumer with live streaming UI
- **Recharts** — volcano plot, gap visualization, evidence completeness
- **Tailwind CSS** — styling

### Integration (Biomni-compatible)
- **cyvcf2** — VCF parsing (Biomni tool: pysam compatible)
- **biopython** — sequence utilities
- **rdkit** — SMILES validation, Lipinski calculation
- **openbabel** — structure format conversion
- **pymed** — PubMed query wrapper

---

## Full Repository Structure

```
aiden/
├── README.md
├── CURSOR_GUIDE.md              ← Start here when opening in Cursor
├── .env.example
├── backend/
│   ├── main.py                  ← FastAPI app, all endpoints
│   ├── requirements.txt
│   ├── models/
│   │   ├── drug_program.py      ← THE anchor object (DrugProgram)
│   │   └── context_bundle.py   ← File parse results
│   ├── parsers/
│   │   ├── universal_parser.py  ← Detects file type, routes to correct parser
│   │   ├── vcf_parser.py        ← cyvcf2 VCF → ParsedVariant[]
│   │   ├── csv_parser.py        ← pandas schema inference → ParsedCompound[]
│   │   ├── resistance_parser.py ← MIC/resistance CSV → ResistanceProfile
│   │   └── pdf_parser.py        ← PyMuPDF → ParsedPDF
│   ├── agents/
│   │   ├── orchestrator.py      ← 9-stage pipeline FSM, SSE streaming
│   │   ├── stage_classifier.py  ← T1–T8 taxonomy, heuristic + LLM
│   │   ├── assumption_auditor.py← 6 heuristic checks + LLM context pass
│   │   ├── literature_agent.py  ← PubMed retrieval + claim extraction
│   │   ├── contradiction_detector.py ← IC50/MIC vs literature cross-ref
│   │   ├── epistemic_gap_mapper.py   ← Knowledge frontier mapping
│   │   ├── translational_agent.py    ← GMP/CDMO/regulatory analysis
│   │   └── action_generator.py      ← Ranked evidence-linked actions
│   └── tools/
│       ├── pubmed_tool.py       ← E-utilities queries + cache
│       ├── chembl_tool.py       ← Scaffold/ADMET queries
│       └── semantic_scholar.py  ← Citation count queries
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx              ← Root, routing
│       ├── hooks/
│       │   └── useAIDENStream.js← SSE consumer hook
│       ├── lib/
│       │   └── demo_data.js     ← Frontend demo data (no backend needed)
│       └── components/
│           ├── FileIngestion.jsx      ← Upload zones for all file types
│           ├── DrugProgramCard.jsx    ← The anchor object display
│           ├── PhaseProgress.jsx      ← 9-step pipeline trace
│           ├── StageBadge.jsx         ← T1–T8 with confidence
│           ├── AssumptionAuditor.jsx  ← Severity-tagged flags
│           ├── ContradictionPanel.jsx ← IC50/MIC side-by-side comparison
│           ├── EpistemicGapMap.jsx    ← Knowledge frontier visualization
│           ├── ActionPlan.jsx         ← Ranked actions with evidence chips
│           ├── TranslationalPanel.jsx ← GMP/CDMO/funding guidance
│           ├── VolcanoPlot.jsx        ← Compound scatter with labels
│           ├── LiteraturePanel.jsx    ← Paper cards with claim highlights
│           └── CitationDrawer.jsx     ← Slide-in detail panel
├── data/
│   └── demo/
│       ├── gyrase_resistance.csv      ← Antibiotic demo: MIC across strains
│       ├── compound14_screen.csv      ← Compound screen results
│       ├── gyra_variants.vcf          ← gyrA D87N + other mutations
│       └── cached_literature.json     ← Pre-fetched literature
├── tests/
│   ├── test_parsers.py
│   ├── test_agents.py
│   └── test_demo_flow.py
├── docs/
│   ├── STAGE_TAXONOMY.md             ← Full T1–T8 stage descriptions
│   ├── BIOMNI_INTEGRATION.md         ← How to wire Biomni tools
│   └── DEMO_SCRIPT.md               ← 90-second demo beats
└── scripts/
    ├── run_demo.py                   ← Run full pipeline on demo data
    └── test_api.sh                   ← curl commands for all endpoints
```

---

## Quickstart

```bash
# Backend
cd backend
cp ../.env.example ../.env
# Fill in ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...       # Required
PUBMED_API_KEY=...                 # Optional (higher rate limits)
SEMANTIC_SCHOLAR_KEY=...           # Optional
CHEMBL_BASE_URL=https://www.ebi.ac.uk/chembl/api/data
DEMO_MODE=false                    # true = always use cached data
```

---

## API Endpoints

```
POST /api/analyze          Upload files, stream SSE pipeline
GET  /api/demo             Run antibiotic resistance demo, stream SSE
GET  /api/health           Health check
GET  /api/program/{id}     Retrieve completed DrugProgram by ID
POST /api/program/{id}/update  Update program with new data
```

---

## The Decision Layer Framing

> Drug discovery is not just finding molecules.
> It is navigating a sequence of scientific, experimental, regulatory,
> and manufacturing decisions.
>
> AIDEN is the decision layer.
>
> Given the data you have today — what should you do next
> to turn this into a real drug?
