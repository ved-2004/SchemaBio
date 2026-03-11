#!/usr/bin/env python3
"""
scripts/run_demo.py

Run the full AIDEN pipeline on demo data.
Tests every component: parsers → stage classifier → auditor → literature → actions.

Usage:
  cd aiden_v2
  python scripts/run_demo.py

  # With API key for full LLM pipeline:
  ANTHROPIC_API_KEY=sk-ant-... python scripts/run_demo.py

  # Parser-only (no API key needed):
  python scripts/run_demo.py --parsers-only
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DEMO_DIR  = Path(__file__).parent.parent / "data" / "demo"
GREEN     = "\033[92m"
YELLOW    = "\033[93m"
RED       = "\033[91m"
BLUE      = "\033[94m"
BOLD      = "\033[1m"
RESET     = "\033[0m"
DIM       = "\033[2m"

def ok(msg):  print(f"{GREEN}✓{RESET} {msg}")
def warn(msg): print(f"{YELLOW}⚠{RESET}  {msg}")
def err(msg):  print(f"{RED}✗{RESET} {msg}")
def head(msg): print(f"\n{BOLD}{BLUE}{'─'*60}{RESET}\n{BOLD}{msg}{RESET}")
def dim(msg):  print(f"{DIM}{msg}{RESET}")


async def run_full_pipeline():
    print(f"\n{BOLD}{'═'*60}")
    print("  AIDEN — AI Drug Program Navigator")
    print("  Demo: Antibiotic Resistance · GyrA · Compound-14 · E. coli")
    print(f"{'═'*60}{RESET}\n")

    has_api = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not has_api:
        warn("ANTHROPIC_API_KEY not set — LLM steps will use fallbacks")
    else:
        ok("API key found — full pipeline will run")

    # ── STEP 1: Parsers ───────────────────────────────────────────────
    head("STEP 1 — Deterministic Parsing (no LLM)")

    from backend.parsers.vcf_parser import parse_vcf
    from backend.parsers.assay_parser import parse_resistance_assay
    from backend.parsers.compound_parser import parse_compound_screen
    from backend.parsers.universal_parser import build_drug_program_from_files

    vcf_path  = DEMO_DIR / "gyra_variants.vcf"
    res_path  = DEMO_DIR / "gyrase_resistance.csv"
    cpd_path  = DEMO_DIR / "compound14_screen.csv"

    # VCF
    t = time.time()
    variants = parse_vcf(vcf_path)
    ok(f"VCF: {len(variants)} variants in {time.time()-t:.2f}s")
    qrdr = [v for v in variants if v.is_qrdr_hotspot]
    for v in qrdr[:3]:
        dim(f"  QRDR hotspot: {v.gene} {v.aa_change} (CADD {v.cadd_score})")

    # Resistance assay
    t = time.time()
    assay = parse_resistance_assay(res_path)
    ok(f"Assay: {assay.raw_summary} in {time.time()-t:.2f}s")
    dim(f"  Resistant: {assay.resistant_strains}")
    dim(f"  Max fold-shift: {assay.max_fold_shift}×")

    # Compound screen
    t = time.time()
    screen = parse_compound_screen(cpd_path)
    ok(f"Screen: {screen.raw_summary} in {time.time()-t:.2f}s")
    if screen.lead_compound:
        dim(f"  Lead: {screen.lead_compound.name} IC50={screen.lead_compound.ic50_nm} nM")

    # ── STEP 2: Build DrugProgram ─────────────────────────────────────
    head("STEP 2 — Build DrugProgram Object")
    t = time.time()
    program = build_drug_program_from_files(
        vcf_path=vcf_path,
        csv_paths=[res_path, cpd_path],
    )
    ok(f"DrugProgram built in {time.time()-t:.2f}s")
    dim(f"  Target:   {program.target.gene} / {program.target.organism}")
    dim(f"  Compound: {program.compound.name} (IC50 {program.compound.ic50_nm} nM)")
    dim(f"  Resistance mutations: {program.resistance.resistance_mutations}")
    dim(f"  Evidence completeness: {program.completeness_pct}%")

    # ── STEP 3: Stage Classifier ──────────────────────────────────────
    head("STEP 3 — Stage Classification")
    from backend.agents.stage_classifier import classify_program_stage
    t = time.time()
    stage = classify_program_stage(program)
    ok(f"Stage: {program.stage_label} ({round(program.stage_confidence*100)}%) in {time.time()-t:.2f}s")
    dim(f"  Rationale: {program.stage_rationale[:100]}")

    # ── STEP 4: Assumption Auditor ────────────────────────────────────
    head("STEP 4 — Assumption Auditor")
    from backend.agents.assumption_auditor import run_assumption_auditor
    t = time.time()
    flags = run_assumption_auditor(program)
    ok(f"{len(flags)} flags in {time.time()-t:.2f}s")
    for f in flags:
        sev_color = RED if f.severity=="high" else YELLOW if f.severity=="medium" else ""
        print(f"  {sev_color}[{f.severity.upper()}]{RESET} {f.title}")

    # ── STEP 5: Literature ────────────────────────────────────────────
    head("STEP 5 — Literature Retrieval")
    from backend.agents.literature_agent import retrieve_literature
    t = time.time()
    await retrieve_literature(program)
    ok(f"{len(program.literature)} papers in {time.time()-t:.2f}s")
    for p in program.literature[:3]:
        dim(f"  PMID:{p.pmid} — {p.title[:60]}...")

    # ── STEP 6: Contradiction Detector ───────────────────────────────
    head("STEP 6 — Contradiction Detection")
    from backend.agents.contradiction_detector import run_contradiction_detector
    t = time.time()
    run_contradiction_detector(program)
    if program.contradictions:
        c = program.contradictions[0]
        print(f"  {YELLOW}⚡ CONTRADICTION:{RESET} {c.compound}")
        dim(f"  Your value: {c.your_value} {c.your_unit}")
        dim(f"  Published:  {c.lit_median} {c.your_unit}")
        dim(f"  Fold diff:  {c.fold_difference}×")
    else:
        ok("No significant contradictions detected")

    # ── STEP 7: Epistemic Gap Map ─────────────────────────────────────
    head("STEP 7 — Epistemic Gap Map")
    from backend.agents.contradiction_detector import _load_demo_gaps
    t = time.time()
    _load_demo_gaps(program)
    ok(f"{len(program.epistemic_gaps)} gaps in {time.time()-t:.2f}s")
    white = [g for g in program.epistemic_gaps if g.classification=="white_space"]
    if white:
        print(f"  {RED}🗺 WHITE SPACE:{RESET} {white[0].query}")

    # ── STEP 8: Translational Agent ───────────────────────────────────
    head("STEP 8 — Translational Feasibility")
    from backend.agents.translational_agent import run_translational_agent
    t = time.time()
    run_translational_agent(program)
    ok(f"Translational analysis in {time.time()-t:.2f}s")
    dim(f"  CDMO readiness: {program.manufacturing.cdmo_readiness}")
    dim(f"  Synthesis: {program.manufacturing.synthesis_tractability}")
    dim(f"  Blocking gaps: {program.evidence.blocking_gaps[:2]}")

    # ── STEP 9: Action Generator ──────────────────────────────────────
    head("STEP 9 — Action Plan")
    from backend.agents.action_generator import generate_actions
    t = time.time()
    generate_actions(program)
    ok(f"{len(program.ranked_actions)} ranked actions in {time.time()-t:.2f}s")
    for a in program.ranked_actions[:3]:
        urgency_color = RED if a.urgency=="blocking" else YELLOW if a.urgency=="high" else ""
        print(f"  {urgency_color}[{a.urgency.upper()}]{RESET} Rank {a.rank}: {a.action}")

    # ── Final Summary ─────────────────────────────────────────────────
    head("FINAL PROGRAM STATE")
    print(f"  Program:     {program.program_name or 'Demo Program'}")
    print(f"  Stage:       {GREEN}{program.stage_label}{RESET} ({round(program.stage_confidence*100)}%)")
    print(f"  Target:      {program.target.gene} / {program.target.organism}")
    print(f"  Compound:    {program.compound.name} (IC50 {program.compound.ic50_nm} nM)")
    print(f"  Audit flags: {len(program.audit_flags)} ({sum(1 for f in program.audit_flags if f.severity=='high')} HIGH)")
    print(f"  Contradictions: {len(program.contradictions)}")
    print(f"  White spaces:   {len([g for g in program.epistemic_gaps if g.classification=='white_space'])}")
    print(f"  Actions:     {len(program.ranked_actions)}")
    print(f"  Evidence %:  {program.completeness_pct}%")
    print(f"  GMP ready:   {program.gmp_readiness_pct}%")
    print(f"  Trace steps: {len(program.agent_trace)}")

    if program.key_finding:
        print(f"\n  {BOLD}KEY FINDING:{RESET}")
        print(f"  {program.key_finding}")

    print(f"\n{GREEN}{'═'*60}")
    print("  ✅ Full pipeline complete")
    print(f"{'═'*60}{RESET}\n")

    return program


def run_parsers_only():
    """Run only the deterministic parsers — no API key needed."""
    print(f"\n{BOLD}Parser-only mode (no API key needed){RESET}\n")

    from backend.parsers.vcf_parser import parse_vcf
    from backend.parsers.assay_parser import parse_resistance_assay
    from backend.parsers.compound_parser import parse_compound_screen

    vcf_path = DEMO_DIR / "gyra_variants.vcf"
    res_path = DEMO_DIR / "gyrase_resistance.csv"
    cpd_path = DEMO_DIR / "compound14_screen.csv"

    variants = parse_vcf(vcf_path)
    ok(f"VCF: {len(variants)} variants, {sum(1 for v in variants if v.is_qrdr_hotspot)} QRDR hotspots")

    assay = parse_resistance_assay(res_path)
    ok(f"Assay: {assay.raw_summary}")

    screen = parse_compound_screen(cpd_path)
    ok(f"Screen: {screen.raw_summary}")

    print("\nParser tests passed. Run without --parsers-only for full pipeline.\n")


if __name__ == "__main__":
    if "--parsers-only" in sys.argv:
        run_parsers_only()
    else:
        asyncio.run(run_full_pipeline())
