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
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Body

from api.schemas.ingestion import IngestionResponse, ProgramState
from api.ingestion.service import run_ingestion
from api.data.demo.demo_ingestion import get_demo_ingestion_response
from api.models.user import User
from api.models.upload import UserUpload
from api.routers.auth import get_optional_user
import api.services.storage as storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ingestion"])


# Local fallback directory (used when Supabase is not configured)
_LOCAL_UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


def _persist_local(program_id: str, path: Path) -> None:
    """Fallback: save a file to the local uploads directory."""
    dest_dir = _LOCAL_UPLOADS_DIR / program_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    try:
        dest.write_bytes(path.read_bytes())
        logger.debug("Local fallback persist: %s", dest)
    except Exception as exc:
        logger.warning("Local persist failed for %s: %s", path.name, exc)


async def _store_uploaded_files(
    program_id: str,
    paths: list[Path],
    file_sizes: dict[str, int],
    user: Optional[User],
) -> None:
    """
    Upload each file to Supabase Storage and save metadata to the DB.
    Falls back to local disk if Supabase is not configured.
    """
    if not storage.is_configured():
        for p in paths:
            _persist_local(program_id, p)
        return

    user_id = user.id if user else "anonymous"
    upload_id = program_id  # reuse program_id as the upload session identifier
    expires_at = storage.make_expires_at()
    now = datetime.now(timezone.utc)

    for path in paths:
        if not path.exists():
            continue
        content = path.read_bytes()
        bucket_path = storage.upload_file(user_id, upload_id, path.name, content)
        if bucket_path is None:
            _persist_local(program_id, path)
            continue

        upload = UserUpload(
            upload_id=f"{upload_id}_{path.stem}",
            user_id=user_id,
            filename=path.name,
            file_size_bytes=file_sizes.get(path.name, len(content)),
            bucket_path=bucket_path,
            program_id=program_id,
            uploaded_at=now,
            expires_at=expires_at,
        )
        storage.save_upload_metadata(upload)


@router.post("/upload-and-parse", response_model=IngestionResponse)
async def upload_and_parse(
    files: list[UploadFile] = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
) -> IngestionResponse:
    """
    Accept uploaded files, run the ingestion pipeline, return IngestionResponse.
    Files are saved to uploads/<program_id>/ for context (Experiment Design / Execution layers).
    Supported: resistance assay CSV, compound screen CSV, VCF, PDF, TXT/MD.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    paths: list[Path] = []
    file_sizes: dict[str, int] = {}
    tmp_dir = Path(tempfile.mkdtemp(prefix="schemabio_ingest_"))
    try:
        for f in files:
            if not f.filename:
                continue
            path = tmp_dir / f.filename
            content = await f.read()
            path.write_bytes(content)
            file_sizes[f.filename] = len(content)
            paths.append(path)
        if not paths:
            raise HTTPException(status_code=400, detail="No valid files to process")
        response = run_ingestion(paths)
        await _store_uploaded_files(
            response.program_state.program_id, paths, file_sizes, current_user
        )
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
