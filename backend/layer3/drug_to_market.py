"""
LAYER 3 — Drug-to-Market Execution Engine
=========================================================
Takes enriched ProgramState from Layer 2.
Maps scientific evidence to:
  - Funding/grant strategy
  - CRO/lab partner routing
  - CDMO/GMP readiness score
  - FDA pathway eligibility
  - Translational gap checklist

This layer is what makes AIDEN-AMP different from all other
science agents. It doesn't stop at insight generation.
"""

from backend.models.program_state import (
    ProgramState, WorkflowStage, FundingTarget,
    TranslationalReadiness
)

# ─────────────────────────────────────────────
# Funding / Grant Database
# ─────────────────────────────────────────────

FUNDING_DATABASE = [
    {
        "program_name": "CARB-X Explorer Award",
        "agency": "CARB-X (Wellcome / BARDA / Gates Foundation)",
        "eligible_stages": [WorkflowStage.HIT_DISCOVERY, WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION],
        "award_size": "Up to $2M",
        "url": "https://carb-x.org/apply/",
        "focus": ["novel antibiotics", "non-traditional therapies", "antibiotic resistance"],
        "eligibility_requirements": [
            "Novel mechanism of action or differentiated spectrum",
            "Demonstrated in vitro activity",
            "Not a me-too compound"
        ]
    },
    {
        "program_name": "CARB-X Development Award",
        "agency": "CARB-X",
        "eligible_stages": [WorkflowStage.EXPERIMENTAL_VALIDATION, WorkflowStage.PRECLINICAL_GAP_ANALYSIS],
        "award_size": "Up to $20M",
        "url": "https://carb-x.org/apply/",
        "focus": ["lead optimization", "preclinical package", "gram-negative bacteria"],
        "eligibility_requirements": [
            "Completed hit-to-lead optimization",
            "In vivo efficacy data in at least one model",
            "Clear ADME/tox profile"
        ]
    },
    {
        "program_name": "NIH NIAID R01 — Drug Development for Drug-Resistant Bacteria",
        "agency": "NIH NIAID",
        "eligible_stages": [
            WorkflowStage.TARGET_IDENTIFICATION,
            WorkflowStage.HIT_DISCOVERY,
            WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION,
            WorkflowStage.EXPERIMENTAL_VALIDATION
        ],
        "award_size": "Up to $500K/year × 5 years",
        "url": "https://grants.nih.gov/grants/guide/pa-files/PAR-22-179.html",
        "focus": ["mechanism research", "drug discovery", "antimicrobial resistance"],
        "eligibility_requirements": [
            "Academic or nonprofit institution",
            "Novel hypothesis with preliminary data",
            "Clear translational relevance"
        ]
    },
    {
        "program_name": "BARDA CARB BAA — Advanced Development",
        "agency": "BARDA (Biomedical Advanced Research and Development Authority)",
        "eligible_stages": [WorkflowStage.PRECLINICAL_GAP_ANALYSIS, WorkflowStage.MANUFACTURING_FEASIBILITY],
        "award_size": "$10M–$200M",
        "url": "https://www.medicalcountermeasures.gov/barda/",
        "focus": ["ESKAPE pathogens", "gram-negative MDR", "Phase 1/2 ready"],
        "eligibility_requirements": [
            "IND-enabling studies completed or in progress",
            "Phase 1 safety data (if applicable)",
            "US manufacturing capability preferred",
            "QIDP designation advantageous"
        ]
    },
    {
        "program_name": "DARPA PREPARE — Prophylactic/Therapeutic AMR",
        "agency": "DARPA",
        "eligible_stages": [WorkflowStage.HIT_DISCOVERY, WorkflowStage.EXPERIMENTAL_VALIDATION],
        "award_size": "Up to $15M",
        "url": "https://www.darpa.mil/program/prepare",
        "focus": ["novel modalities", "phage therapy", "CRISPR antimicrobials", "rapid development"],
        "eligibility_requirements": [
            "High-risk, high-reward approach",
            "Rapid deployment potential",
            "Non-traditional antibiotic modality preferred"
        ]
    },
    {
        "program_name": "Wellcome Trust Innovator Award — AMR",
        "agency": "Wellcome Trust",
        "eligible_stages": [
            WorkflowStage.TARGET_IDENTIFICATION,
            WorkflowStage.HIT_DISCOVERY,
            WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION
        ],
        "award_size": "Up to £500K",
        "url": "https://wellcome.org/grant-funding/schemes/innovator-awards-health-innovation",
        "focus": ["diagnostics", "research tools", "global health", "low-middle income countries"],
        "eligibility_requirements": [
            "Clear global health impact",
            "Feasibility demonstrated",
            "Academic or early-stage company"
        ]
    },
]


