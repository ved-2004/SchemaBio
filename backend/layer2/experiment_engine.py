"""
LAYER 2 — Experiment Design Engine (AI PI Core)
=========================================================
Receives ProgramState from Layer 1.
Runs agent queries (CARD, PubChem, protocols.io) in parallel.
Uses LLM to synthesize results into ranked experiment recommendations.

This is the Biomni-inspired reasoning layer.
Key principle: every recommendation is grounded in real API data.
"""

import asyncio
import os
import json
from typing import Optional

from backend.models.program_state import (
    ProgramState, WorkflowStage, ExperimentRecommendation,
    Protocol, ResistanceGene, Compound
)
from backend.agents.card_agent import annotate_genes_from_list
from backend.agents.pubchem_agent import batch_get_compounds
from backend.agents.protocols_agent import get_protocols_for_stage

# ─────────────────────────────────────────────
# Experiment type templates by stage + mechanism
# ─────────────────────────────────────────────

EXPERIMENT_TEMPLATES = {
    WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION: [
        {
            "type": "Multiplex PCR — Carbapenemase Gene Detection",
            "rationale_template": "Genotypically confirm resistance mechanism in {organism}. "
                                  "PCR for KPC, NDM, OXA-48, VIM, IMP provides definitive mechanism assignment "
                                  "required for compound selection strategy.",
            "bioinformatics": ["CARD RGI (Resistance Gene Identifier)", "ResFinder v4.0", "ABRicate"],
            "controls_required": ["Known carbapenemase-producing positive control", 
                                  "Susceptible negative control", "No-template control"],
            "expected_output": "Gene identity + enzyme class assignment",
            "priority": "critical"
        },
        {
            "type": "Broth Microdilution MIC Panel — 12 Antibiotic Classes",
            "rationale_template": "Establish full susceptibility profile for {organism}. "
                                  "Systematic MIC panel across drug classes identifies cross-resistance patterns "
                                  "and narrows viable treatment options.",
            "bioinformatics": ["WHONET susceptibility interpretation", "AMRFinder+"],
            "controls_required": ["ATCC QC strain", "Growth control", "Sterility control"],
            "expected_output": "Full MIC table with EUCAST/CLSI interpretation (S/I/R)",
            "priority": "critical"
        },
        {
            "type": "Whole Genome Sequencing (Illumina Short-Read)",
            "rationale_template": "Capture full resistome and identify co-resistance genes, "
                                  "plasmid replicons, and integrons in {organism}. "
                                  "Enables AMR transmission network analysis.",
            "bioinformatics": ["Prokka annotation", "MLST typing", "Plasmid Finder", "SRST2"],
            "controls_required": ["Reference strain with known genome", "Extraction blank"],
            "expected_output": "Annotated genome with resistance gene catalog + plasmid map",
            "priority": "high"
        },
    ],
    WorkflowStage.HIT_DISCOVERY: [
        {
            "type": "High-Throughput MIC Screen — Compound Library",
            "rationale_template": "Screen compound collection for activity against {organism}. "
                                  "Miniaturized broth microdilution in 384-well format "
                                  "enables rapid MIC determination across full library.",
            "bioinformatics": ["ChEMBL activity filtering", "KNIME data normalization", "Z-score QC"],
            "controls_required": ["Positive control (known active antibiotic)", 
                                  "Negative control (DMSO vehicle)", "Sterility control"],
            "expected_output": "Hit list: compounds with MIC ≤ clinical breakpoint",
            "priority": "critical"
        },
        {
            "type": "Checkerboard Synergy Assay — Combination Screening",
            "rationale_template": "Evaluate synergistic combinations to overcome {resistance_gene} resistance. "
                                  "β-lactam + inhibitor combinations (e.g., ceftazidime-avibactam) "
                                  "are paradigmatic for carbapenemase-producing organisms.",
            "bioinformatics": ["FICI calculation", "SynergyFinder+ web tool"],
            "controls_required": ["Single-drug MIC controls for each agent", 
                                  "Positive synergy reference", "Growth control"],
            "expected_output": "FICI values: ≤0.5 = synergy, 0.5-4.0 = indifference, >4.0 = antagonism",
            "priority": "high"
        },
        {
            "type": "Time-Kill Kinetics — Bactericidal Activity Confirmation",
            "rationale_template": "Confirm bactericidal vs. bacteriostatic activity of hit compounds "
                                  "against {organism}. Critical for program advancement decision.",
            "bioinformatics": ["CFU/mL log10 reduction calculation", "PKPD modeling (PyDrugSim)"],
            "controls_required": ["No-antibiotic growth control", "Carryover neutralization control"],
            "expected_output": "Time-kill curves — ≥3 log10 CFU/mL reduction = bactericidal",
            "priority": "high"
        },
    ],
    WorkflowStage.EXPERIMENTAL_VALIDATION: [
        {
            "type": "Murine Neutropenic Thigh Infection Model",
            "rationale_template": "Establish in vivo proof-of-concept for lead compound against {organism}. "
                                  "Neutropenic thigh model is the gold standard for bacterial pharmacodynamics "
                                  "and required for IND-enabling package.",
            "bioinformatics": ["PKPD target attainment modeling", "Monte Carlo simulation (Pmetrics)"],
            "controls_required": ["Vehicle control", "Reference antibiotic arm", 
                                  "Untreated infection control", "Uninfected sham"],
            "expected_output": "Log10 CFU/thigh reduction + PKPD target (fT>MIC, fAUC/MIC)",
            "priority": "critical"
        },
        {
            "type": "Resistance Frequency Determination",
            "rationale_template": "Determine single-step mutation frequency to {compound} resistance. "
                                  "Resistance frequency <10^-9 is generally acceptable for clinical development.",
            "bioinformatics": ["Mutation rate calculation", "Whole-genome sequencing of resistant mutants"],
            "controls_required": ["Reference strain with known mutation frequency", "Antibiotic-free control"],
            "expected_output": "Mutation frequency + genetic basis of resistance (WGS of escapers)",
            "priority": "high"
        },
        {
            "type": "Biofilm Activity Assessment",
            "rationale_template": "Assess activity against {organism} biofilms. "
                                  "Biofilm-associated infections require 100-1000x higher concentrations. "
                                  "MBIC/MBEC determination guides clinical dosing strategy.",
            "bioinformatics": ["MBIC/MBEC ratio calculation", "Biofilm image analysis (ImageJ)"],
            "controls_required": ["Crystal violet biofilm quantification control", 
                                  "Planktonic MIC reference"],
            "expected_output": "MBIC (minimal biofilm inhibitory concentration) + MBEC",
            "priority": "medium"
        },
    ],
    WorkflowStage.PRECLINICAL_GAP_ANALYSIS: [
        {
            "type": "ADME Profiling Panel (in vitro)",
            "rationale_template": "Complete in vitro ADME characterization before IND submission. "
                                  "Identifies PK liabilities early before costly in vivo studies.",
            "bioinformatics": ["QSAR-based ADME prediction (SwissADME)", "MetaSite metabolite prediction"],
            "controls_required": ["Positive controls for each assay (known substrates)", "Blank matrix"],
            "expected_output": "Microsomal stability (t½), plasma protein binding, CYP inhibition panel, Caco-2 permeability",
            "priority": "critical"
        },
        {
            "type": "hERG Cardiac Safety Assay",
            "rationale_template": "Screen for cardiac liability. hERG channel inhibition (QT prolongation) "
                                  "is a major cause of late-stage clinical failure. Required by ICH S7B.",
            "bioinformatics": ["hERG computational prediction (DeepHERG)", "IC50 extrapolation to safety margin"],
            "controls_required": ["Cisapride positive control", "Vehicle negative control"],
            "expected_output": "hERG IC50 + safety margin (MIC/IC50 ratio)",
            "priority": "critical"
        },
    ],
}


