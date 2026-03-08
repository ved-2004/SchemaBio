# AIDEN — Cursor Navigation Guide

## QUICK START

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env  # add ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173

# 3. Parser-only test (no API key needed)
cd ..
python scripts/run_demo.py --parsers-only

# 4. Full demo test
ANTHROPIC_API_KEY=sk-ant-... python scripts/run_demo.py
```

---

## FILE MAP

```
aiden_v2/
├── backend/
│   ├── main.py                     ← FastAPI + SSE endpoints
│   ├── models/
│   │   └── drug_program.py         ← THE ANCHOR OBJECT (DrugProgram)
│   ├── parsers/
│   │   ├── universal_parser.py     ← Orchestrates all parsers
│   │   ├── vcf_parser.py           ← VCF → gyrA/parC variants
│   │   ├── assay_parser.py         ← MIC CSV → fold-shifts
│   │   ├── compound_parser.py      ← Compound screen → IC50/hits
│   │   └── pdf_parser.py           ← Paper → genes/mechanisms/claims
│   ├── agents/
│   │   ├── orchestrator.py         ← 9-step pipeline, SSE events
│   │   ├── stage_classifier.py     ← T1–T8 stage detection
│   │   ├── assumption_auditor.py   ← Flag missing controls etc
│   │   ├── literature_agent.py     ← PubMed + claim extraction
│   │   ├── contradiction_detector.py ← Your IC50 vs published
│   │   ├── translational_agent.py  ← CRO/CDMO/funding/GMP
│   │   └── action_generator.py     ← Ranked action plan
│   └── prompts/
│       ├── experiment_design.txt   ← System prompt for AI PI
│       └── execution_planning.txt  ← System prompt for execution
│
├── frontend/src/
│   ├── App.jsx                     ← ALL panels (one file)
│   ├── lib/demo_data.js            ← Complete frontend demo data
│   └── hooks/useAIDENStream.js     ← SSE consumer hook
│
├── data/demo/
│   ├── gyra_variants.vcf           ← gyrA D87N + parC S80I
│   ├── gyrase_resistance.csv       ← MIC table, 64× fold-shift
│   └── compound14_screen.csv       ← IC50 screen, Compound-14
│
├── scripts/
│   └── run_demo.py                 ← End-to-end CLI test
│
└── tests/
    └── test_parsers.py             ← Parser unit tests
```

---

## DATA FLOW

```
Files uploaded
     ↓
[Parsers] — ZERO LLM CALLS
  vcf_parser.py     → gyrA D87N, parC S80I → ParsedVariant[]
  assay_parser.py   → 64× fold-shift       → ParsedAssayData
  compound_parser.py→ Compound-14 32nM     → ParsedCompoundScreen
  pdf_parser.py     → genes/mechanisms     → ParsedPDF
     ↓
universal_parser.py → merge into DrugProgram
     ↓
[Agents] — LLM CALLS USE STRUCTURED DrugProgram
  stage_classifier    → T3 resistance_characterization (93%)
  assumption_auditor  → 4 flags (2 HIGH)
  literature_agent    → 4 papers, 6 claims
  contradiction_detector → 27.8× fold diff vs published
  epistemic_gap_mapper→ 0 papers (WHITE SPACE)
  translational_agent → CRO/CDMO/funding/GMP
  action_generator    → 6 ranked actions
     ↓
SSE stream → frontend React state
```

---

## DEMO SCRIPT (90 seconds)

1. **Open** → click "▶ DEMO"
2. **Watch** pipeline progress bar fill: 9 steps, 6 seconds
3. **Point to DrugProgram card** → "This is the anchor object — structured scientific state, not chat"
4. **Assumption Auditor** → "Two HIGH flags caught before we waste lab time: no vehicle control, n=1 replicates"
5. **Contradiction Detector** → "Compound-14 at 32 nM vs 890 nM published — 27.8× fold difference. Bug or breakthrough?"
6. **Epistemic Gap Map** → "Zero papers on GyrA D87N × Compound-14 × E. coli. Genuine white space."
7. **Action Plan** → Rank 1 blocking action: "Characterize resistance mechanism — efflux assay + enzyme inhibition"
8. **Translational panel** → "BARDA CARB-X up to $2M, specific CRO type, GMP readiness at 20%"
9. **Close** → "This is the scientific operating system every resistance lab is missing."

---

## WHERE TO ADD THINGS

### New parser for a file type
→ `backend/parsers/` — add `your_parser.py`
→ Wire into `universal_parser.py` `build_drug_program_from_files()`

### New agent step
→ `backend/agents/` — add `your_agent.py`
→ Add to `orchestrator.py` pipeline
→ Add SSE event type to `useAIDENStream.js`

### New dashboard panel
→ `frontend/src/App.jsx` — add component, wire to state
→ Add demo data to `frontend/src/lib/demo_data.js`

### Change the system prompt
→ `backend/prompts/experiment_design.txt`
→ `backend/prompts/execution_planning.txt`

### Change the demo data
→ `data/demo_program.py` (backend DrugProgram)
→ `frontend/src/lib/demo_data.js` (frontend state)
→ `data/demo/` (raw demo input files)

---

## JUDGING DEFENSE

**"Why not just ChatGPT?"**
"ChatGPT receives unstructured text. AIDEN deterministically parses heterogeneous biology files — VCF, MIC tables, compound screens — normalizes them to a typed DrugProgram object, then runs structured agents over that object. Every output is evidence-linked and reproducible. That's an operating system, not a chatbot."

**"Where does Claude run?"**
"Only after parsers produce a clean DrugProgram. Claude never sees raw files. It sees structured scientific state with typed fields. That's why outputs are specific: 'Compound-14 IC50 32 nM vs 890 nM published' not 'the compound showed interesting activity'."

**"What's the company?"**
"The scientific operating system that runs inside every antibiotic resistance lab. Today: manual decisions across fragmented data. AIDEN: one interface, deterministic ingestion, AI-powered decision support, translational execution planning."
