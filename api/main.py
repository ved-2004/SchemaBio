"""
backend/main.py

AIDEN FastAPI application.

Endpoints:
  POST /api/analyze     — Upload files, stream SSE pipeline events
  GET  /api/demo        — Run antibiotic resistance demo, stream SSE
  GET  /api/health      — Health check + version
  GET  /api/program/{id}— Retrieve completed DrugProgram by ID
  
SSE Event Types (consumed by frontend useAIDENStream hook):
  phase | drug_program | stage | audit_flags | literature |
  contradictions | epistemic_gaps | translational | actions |
  key_finding | trace | complete | error
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()  # reads ANTHROPIC_API_KEY (and any other vars) from .env

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Start the daily cleanup scheduler on startup; stop it on shutdown."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from api.routers.uploads import cleanup_expired

        scheduler = AsyncIOScheduler()
        scheduler.add_job(cleanup_expired, "interval", hours=24, id="cleanup_expired_uploads")
        scheduler.start()
        logger.info("APScheduler started — expired-upload cleanup runs every 24 h.")
        yield
        scheduler.shutdown(wait=False)
    except ImportError:
        logger.warning("apscheduler not installed — skipping scheduled cleanup.")
        yield


app = FastAPI(
    title="SchemaBio — AI Drug Discovery OS",
    description="AI-driven scientific workflow platform for antibiotic resistance drug discovery and translational execution.",
    version="1.0.0",
    lifespan=_lifespan,
)

# Auth — Google OAuth2 + JWT
from api.routers import auth as auth_router
app.include_router(auth_router.router)

# Uploads — cloud storage metadata + TTL management
from api.routers import uploads as uploads_router
app.include_router(uploads_router.router)

# SchemaBio ingestion layer (source of truth for program state)
from api.routers import ingestion as ingestion_router
app.include_router(ingestion_router.router)

# RAG layer — CARD / AlphaFold / IMGT retrieval for Layers 2 & 3
from api.routers import rag as rag_router
app.include_router(rag_router.router)

# Layer 2 — Experiment Design (LLM reasoning)
from api.routers import experiment_design as experiment_design_router
app.include_router(experiment_design_router.router)

# Layer 3 — Execution / Translational Planning
from api.routers import execution_planning as execution_planning_router
app.include_router(execution_planning_router.router)

_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:4173",
    # Render / production — set FRONTEND_URL env var on the backend service
    *(
        [os.environ["FRONTEND_URL"]]
        if os.environ.get("FRONTEND_URL")
        else []
    ),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory program store (production: Redis or PostgreSQL)
_program_store: dict[str, dict] = {}


# ─── SSE Wrapper ─────────────────────────────────────────────────────────────

async def _sse_generator(gen):
    """Wrap async generator as Server-Sent Events."""
    async for event in gen:
        event_name = event.get("event", "message")
        data = json.dumps(event.get("data", {}), default=str)
        yield f"event: {event_name}\ndata: {data}\n\n"


def _sse_response(gen) -> StreamingResponse:
    return StreamingResponse(
        _sse_generator(gen),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "api_key_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "demo_available": True,
    }


@app.get("/api/demo")
async def run_demo():
    """
    Run full pipeline on the antibiotic resistance demo dataset.
    Streams SSE events in real-time.
    Demo always works — no API key required for demo data.
    """
    from api.legacy.agents.orchestrator import run_pipeline

    async def pipeline_with_store():
        async for event in run_pipeline(use_demo=True):
            if event.get("event") == "complete":
                prog = event.get("data", {})
                pid = prog.get("program_id")
                if pid:
                    _program_store[pid] = prog
            yield event

    return _sse_response(pipeline_with_store())


@app.post("/api/analyze")
async def analyze(
    vcf_file:  Optional[UploadFile] = File(None),
    csv_files: Optional[list[UploadFile]] = File(None),
    pdf_file:  Optional[UploadFile] = File(None),
    txt_file:  Optional[UploadFile] = File(None),
):
    """
    Upload any combination of biological files and run the AIDEN pipeline.
    All files optional — any subset works.

    Supported formats:
      vcf_file  — VCF/BCF genomics file (variants, resistance mutations)
      csv_files — Multiple CSVs: compound screen, resistance MIC, ADMET
      pdf_file  — Scientific paper or methods PDF
      txt_file  — Target rationale or notes text file

    Falls back to demo data if no files uploaded.
    """
    from api.legacy.agents.orchestrator import run_pipeline

    tmp_dir = Path(tempfile.mkdtemp(prefix="aiden_"))
    vcf_path = csv_paths = pdf_path = txt_paths = None

    try:
        if vcf_file and vcf_file.filename:
            vcf_path = tmp_dir / vcf_file.filename
            vcf_path.write_bytes(await vcf_file.read())

        if csv_files:
            csv_paths = []
            for f in csv_files:
                if f and f.filename:
                    p = tmp_dir / f.filename
                    p.write_bytes(await f.read())
                    csv_paths.append(p)

        if pdf_file and pdf_file.filename:
            pdf_path = tmp_dir / pdf_file.filename
            pdf_path.write_bytes(await pdf_file.read())

        if txt_file and txt_file.filename:
            txt_path = tmp_dir / txt_file.filename
            txt_path.write_bytes(await txt_file.read())
            txt_paths = [txt_path]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File upload failed: {e}")

    use_demo = not any([vcf_path, csv_paths, pdf_path, txt_paths])

    async def pipeline_with_store():
        async for event in run_pipeline(
            vcf_path=vcf_path,
            csv_paths=csv_paths,
            pdf_path=pdf_path,
            text_paths=txt_paths,
            use_demo=use_demo,
        ):
            if event.get("event") == "complete":
                prog = event.get("data", {})
                pid = prog.get("program_id")
                if pid:
                    _program_store[pid] = prog
            yield event

    return _sse_response(pipeline_with_store())


@app.get("/api/program/{program_id}")
async def get_program(program_id: str):
    """Retrieve a completed DrugProgram by its ID."""
    prog = _program_store.get(program_id.upper())
    if not prog:
        raise HTTPException(status_code=404, detail=f"Program {program_id} not found")
    return prog


@app.post("/api/program/{program_id}/update")
async def update_program(program_id: str, new_data: dict):
    """
    Update an existing program with new data (e.g. new assay results).
    Re-runs the analysis pipeline with merged data.
    """
    existing = _program_store.get(program_id.upper())
    if not existing:
        raise HTTPException(status_code=404, detail=f"Program {program_id} not found")
    # TODO: merge new_data into existing program and re-run affected agents
    return {"status": "update queued", "program_id": program_id}
