"""
routers/ingestion.py

SchemaBio ingestion API routes.
- POST /api/upload-and-parse — upload files, run ingestion, return IngestionResponse
- GET  /api/demo-ingestion  — return fully mocked demo IngestionResponse
- POST /api/program-state   — optional: return program state from provided test input
"""

from __future__ import annotations
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Body

from api.schemas.ingestion import IngestionResponse, ProgramState
from api.ingestion.service import run_ingestion
from api.data.demo.demo_ingestion import get_demo_ingestion_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ingestion"])


# Directory for persisting uploaded files (per program) for context
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


def _persist_uploaded_files(program_id: str, paths: list[Path]) -> None:
    """Save uploaded files to uploads/<program_id>/ so they are kept for context."""
    if not program_id or not paths:
        return
    dest_dir = UPLOADS_DIR / program_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    for p in paths:
        if not p.exists():
            continue
        dest = dest_dir / p.name
        try:
            dest.write_bytes(p.read_bytes())
            logger.info("Persisted upload: %s -> %s", p.name, dest)
        except Exception as e:
            logger.warning("Failed to persist %s: %s", p.name, e)


@router.post("/upload-and-parse", response_model=IngestionResponse)
async def upload_and_parse(
    files: list[UploadFile] = File(...),
) -> IngestionResponse:
    """
    Accept uploaded files, run the ingestion pipeline, return IngestionResponse.
    Files are saved to uploads/<program_id>/ for context (Experiment Design / Execution layers).
    Supported: resistance assay CSV, compound screen CSV, VCF, PDF, TXT/MD.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    paths: list[Path] = []
    tmp_dir = Path(tempfile.mkdtemp(prefix="schemabio_ingest_"))
    try:
        for f in files:
            if not f.filename:
                continue
            path = tmp_dir / f.filename
            content = await f.read()
            path.write_bytes(content)
            paths.append(path)
        if not paths:
            raise HTTPException(status_code=400, detail="No valid files to process")
        response = run_ingestion(paths)
        _persist_uploaded_files(response.program_state.program_id, paths)
        return response
    finally:
        for p in paths:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
        try:
            tmp_dir.rmdir()
        except Exception:
            pass


@router.get("/demo-ingestion", response_model=IngestionResponse)
async def demo_ingestion() -> IngestionResponse:
    """Return a fully mocked antibiotic resistance demo IngestionResponse."""
    return get_demo_ingestion_response()


@router.post("/program-state", response_model=ProgramState)
async def program_state_from_input(
    body: Optional[dict] = Body(None),
) -> ProgramState:
    """
    Optional route: return normalized program state from provided test input.
    If body is empty, returns demo program_state only.
    """
    demo = get_demo_ingestion_response()
    if not body:
        return demo.program_state
    # Minimal merge: allow overriding program_id, status
    state = demo.program_state.model_copy(deep=True)
    if "program_id" in body:
        state.program_id = str(body["program_id"])
    if "status" in body:
        state.status = str(body["status"])
    return state
