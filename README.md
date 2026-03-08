# AIDEN-AMP
## AI PI for Antibiotic Resistance Drug Discovery
### YC AIxBio Hackathon

> An AI PI that takes antibiotic resistance programs from biological evidence  
> to experimental plan to manufacturability readiness — in one pipeline.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  LAYER 1 — Ingestion + Scientific State Builder  │
│  CSV · VCF · PDF · Text → ProgramState JSON      │
│  Deterministic parsing. Zero hallucination.      │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  LAYER 2 — Experiment Design Engine (AI PI Core) │
│  CARD API · PubChem API · protocols.io API       │
│  → Ranked experiments with verified protocols    │
│  → Compound analysis + hypothesis card           │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  LAYER 3 — Drug-to-Market Execution Engine       │
│  → Funding routing (CARB-X, NIH, BARDA)         │
│  → CRO/lab partner type recommendation          │
│  → CDMO/GMP readiness score (0-100)             │
│  → FDA pathway (QIDP, Fast Track, LPAD)         │
│  → IND-enabling study gap checklist             │
└─────────────────────────────────────────────────┘
```

## External APIs Used
| API | Purpose | Auth |
|-----|---------|------|
| CARD (mcmaster.ca) | Resistance gene annotation + mechanism | None |
| PubChem PUG REST | Compound properties (MW, logP, HBD/HBA) | None |
| protocols.io v3 | Verified experimental protocols | None (public) |

---

## Quick Start

### Backend (Python 3.10+)

```bash
cd backend
pip install -r requirements.txt
python main.py
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend (React)

```bash
cd frontend
npm install
npm start
# Dashboard at http://localhost:3000
```

### Demo endpoint (no files needed)
```bash
curl -X POST http://localhost:8000/analyze/demo | python -m json.tool
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Full analysis with file uploads |
| POST | `/analyze/text` | Text-only quick analysis |
| POST | `/analyze/demo` | Demo: KPC Klebsiella pneumoniae |
| GET  | `/health` | System health check |
| GET  | `/docs` | FastAPI Swagger UI |

---

## Demo Input (included in /data/sample/)
- `kpc_kpn_assay.csv` — MIC data for carbapenem-resistant K. pneumoniae ST258
- `kpc_kpn_variants.tsv` — Resistance gene annotation (blaKPC-2, blaTEM-1, etc.)

---

## Sample Output Structure (ProgramState)
```json
{
  "stage": "resistance_mechanism_characterization",
  "organism": "Klebsiella pneumoniae",
  "evidence_strength": "strong",
  "resistance_genes": [
    { "gene_name": "blaKPC-2", "mechanism": "carbapenemase (class A β-lactamase)", "drug_class": "Carbapenem" }
  ],
  "compounds": [
    { "name": "ceftazidime-avibactam", "drug_likeness_score": 0.82, "molecular_weight": 546.58 }
  ],
  "mic_data": [...],
  "experiment_recommendations": [
    {
      "rank": 1, "priority": "critical",
      "experiment_type": "Multiplex PCR — Carbapenemase Gene Detection",
      "protocol": { "title": "...", "doi": "10.17504/protocols.io.q26g7pw3kgwz", "url": "https://www.protocols.io/..." },
      "missing_controls": [...],
      "bioinformatics_steps": [...]
    }
  ],
  "funding_targets": [
    { "program_name": "CARB-X Explorer Award", "fit_score": 0.80, "award_size": "Up to $2M" }
  ],
  "translational_readiness": {
    "cdmo_readiness_score": 23,
    "qidp_eligible": true,
    "fda_pathway": "Pre-IND consultation recommended",
    "scale_up_blockers": [...]
  }
}
```

---

## Project Files

```
aiden-amp/
├── backend/
│   ├── main.py                     ← FastAPI app + endpoints
│   ├── requirements.txt
│   ├── models/
│   │   └── program_state.py        ← ProgramState + all data types
│   ├── agents/
│   │   ├── card_agent.py           ← CARD API + resistance gene annotation
│   │   ├── pubchem_agent.py        ← PubChem property retrieval
│   │   └── protocols_agent.py      ← protocols.io verified protocols
│   ├── layer1/
│   │   └── ingestion.py            ← CSV/VCF/PDF parser + state builder
│   ├── layer2/
│   │   └── experiment_engine.py    ← AI PI experiment design core
│   └── layer3/
│       └── drug_to_market.py       ← FDA/CDMO/funding execution engine
├── frontend/
│   └── src/
│       └── App.jsx                 ← React dashboard
└── data/sample/
    ├── kpc_kpn_assay.csv
    └── kpc_kpn_variants.tsv
```

---

## One-Liner for Judges

> "We built a three-layer AI PI that ingests resistance assay data, variant files, and papers, 
> queries CARD, PubChem, and protocols.io live, detects where a drug program is in the workflow, 
> and returns grounded experiment plans, funding targets, and FDA/CDMO readiness scores — 
> deterministically, in one run."

---

## Team
YC AIxBio Hackathon — Tracks: AI Scientist · AI Drug Discovery · Bio-data Infrastructure · Agents · Scientific Visualization