# ─────────────────────────────────────────────
# CRO / Lab Partner Routing
# ─────────────────────────────────────────────

CRO_ROUTING = {
    WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION: {
        "partner_type": "Clinical Microbiology CRO (BSL-2 certified)",
        "capabilities_needed": ["MIC testing (CLSI/EUCAST)", "PCR genotyping", "WGS with AMR annotation"],
        "example_partners": ["Micromyx (Kalamazoo, MI)", "JMI Laboratories (North Liberty, IA)", "IHMA (Schaumburg, IL)"],
        "biosafety_level": "BSL-2",
        "timeline_estimate": "4–8 weeks"
    },
    WorkflowStage.HIT_DISCOVERY: {
        "partner_type": "HTS / Drug Discovery CRO",
        "capabilities_needed": ["384-well MIC screening", "Echo liquid handling", "Data normalization"],
        "example_partners": ["Evotec (Hamburg)", "Jubilant Biosys (Bangalore)", "Eurofins Discovery"],
        "biosafety_level": "BSL-2",
        "timeline_estimate": "6–10 weeks"
    },
    WorkflowStage.EXPERIMENTAL_VALIDATION: {
        "partner_type": "In Vivo Pharmacology CRO (AAALAC-accredited)",
        "capabilities_needed": ["Murine infection models", "PKPD sampling", "CFU counting"],
        "example_partners": ["Bioduro-Sundia (Beijing/San Diego)", "Wuxi AppTec", "Charles River Laboratories"],
        "biosafety_level": "BSL-2/ABSL-2",
        "timeline_estimate": "8–16 weeks"
    },
    WorkflowStage.PRECLINICAL_GAP_ANALYSIS: {
        "partner_type": "Full-Service Preclinical CRO (IND-enabling)",
        "capabilities_needed": ["GLP toxicology", "ADME/DMPK", "hERG safety", "Formulation development"],
        "example_partners": ["Covance (Labcorp Drug Development)", "Pacific BioLabs", "BioDuro"],
        "biosafety_level": "BSL-1/2",
        "timeline_estimate": "12–24 months"
    },
    WorkflowStage.MANUFACTURING_FEASIBILITY: {
        "partner_type": "CDMO (Contract Development and Manufacturing Organization)",
        "capabilities_needed": ["API synthesis scale-up", "GMP manufacturing", "ICH stability studies"],
        "example_partners": ["Lonza (Basel)", "CARBOGEN AMCIS", "Hovione", "Recipharm"],
        "biosafety_level": "GMP facility required",
        "timeline_estimate": "18–36 months to GMP batch"
    },
}


# ─────────────────────────────────────────────
# CDMO/GMP Readiness Scoring
# ─────────────────────────────────────────────

