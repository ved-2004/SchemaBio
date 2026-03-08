# How to Test the Ingestion Layer

Three ways: **API (manual)**, **frontend (manual)**, and **pytest (automated)**.

---

## 1. API (curl / browser)

### Start the backend

From the **repo root** (so `backend` is a package and relative imports work):

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/api/health  

### Test demo (no files)

```bash
curl -s http://localhost:8000/api/demo-ingestion | python3 -m json.tool | head -80
```

You should see `program_state`, `experiment_design_input`, and `execution_planning_input` with `program_id`, `uploaded_files`, `entities`, `signals`, `stage_estimate`, etc.

### Test upload-and-parse (real files)

Use the demo data in `data/demo/`:

```bash
cd /path/to/SchemaBio
curl -s -X POST http://localhost:8000/api/upload-and-parse \
  -F "files=@data/demo/gyrase_resistance.csv" \
  -F "files=@data/demo/compound14_screen.csv" \
  -F "files=@data/demo/gyra_variants.vcf" \
  | python3 -m json.tool | head -100
```

Check:

- `program_state.program_id` is a short ID (e.g. `A1B2C3D4`).
- `program_state.uploaded_files` has one entry per file with `detected_type`, `schema_confidence`, `parse_status`.
- `program_state.entities` includes organism, target, compound, variant, assay_type.
- `program_state.signals` includes e.g. `resistance_fold_shift`, `compound_hit`.
- `program_state.stage_estimate.name` is e.g. `resistance_mechanism_characterization`.
- Files are persisted under `backend/uploads/<program_id>/`.

### Test health

```bash
curl -s http://localhost:8000/api/health
```

---

## 2. Frontend (manual)

1. Start backend (port 8000) and frontend (port 5173):

   ```bash
   # Terminal 1 (from repo root)
   uvicorn backend.main:app --reload --port 8000

   # Terminal 2
   cd frontend && npm run dev
   ```

2. Open http://localhost:5173 → **Ingestion**.
3. **Load demo (API)** — uses `GET /api/demo-ingestion`; dashboard and ingestion should show program state, stage, entities, signals.
4. **Upload & parse** — choose one or more files (e.g. from `data/demo/`). Response should appear and **Program Dashboard** should reflect the new program.

---

## 3. Pytest (automated)

### Parser tests (no API, no server)

Uses demo files under `data/demo/`. No API key needed.

```bash
cd /path/to/SchemaBio
python3 -m pytest tests/test_parsers.py -v
```

Covers VCF, assay CSV, compound CSV, and PDF parsers.

### Ingestion service + API tests

From repo root:

```bash
python3 -m pytest tests/test_ingestion.py -v
```

This runs:

- `run_ingestion()` on demo paths → checks `IngestionResponse` shape and that `program_state` has entities/signals/stage_estimate.
- `GET /api/demo-ingestion` → 200 and valid JSON.
- `POST /api/upload-and-parse` with demo files → 200, valid `program_state.program_id`, and files under `backend/uploads/<program_id>/` (if uploads dir is used).

---

## Quick checklist

| Check | How |
|-------|-----|
| Demo returns valid JSON | `curl http://localhost:8000/api/demo-ingestion` |
| Upload returns program_id + entities/signals | `curl -X POST ... -F "files=@data/demo/gyrase_resistance.csv"` |
| Stage is non-empty | `program_state.stage_estimate.name` |
| Files persisted | `ls backend/uploads/<program_id>/` after upload |
| Frontend demo loads | Ingestion → Load demo (API) → Dashboard shows data |
| Parsers unit tests pass | `pytest tests/test_parsers.py tests/test_ingestion.py -v` |