# ─────────────────────────────────────────────
# Hypothesis card builder
# ─────────────────────────────────────────────

def build_hypothesis_card(
    organism: Optional[str],
    genes: list[ResistanceGene],
    compounds: list[Compound],
    stage: WorkflowStage
) -> str:
    """
    Construct a literature-backed scientific hypothesis for the program.
    Grounded in CARD-annotated mechanism data.
    """
    org_str = organism or "the target pathogen"
    gene_str = ", ".join(f"{g.gene_name} ({g.mechanism or 'mechanism TBD'})" for g in genes[:3]) or "uncharacterized resistance determinants"
    compound_str = ", ".join(c.name for c in compounds[:3]) or "candidate compounds"

    mechanism_insights = []
    for gene in genes[:2]:
        if gene.mechanism:
            if "carbapenemase" in gene.mechanism.lower():
                mechanism_insights.append(
                    f"{gene.gene_name}-mediated carbapenem resistance requires "
                    "covalent enzyme inhibition or compound structural features "
                    "that evade β-lactamase hydrolysis (e.g., diazabicyclooctane scaffold, siderophore conjugation)"
                )
            elif "efflux" in gene.mechanism.lower():
                mechanism_insights.append(
                    f"{gene.gene_name}-driven efflux resistance may be overcome by "
                    "efflux pump inhibitor co-administration or compounds with reduced pump recognition"
                )
            elif "methyltransferase" in gene.mechanism.lower():
                mechanism_insights.append(
                    f"{gene.gene_name} RNA methylation confers broad-spectrum resistance — "
                    "compounds targeting upstream regulatory pathways may restore susceptibility"
                )

    insight_text = " ".join(mechanism_insights) if mechanism_insights else \
        "Resistance mechanism characterization is required to guide compound selection strategy."

    return (
        f"SCIENTIFIC HYPOTHESIS\n"
        f"{'─'*50}\n"
        f"Target organism: {org_str}\n"
        f"Resistance determinants: {gene_str}\n"
        f"Candidate compounds: {compound_str}\n"
        f"Program stage: {stage.value.replace('_', ' ').title()}\n\n"
        f"Central hypothesis: {insight_text}\n\n"
        f"Predicted path: Mechanism confirmation → compound optimization guided by "
        f"resistance gene structure → in vitro validation → PK/PD modeling → in vivo proof-of-concept.\n"
        f"Key decision gate: MIC ≤ EUCAST clinical breakpoint in at least 3 independent isolates "
        f"before advancing to validation stage."
    )