# IND-enabling study checklist (required before Phase 1)
IND_ENABLING_STUDIES = [
    {"id": "in_vitro_activity", "name": "In vitro MIC panel (≥30 clinical isolates)", "stage_required": WorkflowStage.HIT_DISCOVERY},
    {"id": "mechanism_id", "name": "Mechanism of action identified", "stage_required": WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION},
    {"id": "in_vivo_efficacy", "name": "In vivo efficacy (murine model)", "stage_required": WorkflowStage.EXPERIMENTAL_VALIDATION},
    {"id": "adme", "name": "ADME profiling (microsomal stability, PPB, CYP)", "stage_required": WorkflowStage.PRECLINICAL_GAP_ANALYSIS},
    {"id": "herg_safety", "name": "hERG cardiac safety assay", "stage_required": WorkflowStage.PRECLINICAL_GAP_ANALYSIS},
    {"id": "acute_tox", "name": "Acute toxicity study (GLP, 14-day)", "stage_required": WorkflowStage.PRECLINICAL_GAP_ANALYSIS},
    {"id": "repeat_dose_tox", "name": "28-day repeat-dose toxicity study", "stage_required": WorkflowStage.PRECLINICAL_GAP_ANALYSIS},
    {"id": "genotox", "name": "Genotoxicity panel (Ames + in vitro micronucleus)", "stage_required": WorkflowStage.PRECLINICAL_GAP_ANALYSIS},
    {"id": "formulation", "name": "Formulation development + stability data", "stage_required": WorkflowStage.MANUFACTURING_FEASIBILITY},
    {"id": "gmp_batch", "name": "GMP drug substance batch (≥1 batch)", "stage_required": WorkflowStage.MANUFACTURING_FEASIBILITY},
    {"id": "cmc", "name": "CMC documentation (ICH Q6A/Q6B)", "stage_required": WorkflowStage.MANUFACTURING_FEASIBILITY},
]


def compute_cdmo_readiness_score(state: ProgramState) -> float:
    """
    Score CDMO/GMP readiness from 0-100 based on stage and evidence.
    0-20: Discovery — not ready
    20-40: Validation — some work done
    40-60: Preclinical — IND preparation possible
    60-80: IND-ready or filed
    80-100: GMP batch available, Phase 1 ready
    """
    stage_base_scores = {
        WorkflowStage.UNKNOWN: 0,
        WorkflowStage.TARGET_IDENTIFICATION: 5,
        WorkflowStage.HIT_DISCOVERY: 12,
        WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION: 18,
        WorkflowStage.EXPERIMENTAL_VALIDATION: 35,
        WorkflowStage.PRECLINICAL_GAP_ANALYSIS: 55,
        WorkflowStage.MANUFACTURING_FEASIBILITY: 75,
    }

    score = stage_base_scores.get(state.stage, 0)

    # Evidence bonuses
    if state.mic_data: score += 5
    if state.resistance_genes and state.resistance_genes[0].mechanism: score += 5
    if len(state.compounds) > 0 and state.compounds[0].drug_likeness_score and state.compounds[0].drug_likeness_score > 0.5: score += 5

    return min(100.0, round(score, 1))


def get_scale_up_blockers(state: ProgramState) -> list[str]:
    """Identify stage-appropriate scale-up blockers."""
    blockers = []
    stage = state.stage

    early_stages = [WorkflowStage.UNKNOWN, WorkflowStage.TARGET_IDENTIFICATION,
                    WorkflowStage.HIT_DISCOVERY, WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION]

    if stage in early_stages:
        blockers.extend([
            "No in vivo efficacy data — required before any scale-up discussion",
            "No ADME/tox profile — PK properties unknown",
            "No defined lead compound — optimization not started",
            "No formulation data — route of administration undefined"
        ])
    elif stage == WorkflowStage.EXPERIMENTAL_VALIDATION:
        blockers.extend([
            "GLP toxicology studies not yet completed",
            "ADME package may be incomplete",
            "hERG cardiac safety data required",
            "Synthetic route scalability not assessed"
        ])
    elif stage == WorkflowStage.PRECLINICAL_GAP_ANALYSIS:
        blockers.extend([
            "CMC documentation not initiated",
            "GMP synthesis route not qualified",
            "ICH stability studies pending",
            "Scale-up yield and purity data needed"
        ])

    return blockers


