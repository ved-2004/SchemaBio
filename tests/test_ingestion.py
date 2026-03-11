"""
tests/test_ingestion.py

Tests for the SchemaBio ingestion layer: service + API.
No API key required. Uses data/demo/ files when present.

Run from repo root:
  pytest tests/test_ingestion.py -v
"""

import pytest
from pathlib import Path

DEMO_DIR = Path(__file__).parent.parent / "data" / "demo"


# ─── Ingestion service (run_ingestion) ─────────────────────────────────────────

class TestIngestionService:
    """Test run_ingestion() with demo paths."""

    def test_run_ingestion_returns_ingestion_response(self):
        from api.services.ingestion_service import run_ingestion
        paths = list(DEMO_DIR.glob("*.csv"))[:1]  # at least one file
        if not paths:
            pytest.skip("No demo CSV in data/demo/")
        response = run_ingestion(paths)
        assert response is not None
        assert hasattr(response, "program_state")
        assert hasattr(response, "experiment_design_input")
        assert hasattr(response, "execution_planning_input")

    def test_program_state_has_required_fields(self):
        from api.services.ingestion_service import run_ingestion
        paths = list(DEMO_DIR.glob("*.csv"))[:1]
        if not paths:
            pytest.skip("No demo CSV in data/demo/")
        response = run_ingestion(paths)
        ps = response.program_state
        assert ps.program_id
        assert isinstance(ps.uploaded_files, list)
        assert isinstance(ps.entities, list)
        assert isinstance(ps.signals, list)
        assert isinstance(ps.missing_data_flags, list)
        assert "evidence_index" in ps.model_dump()

    def test_stage_estimate_present_with_demo_data(self):
        from api.services.ingestion_service import run_ingestion
        paths = [p for p in DEMO_DIR.iterdir() if p.suffix in (".csv", ".vcf")][:3]
        if not paths:
            pytest.skip("No demo files in data/demo/")
        response = run_ingestion(paths)
        assert response.program_state.stage_estimate is not None
        se = response.program_state.stage_estimate
        assert se.name
        assert 0 <= se.confidence <= 1
        assert isinstance(se.reasoning_basis, list)


# ─── API (FastAPI TestClient) ──────────────────────────────────────────────────

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


class TestIngestionAPI:
    """Test ingestion endpoints with TestClient."""

    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"

    def test_demo_ingestion_returns_200_and_shape(self, client):
        r = client.get("/api/demo-ingestion")
        assert r.status_code == 200
        data = r.json()
        assert "program_state" in data
        assert "experiment_design_input" in data
        assert "execution_planning_input" in data
        assert data["program_state"].get("program_id") == "DEMO01"
        assert len(data["program_state"].get("uploaded_files", [])) >= 1

    def test_upload_and_parse_with_demo_files(self, client):
        csv_path = DEMO_DIR / "gyrase_resistance.csv"
        if not csv_path.exists():
            pytest.skip("data/demo/gyrase_resistance.csv not found")
        with open(csv_path, "rb") as f:
            r = client.post(
                "/api/upload-and-parse",
                files=[("files", ("gyrase_resistance.csv", f.read(), "text/csv"))],
            )
        assert r.status_code == 200
        data = r.json()
        assert "program_state" in data
        pid = data["program_state"].get("program_id")
        assert pid and len(pid) >= 1
        assert len(data["program_state"].get("uploaded_files", [])) >= 1
        assert len(data["program_state"].get("entities", [])) >= 0
        # Files should be persisted under backend/uploads/<program_id>/
        uploads_dir = Path(__file__).resolve().parent.parent / "backend" / "uploads" / pid
        if uploads_dir.exists():
            assert (uploads_dir / "gyrase_resistance.csv").exists()