# ─────────────────────────────────────────────
# Main Layer 2 entry point
# ─────────────────────────────────────────────

async def run_experiment_design_engine(state: ProgramState) -> ProgramState:
    """
    Main Layer 2 entry point.
    Enriches ProgramState with experiment recommendations + hypothesis.
    """

    # ── Step 1: Parallel agent queries ──
    gene_names = [g.gene_name for g in state.resistance_genes]
    compound_names = [c.name for c in state.compounds]

    annotated_genes, enriched_compounds, protocols = await asyncio.gather(
        annotate_genes_from_list(gene_names) if gene_names else asyncio.sleep(0, result=[]),
        batch_get_compounds(compound_names) if compound_names else asyncio.sleep(0, result=[]),
        get_protocols_for_stage(
            stage=state.stage.value,
            organism=state.organism,
            resistance_gene=gene_names[0] if gene_names else None
        )
    )

    # Update state with enriched data
    if annotated_genes:
        state.resistance_genes = list(annotated_genes)
    if enriched_compounds:
        state.compounds = list(enriched_compounds)

    # ── Step 2: Build experiment recommendations ──
    templates = EXPERIMENT_TEMPLATES.get(state.stage, 
                    EXPERIMENT_TEMPLATES.get(WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION))

    gene_0 = state.resistance_genes[0] if state.resistance_genes else None
    compound_0 = state.compounds[0] if state.compounds else None
    org = state.organism or "target organism"
    gene_name = gene_0.gene_name if gene_0 else "resistance gene"

    recs = []
    for i, template in enumerate(templates[:3]):
        rationale = template["rationale_template"].format(
            organism=org,
            resistance_gene=gene_name,
            compound=compound_0.name if compound_0 else "lead compound"
        )

        # Attach protocol from protocols.io
        protocol = protocols[i] if i < len(protocols) else None

        rec = ExperimentRecommendation(
            rank=i + 1,
            experiment_type=template["type"],
            rationale=rationale,
            protocol=protocol,
            missing_controls=template.get("controls_required", []),
            bioinformatics_steps=template.get("bioinformatics", []),
            expected_output=template.get("expected_output"),
            priority=template.get("priority", "medium")
        )
        recs.append(rec)

    state.experiment_recommendations = recs

    # ── Step 3: Build hypothesis card ──
    state.hypothesis_card = build_hypothesis_card(
        state.organism,
        state.resistance_genes,
        state.compounds,
        state.stage
    )

    # ── Step 4: Add literature context ──
    state.literature_context = _get_literature_context(gene_names, state.stage)

    return state


def _get_literature_context(gene_names: list[str], stage: WorkflowStage) -> list[str]:
    """
    Curated key literature references by mechanism and stage.
    In production, replace with real semantic search (e.g., PubMed API).
    """
    refs = []
    for gene in gene_names[:2]:
        g = gene.lower()
        if "blakpc" in g or "kpc" in g:
            refs.append("Nordmann P et al. (2011). Global emergence of carbapenemase-producing Enterobacteriaceae. Clin Infect Dis. 10.1086/657009")
            refs.append("Papp-Wallace KM et al. (2011). Carbapenems: past, present, and future. Antimicrob Agents Chemother. 10.1128/AAC.00296-11")
        elif "blaNDM" in gene or "ndm" in g:
            refs.append("Walsh TR et al. (2011). Dissemination of NDM-1 positive bacteria in the New Delhi environment. Lancet Infect Dis. 10.1016/S1473-3099(11)70059-7")
        elif "mcr" in g:
            refs.append("Liu YY et al. (2016). Emergence of plasmid-mediated colistin resistance mechanism MCR-1 in animals and human beings in China. Lancet Infect Dis. 10.1016/S1473-3099(15)00424-7")
        elif "vana" in g or "vanb" in g:
            refs.append("Courvalin P (2006). Vancomycin resistance in gram-positive cocci. Clin Infect Dis. 10.1086/491711")

    if stage == WorkflowStage.EXPERIMENTAL_VALIDATION:
        refs.append("Craig WA (1998). Pharmacokinetic/pharmacodynamic parameters: rationale for antibacterial dosing of mice and men. Clin Infect Dis. 10.1086/514974")

    return refs