def get_fda_pathway(state: ProgramState) -> dict:
    """
    Determine FDA-regulated pathway signals for antibiotic programs.
    Key designations: QIDP, Fast Track, LPAD (Limited Population Pathway).
    """
    has_eskape = state.organism and any(
        p in state.organism.lower() for p in
        ["klebsiella", "acinetobacter", "pseudomonas", "staphylococcus aureus",
         "enterococcus", "enterobacter", "escherichia coli"]
    )

    has_critical_resistance = any(
        any(k in g.gene_name.lower() for k in ["kpc", "ndm", "oxa", "vim", "mcr"])
        for g in state.resistance_genes
    )

    qidp_eligible = has_eskape or has_critical_resistance
    fast_track_eligible = qidp_eligible and state.stage.value in [
        "experimental_validation", "preclinical_gap_analysis"
    ]
    lpad_eligible = has_critical_resistance  # LPAD for serious/life-threatening with unmet need

    if state.stage == WorkflowStage.MANUFACTURING_FEASIBILITY:
        pathway = "NDA (505(b)(1) or 505(b)(2)) — standard pathway with potential QIDP/Fast Track"
    elif state.stage in [WorkflowStage.PRECLINICAL_GAP_ANALYSIS, WorkflowStage.EXPERIMENTAL_VALIDATION]:
        pathway = "IND application (Phase 1 safety) → Phase 2/3 efficacy — QIDP designation recommended"
    else:
        pathway = "Pre-IND consultation with FDA CDER Division of Anti-Infectives recommended"

    return {
        "qidp_eligible": qidp_eligible,
        "fast_track_eligible": fast_track_eligible,
        "lpad_eligible": lpad_eligible,
        "pathway": pathway,
        "notes": [
            "QIDP grants 5-year market exclusivity extension + priority review voucher eligibility" if qidp_eligible else None,
            "LPAD allows approval based on smaller pivotal trials if treating serious, life-threatening infection" if lpad_eligible else None,
            "GAIN Act incentives apply for qualifying pathogens (ESKAPE + 7 others)" if has_eskape else None,
        ]
    }


# ─────────────────────────────────────────────
# Funding fit scorer
# ─────────────────────────────────────────────

def score_funding_fit(grant: dict, state: ProgramState) -> float:
    score = 0.0

    # Stage match (most important)
    if state.stage in grant["eligible_stages"]:
        score += 0.6

    # Organism/focus match
    org_str = (state.organism or "").lower()
    for focus_term in grant.get("focus", []):
        if any(term in org_str for term in focus_term.split()):
            score += 0.1
        if any(term in state.project_summary.lower() for term in focus_term.split()):
            score += 0.1

    # Evidence strength match
    from backend.models.program_state import EvidenceStrength
    if state.evidence_strength == EvidenceStrength.STRONG:
        score += 0.2
    elif state.evidence_strength == EvidenceStrength.MODERATE:
        score += 0.1

    return min(1.0, round(score, 2))


def identify_eligibility_gaps(grant: dict, state: ProgramState) -> list[str]:
    gaps = []
    for req in grant.get("eligibility_requirements", []):
        req_lower = req.lower()
        if "in vitro activity" in req_lower and not state.mic_data:
            gaps.append(f"Missing: {req}")
        if "in vivo" in req_lower and state.stage.value not in ["experimental_validation", "preclinical_gap_analysis", "manufacturing_feasibility"]:
            gaps.append(f"Missing: {req}")
        if "adme" in req_lower and state.stage.value not in ["preclinical_gap_analysis", "manufacturing_feasibility"]:
            gaps.append(f"Gap: {req}")
    return gaps


# ─────────────────────────────────────────────
# Execution brief generator
# ─────────────────────────────────────────────

