"""
AIDEN-AMP — FastAPI Main Application
REST API that orchestrates all three layers.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn

from layer1.ingestion import build_program_state
from layer2.experiment_engine import run_experiment_design_engine
from layer3.drug_to_market import run_drug_to_market_engine

app = FastAPI(
    title="AIDEN-AMP",
    description="AI PI for Antibiotic Resistance Drug Discovery — YC AIxBio Hackathon",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "AIDEN-AMP",
        "description": "AI PI for antibiotic resistance drug discovery — from biological evidence to manufacturability",
        "version": "1.0.0",
        "layers": ["ingestion", "experiment_design", "drug_to_market"]
    }


@app.post("/analyze")
async def analyze(
    assay_csv: Optional[UploadFile] = File(None),
    variant_file: Optional[UploadFile] = File(None),
    paper_pdf: Optional[UploadFile] = File(None),
    compound_screen: Optional[UploadFile] = File(None),
    free_text: Optional[str] = Form(None),
    run_layers: Optional[str] = Form("1,2,3"),  # Which layers to run
):
    """
    Main analysis endpoint.
    Accepts any combination of: assay CSV, variant file, paper PDF, compound screen, free text.
    Runs specified layers and returns full ProgramState as JSON.
    """
    try:
        layers = [int(x.strip()) for x in run_layers.split(",")]

        # Read file contents
        assay_csv_str = None
        if assay_csv:
            content = await assay_csv.read()
            assay_csv_str = content.decode("utf-8", errors="replace")

        variant_str = None
        if variant_file:
            content = await variant_file.read()
            variant_str = content.decode("utf-8", errors="replace")

        pdf_bytes = None
        if paper_pdf:
            pdf_bytes = await paper_pdf.read()

        compound_screen_str = None
        if compound_screen:
            content = await compound_screen.read()
            compound_screen_str = content.decode("utf-8", errors="replace")

        # Layer 1: Ingestion
        state = await build_program_state(
            assay_csv=assay_csv_str,
            variant_file=variant_str,
            pdf_bytes=pdf_bytes,
            free_text=free_text,
            compound_screen_csv=compound_screen_str,
        )

        # Layer 2: Experiment Design
        if 2 in layers:
            state = await run_experiment_design_engine(state)

        # Layer 3: Drug-to-Market
        if 3 in layers:
            state = await run_drug_to_market_engine(state)

        return JSONResponse(content=state.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/text")
async def analyze_text(body: dict):
    """
    Lightweight text-only endpoint for quick demos.
    Body: {"text": "...", "organism": "...", "genes": [...], "compounds": [...]}
    """
    try:
        free_text = body.get("text", "")
        organism_hint = body.get("organism", "")
        gene_hints = body.get("genes", [])
        compound_hints = body.get("compounds", [])

        combined_text = f"{free_text} {organism_hint} {' '.join(gene_hints)} {' '.join(compound_hints)}"

        state = await build_program_state(free_text=combined_text)
        state = await run_experiment_design_engine(state)
        state = await run_drug_to_market_engine(state)

        return JSONResponse(content=state.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/demo")
async def run_demo():
    """
    Runs the canonical demo: KPC-producing Klebsiella pneumoniae.
    Demonstrates the full pipeline without file uploads.
    """
    demo_csv = """compound,organism,MIC (µg/mL),method
meropenem,Klebsiella pneumoniae,64,broth microdilution
ceftazidime,Klebsiella pneumoniae,128,broth microdilution
colistin,Klebsiella pneumoniae,1,broth microdilution
ceftazidime-avibactam,Klebsiella pneumoniae,2,broth microdilution
meropenem,Klebsiella pneumoniae ATCC 25922,0.125,broth microdilution
"""

    demo_variant = """gene\taccession\tmechanism\tdrug_class
blaKPC-2\tARO:3000745\tcarbapenemase\tCarbapenem
blaTEM-1\tARO:3000059\tbeta-lactamase\tbeta-lactam
"""

    demo_text = (
        "This Klebsiella pneumoniae clinical isolate exhibits carbapenem resistance "
        "mediated by blaKPC-2 on a conjugative IncF plasmid. "
        "Ceftazidime-avibactam retains activity (MIC 2 µg/mL). "
        "Target: characterize resistance mechanism and design validation experiments "
        "for ceftazidime-avibactam combination therapy."
    )

    state = await build_program_state(
        assay_csv=demo_csv,
        variant_file=demo_variant,
        free_text=demo_text
    )
    state = await run_experiment_design_engine(state)
    state = await run_drug_to_market_engine(state)

    return JSONResponse(content=state.to_dict())


@app.get("/health")
async def health():
    return {"status": "ok", "layers": ["layer1", "layer2", "layer3"]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