def generate_execution_brief(state: ProgramState, readiness: TranslationalReadiness) -> str:
    org = state.organism or "target organism"
    genes = ", ".join(g.gene_name for g in state.resistance_genes[:2]) or "uncharacterized"
    stage = state.stage.value.replace("_", " ").title()

    top_funding = state.funding_targets[0] if state.funding_targets else None
    funding_line = f"Top funding match: {top_funding.program_name} ({top_funding.agency}, {top_funding.award_size}) — fit score {top_funding.fit_score:.0%}" if top_funding else "No high-fit funding match identified"

    cro_info = CRO_ROUTING.get(state.stage, {})
    cro_line = f"Recommended CRO type: {cro_info.get('partner_type', 'TBD')} ({cro_info.get('timeline_estimate', 'TBD')})" if cro_info else ""

    fda_line = f"FDA pathway: {readiness.fda_pathway or 'Pre-IND consultation recommended'}"
    if readiness.qidp_eligible:
        fda_line += " | QIDP designation eligible"

    blockers_line = "\n  • ".join(readiness.scale_up_blockers[:3]) if readiness.scale_up_blockers else "None identified at current stage"

    return (
        f"EXECUTION BRIEF — AIDEN-AMP\n"
        f"{'═'*55}\n"
        f"Program: {org} | {genes} | Stage: {stage}\n"
        f"CDMO Readiness Score: {readiness.cdmo_readiness_score:.0f}/100\n"
        f"Evidence Completeness: {readiness.evidence_completeness_score:.0f}%\n\n"
        f"FUNDING STRATEGY\n{funding_line}\n\n"
        f"EXTERNAL EXECUTION\n{cro_line}\n\n"
        f"REGULATORY PATH\n{fda_line}\n\n"
        f"SCALE-UP BLOCKERS\n  • {blockers_line}\n\n"
        f"IMMEDIATE NEXT ACTIONS\n"
        f"  1. Execute top-ranked experiment (see Layer 2 recommendations)\n"
        f"  2. Apply to {top_funding.program_name if top_funding else 'matched grant program'} — prepare evidence package\n"
        f"  3. Request pre-IND meeting with FDA CDER (Division of Anti-Infectives) to confirm pathway\n"
        f"  4. Engage {cro_info.get('partner_type', 'appropriate CRO')} for next experimental phase\n"
    )


# ─────────────────────────────────────────────
# Main Layer 3 entry point
# ─────────────────────────────────────────────

async def run_drug_to_market_engine(state: ProgramState) -> ProgramState:
    """
    Main Layer 3 entry point.
    Maps scientific program state to execution roadmap.
    """

    # ── Funding routing ──
    funding_targets = []
    for grant in FUNDING_DATABASE:
        fit_score = score_funding_fit(grant, state)
        if fit_score > 0.2:  # Only include relevant grants
            gaps = identify_eligibility_gaps(grant, state)
            funding_targets.append(FundingTarget(
                program_name=grant["program_name"],
                agency=grant["agency"],
                fit_score=fit_score,
                stage_match=state.stage in grant["eligible_stages"],
                eligibility_gaps=gaps,
                url=grant["url"],
                award_size=grant["award_size"]
            ))

    # Sort by fit score
    state.funding_targets = sorted(funding_targets, key=lambda x: x.fit_score, reverse=True)[:4]

    # ── CDMO/GMP readiness ──
    cdmo_score = compute_cdmo_readiness_score(state)
    scale_up_blockers = get_scale_up_blockers(state)
    fda_info = get_fda_pathway(state)

    # ── Missing IND studies ──
    missing_ind = []
    stage_order = list(WorkflowStage)
    current_idx = stage_order.index(state.stage) if state.stage in stage_order else 0

    for study in IND_ENABLING_STUDIES:
        study_stage_idx = stage_order.index(study["stage_required"]) if study["stage_required"] in stage_order else 99
        if study_stage_idx > current_idx:
            missing_ind.append(study["name"])

    # Evidence completeness
    total_ind = len(IND_ENABLING_STUDIES)
    completed_ind = total_ind - len(missing_ind)
    evidence_pct = round((completed_ind / total_ind) * 100, 1)

    # CRO routing
    cro_info = CRO_ROUTING.get(state.stage, {})

    readiness = TranslationalReadiness(
        cdmo_readiness_score=cdmo_score,
        evidence_completeness_score=evidence_pct,
        scale_up_blockers=scale_up_blockers,
        missing_ind_studies=missing_ind,
        qidp_eligible=fda_info["qidp_eligible"],
        fast_track_eligible=fda_info["fast_track_eligible"],
        lpad_eligible=fda_info["lpad_eligible"],
        fda_pathway=fda_info["pathway"],
        cro_partner_type=cro_info.get("partner_type"),
        formulation_data_present=state.stage in [WorkflowStage.PRECLINICAL_GAP_ANALYSIS, WorkflowStage.MANUFACTURING_FEASIBILITY],
        in_vivo_data_present=state.stage in [WorkflowStage.EXPERIMENTAL_VALIDATION, WorkflowStage.PRECLINICAL_GAP_ANALYSIS, WorkflowStage.MANUFACTURING_FEASIBILITY],
    )

    state.translational_readiness = readiness
    state.execution_brief = generate_execution_brief(state, readiness)

    return state
