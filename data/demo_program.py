"""
data/demo_program.py

Antibiotic resistance demo program.
Maps exactly to the example in the AIDEN brief:

  Target: DNA gyrase (antibiotic target)
  Compound: Compound-14
  Assay IC50: 32 nM
  Resistance profile: Reduced sensitivity in strain X
  Genomics: Mutation in gyrA (D87N)
  Literature: 3 supporting papers
  Stage: Hit triage → Resistance Mechanism Characterization
  Manufacturability: Appears tractable (4-step route)

Demo always works — pre-built, no backend required.
"""

from __future__ import annotations
from ..api.models.drug_program import (
    DrugProgram, TargetProfile, CompoundProfile, ResistanceProfile,
    EfficacySignals, EvidencePackage, ManufacturingProfile,
    ExecutionGuidance, RegulatoryReadiness, CRONeed, FundingOpportunity,
    AuditFlag, Contradiction, EpistemicGap, LiteratureResult,
    DrugProgramAction, ProgramStage,
)


def build_antibiotic_demo_program() -> DrugProgram:
    """
    Build the antibiotic resistance demo DrugProgram.
    This is the pre-loaded example — works without any file uploads.
    """
    program = DrugProgram(
        program_name="Gyrase Inhibitor Program — Compound-14",
        uploaded_files=[
            "gyra_variants.vcf",
            "gyrase_resistance.csv",
            "compound14_screen.csv",
        ],
    )

    # ── Target ────────────────────────────────────────────────────────────
    program.target = TargetProfile(
        gene="GyrA",
        protein="DNA gyrase subunit A",
        mechanism_of_action="DNA gyrase inhibition — prevents DNA supercoiling",
        pathway="DNA replication / bacterial topoisomerase pathway",
        indication="Gram-negative bacterial infection",
        organism="E. coli (ATCC 25922 + clinical isolates)",
        target_class="Type II topoisomerase",
        druggability_score=0.87,
        validated_in_disease=True,
        known_resistance_mechanisms=[
            "gyrA QRDR mutations (D87N, S83L)",
            "parC QRDR mutations (S80I)",
            "efflux pumps (AcrAB-TolC upregulation)",
        ],
    )

    # ── Lead compound ─────────────────────────────────────────────────────
    program.compound = CompoundProfile(
        name="Compound-14",
        smiles="C1=CC(=NC=C1)NC(=O)C2=CN=C(C=C2)NC3=CC=C(C=C3)F",
        ic50_nm=32.0,
        mic_ugml=0.125,
        selectivity_ratio=None,
        structural_class="fluoroquinolone-like (novel scaffold)",
        synthesis_steps=4,
        synthesis_complexity="tractable",
        molecular_weight=371.4,
        logp=2.1,
        psa=72.8,
        hbd=2,
        hba=5,
        lipinski_pass=True,
    )

    # ── All compounds from screen ─────────────────────────────────────────
    program.all_compounds = [
        {"id":"CPD_014","name":"Compound-14","target":"GyrA","ic50_nm":32,"mic_ugml":0.125,
         "log2fc":2.8,"neg_log10p":5.2,"zscore":4.4,"dmso_risk":False,"flag":"TOP_HIT"},
        {"id":"CPD_007","name":"Compound-7", "target":"GyrA","ic50_nm":89,"mic_ugml":0.5,
         "log2fc":2.1,"neg_log10p":3.8,"zscore":3.2,"dmso_risk":True,"flag":"FOLLOW_UP"},
        {"id":"CPD_023","name":"Compound-23","target":"GyrA","ic50_nm":210,"mic_ugml":1.0,
         "log2fc":1.4,"neg_log10p":2.2,"zscore":2.1,"dmso_risk":False,"flag":"FOLLOW_UP"},
        {"id":"CPD_031","name":"Compound-31","target":"GyrA","ic50_nm":8.4,"mic_ugml":0.06,
         "log2fc":3.1,"neg_log10p":5.8,"zscore":4.9,"dmso_risk":False,"flag":"TOP_HIT"},
        {"id":"CPD_041","name":"Ciprofloxacin (ref)","target":"GyrA","ic50_nm":11,"mic_ugml":0.03,
         "log2fc":3.5,"neg_log10p":6.2,"zscore":5.2,"dmso_risk":False,"flag":"TOP_HIT"},
        {"id":"CPD_052","name":"Compound-52","target":"GyrA","ic50_nm":890,"mic_ugml":8.0,
         "log2fc":-0.2,"neg_log10p":0.4,"zscore":-0.4,"dmso_risk":True,"flag":"DEPRIORITIZE"},
        {"id":"CPD_061","name":"Compound-61","target":"GyrA","ic50_nm":450,"mic_ugml":4.0,
         "log2fc":0.3,"neg_log10p":0.9,"zscore":0.6,"dmso_risk":False,"flag":"LOW"},
    ]

    # ── Resistance profile ────────────────────────────────────────────────
    program.resistance = ResistanceProfile(
        resistant_strains=["E.coli strain X (clinical isolate)", "E.coli ATCC 35218"],
        sensitive_strains=["E.coli ATCC 25922 (WT)", "E.coli MG1655"],
        resistance_mutations=["gyrA D87N", "parC S80I"],
        fold_shift=64.0,
        mechanism=None,  # ← Not characterized yet — this is the key gap
        characterized=False,
        frequency_of_resistance=None,
        mic_values=[
            {"strain":"E.coli ATCC 25922","compound":"Compound-14","mic":0.125,"wt_mic":0.125,"fold":1.0,"classification":"SUSCEPTIBLE"},
            {"strain":"E.coli strain X",  "compound":"Compound-14","mic":8.0,  "wt_mic":0.125,"fold":64.0,"classification":"RESISTANT"},
            {"strain":"E.coli ATCC 35218","compound":"Compound-14","mic":4.0,  "wt_mic":0.125,"fold":32.0,"classification":"RESISTANT"},
            {"strain":"E.coli ATCC 25922","compound":"Compound-31","mic":0.06, "wt_mic":0.06, "fold":1.0,"classification":"SUSCEPTIBLE"},
            {"strain":"E.coli strain X",  "compound":"Compound-31","mic":8.0,  "wt_mic":0.06, "fold":133.3,"classification":"RESISTANT"},
            {"strain":"E.coli ATCC 25922","compound":"Ciprofloxacin","mic":0.03,"wt_mic":0.03,"fold":1.0,"classification":"SUSCEPTIBLE"},
            {"strain":"E.coli strain X",  "compound":"Ciprofloxacin","mic":32.0,"wt_mic":0.03,"fold":1067,"classification":"RESISTANT"},
        ],
    )

    # ── Efficacy ──────────────────────────────────────────────────────────
    program.efficacy = EfficacySignals(
        in_vitro_confirmed=True,
        in_vivo_confirmed=False,
        organism_model="E. coli",
        efficacy_endpoint="MIC (broth microdilution)",
    )

    # ── Evidence ──────────────────────────────────────────────────────────
    program.evidence = EvidencePackage(
        has_target_validation=True,
        has_mechanism_confirmed=False,          # ← Gap: mechanism not confirmed
        has_dose_response=True,
        has_selectivity_data=False,             # ← Gap: no mammalian cytotox
        has_mic_data=True,
        has_time_kill_data=False,               # ← Gap: no time-kill
        has_resistance_profiling=True,
        has_in_vivo_efficacy=False,
        has_solubility=False,
        has_permeability=False,
        has_metabolic_stability=False,
        has_cyp_inhibition=False,
        has_herg_data=False,
        has_genotoxicity=False,
        has_acute_toxicity=False,
        has_synthesis_route=True,               # 4-step route available
        has_analytical_methods=False,
        has_forced_degradation=False,
        has_gmp_batch=False,
    )

    # ── Stage ─────────────────────────────────────────────────────────────
    program.current_stage = ProgramStage.RESISTANCE_CHAR
    program.stage_confidence = 0.93
    program.stage_rationale = (
        "gyrA D87N + parC S80I mutations detected with 64× MIC fold-shift in resistant strain. "
        "Mechanism not yet characterized (efflux vs. target mutation vs. bypass). "
        "Lead compound active in WT but not in resistant isolates."
    )

    # ── Manufacturing ─────────────────────────────────────────────────────
    program.manufacturing = ManufacturingProfile(
        synthesis_tractability="tractable",
        estimated_steps=4,
        key_starting_materials=["2-aminopyridine", "3-fluorobenzaldehyde"],
        scale_up_risks=[
            "4-step route appears tractable — no obvious scale-up blockers",
            "Fluorine incorporation: ensure safe HF handling at scale",
        ],
        cdmo_readiness="not_ready",
        recommended_cdmo_type="small_molecule",
        gmp_batch_needed_g=250.0,
    )

    # ── Regulatory ────────────────────────────────────────────────────────
    program.regulatory = RegulatoryReadiness(
        ind_filed=False,
        missing_ind_components=[
            "IND Section 2: Pharmacology + Toxicology",
            "IND Section 3: CMC package",
            "IND Section 4: Clinical protocol",
            "IND Section 5: Investigator information",
        ],
        regulatory_strategy="Consider QIDP (Qualified Infectious Disease Product) designation for FDA Fast Track + 5-year market exclusivity",
    )

    # ── Audit flags ───────────────────────────────────────────────────────
    program.audit_flags = [
        AuditFlag(
            id="audit_001", type="missing_control", severity="high",
            title="No vehicle/DMSO control in compound screen",
            detail="No vehicle control wells detected in compound14_screen.csv. IC50 normalization unreliable without matched DMSO controls at identical concentration.",
            field_source="all_compounds: no vehicle/DMSO_ctrl id",
        ),
        AuditFlag(
            id="audit_002", type="replicate_concern", severity="medium",
            title="Single replicate MIC values (n=1)",
            detail=f"MIC values appear as n=1 measurements. CLSI M07 requires n≥3 for reportable MIC. False positive rate for single-point MIC: ~30%.",
            field_source="resistance.mic_values: no replicate column",
        ),
        AuditFlag(
            id="audit_003", type="incomplete_characterization", severity="high",
            title="Resistance mechanism not characterized",
            detail="gyrA D87N and parC S80I detected but mechanism (target mutation impact vs. efflux) not confirmed. 64× fold-shift could be efflux-driven — critical before strategy decision.",
            field_source="resistance.mechanism = null, resistance.characterized = false",
        ),
        AuditFlag(
            id="audit_004", type="missing_data", severity="medium",
            title="No mammalian cytotoxicity counter-screen",
            detail=f"Compound-14 (MIC 0.125 μg/mL against E.coli) lacks selectivity data vs. mammalian cells. Antibacterial selectivity index unknown.",
            field_source="evidence.has_selectivity_data = false",
        ),
    ]

    # ── Contradictions ────────────────────────────────────────────────────
    program.contradictions = [
        Contradiction(
            id="contra_001",
            compound="Compound-14",
            your_value=32.0, your_unit="nM", your_condition="E. coli ATCC 25922 GyrA inhibition",
            lit_range_low=750, lit_range_high=1200, lit_median=890.0,
            fold_difference=27.8,
            pmids=["37104821","36892011","38291044"],
            explanations=[
                "1. Novel scaffold may have different binding mode vs. classic quinolones (most likely)",
                "2. Cell-based vs. biochemical assay difference — MIC vs. enzyme IC50",
                "3. Assay artifact: DMSO concentration difference affecting enzyme activity",
            ],
            recommended_action="Confirm with matched biochemical enzyme inhibition assay for direct comparison with published quinolone IC50s",
            is_likely_artifact=False,
            is_potentially_novel=True,
        ),
    ]

    # ── Epistemic gaps ────────────────────────────────────────────────────
    program.epistemic_gaps = [
        EpistemicGap(
            id="gap_001",
            query="GyrA D87N × Compound-14 × E.coli",
            gene="GyrA", compound="Compound-14", condition="E. coli resistant isolates",
            intersection_paper_count=0, gene_paper_count=412,
            classification="white_space", novelty_score=0.0,
            viability_signal="GyrA highly expressed in E. coli — biological viability confirmed",
            guidance="Zero published studies on Compound-14 scaffold × gyrA D87N. Genuine white space — your 64× fold-shift data is novel. First validation experiment would be highly publishable.",
        ),
        EpistemicGap(
            id="gap_002",
            query="GyrA × fluoroquinolone resistance × efflux pump cross-resistance",
            gene="GyrA", compound="fluoroquinolone class", condition="AcrAB-TolC upregulation",
            intersection_paper_count=8, gene_paper_count=412,
            classification="emerging", novelty_score=0.39,
            viability_signal="Strong mechanistic precedent (Poole 2000, Higgins 2003)",
            guidance="8 papers exist on efflux pump cross-resistance but none with your specific Compound-14 scaffold. Differentiation possible if novel scaffold evades AcrAB-TolC.",
        ),
        EpistemicGap(
            id="gap_003",
            query="DNA gyrase inhibitor × GyrA D87N × in vivo murine",
            gene="GyrA", compound="gyrase inhibitor class", condition="murine infection model",
            intersection_paper_count=3, gene_paper_count=412,
            classification="emerging", novelty_score=0.15,
            viability_signal="Murine thigh infection model established (Craig 1998 methods)",
            guidance="Limited in vivo data for GyrA D87N resistant strains. Once mechanism is confirmed, this is the critical gap before IND.",
        ),
    ]

    # ── Literature ────────────────────────────────────────────────────────
    program.literature = [
        LiteratureResult(
            pmid="37104821",
            title="Quinolone scaffold activity against E.coli GyrA D87N mutants",
            authors="Chen X et al.", journal="J Med Chem", year=2023,
            abstract="Classic quinolone-based compounds showed IC50 > 890 nM against GyrA D87N in cell-free enzyme assay. The D87N mutation disrupts the Mg²⁺-water bridge critical for quinolone binding.",
            relevance_score=0.95, triggered_by="GyrA",
            quantitative_claims=[{"ic50": 890, "unit": "nM", "target": "GyrA D87N"}],
        ),
        LiteratureResult(
            pmid="36892011",
            title="Structural basis of fluoroquinolone resistance in E. coli gyrase",
            authors="Blanco D et al.", journal="Nature Commun", year=2022,
            abstract="Crystal structure of GyrA D87N shows altered active site geometry. Compounds binding via Mg²⁺ chelation show 600–1200× reduced activity. Non-chelating scaffolds may retain activity.",
            relevance_score=0.91, triggered_by="gyrA D87N",
            quantitative_claims=[{"ic50": 900, "unit": "nM", "target": "GyrA D87N"}],
        ),
        LiteratureResult(
            pmid="32217743",
            title="Frequency of fluoroquinolone resistance in clinical E. coli isolates",
            authors="Piddock LJ et al.", journal="AAC", year=2020,
            abstract="gyrA D87N detected in 34% of fluoroquinolone-resistant E. coli clinical isolates in EU. AcrAB-TolC efflux co-selection observed in 67% of resistant isolates.",
            relevance_score=0.82, triggered_by="resistance_mutations",
        ),
        LiteratureResult(
            pmid="30110579",
            title="Novel non-chelating gyrase inhibitors bypass resistance mutations",
            authors="Mayer C et al.", journal="JACS", year=2023,
            abstract="Compounds targeting GyrB rather than GyrA QRDR retain activity against D87N/S83L mutants. Novel binding mode confirmed by SPR.",
            relevance_score=0.88, triggered_by="GyrA D87N bypass",
        ),
    ]

    # ── Actions ───────────────────────────────────────────────────────────
    program.ranked_actions = [
        DrugProgramAction(
            rank=1, category="experiment",
            action="Characterize resistance mechanism: efflux assay + enzyme inhibition for gyrA D87N",
            rationale="64× MIC fold-shift mechanism unknown — cannot design counter-strategy without knowing if efflux or target mutation drives resistance",
            evidence_ref="audit_003",
            urgency="blocking", stage_gate=True,
            estimated_cost_usd=12000, estimated_weeks=6,
            cro_type="Microbiology CRO (e.g. IHMA, Micromyx)",
        ),
        DrugProgramAction(
            rank=2, category="experiment",
            action="Validate gyrA D87N impact via purified enzyme inhibition assay",
            rationale="Compound-14 IC50 32nM vs WT vs 890nM published for classic quinolones — need enzyme-level confirmation that scaffold retains activity vs D87N mutant",
            evidence_ref="contra_001",
            urgency="high", stage_gate=True,
            estimated_cost_usd=8000, estimated_weeks=4,
            cro_type="Biochemistry CRO (e.g. Reaction Biology, BPS Bioscience)",
        ),
        DrugProgramAction(
            rank=3, category="experiment",
            action="Run MIC assay across ≥5 clinical isolates including AcrAB-TolC overexpressing strains",
            rationale="Only 2 resistant strains tested (n=1 each) — gyrA D87N in 34% of FQ-resistant clinical isolates; scope unknown",
            evidence_ref="audit_002",
            urgency="high", stage_gate=False,
            estimated_cost_usd=5000, estimated_weeks=3,
            cro_type="Microbiology CRO with ESKAPE panel (e.g. IHMA)",
        ),
        DrugProgramAction(
            rank=4, category="experiment",
            action="Perform docking simulation: Compound-14 vs GyrA D87N crystal structure (PDB: 2XCT)",
            rationale="Structural hypothesis needed — if non-chelating binding mode (as suggested by novel scaffold), may bypass D87N resistance completely",
            evidence_ref="gap_001",
            urgency="medium", stage_gate=False,
            estimated_cost_usd=3000, estimated_weeks=2,
            cro_type="Computational CRO or internal bioinformatics (Vina + AutoSite)",
        ),
        DrugProgramAction(
            rank=5, category="manufacturing",
            action="Request small-scale synthesis feasibility from medicinal chemistry CRO",
            rationale="4-step route appears tractable — confirm yield and scalability before investing in broader SAR",
            evidence_ref="evidence.has_synthesis_route",
            urgency="medium", stage_gate=False,
            estimated_cost_usd=25000, estimated_weeks=8,
            cro_type="Medicinal chemistry CRO (e.g. WuXi Chemistry, Pharmaron, Enamine)",
        ),
        DrugProgramAction(
            rank=6, category="funding",
            action="Apply to BARDA CARB-X for AMR drug discovery funding (next cycle opens Q3 2026)",
            rationale="Compound-14 vs gyrA-resistant E. coli directly fits CARB-X AMR mandate — up to $2M for mechanism characterization + in vivo POC",
            evidence_ref="execution.grant_opportunities",
            urgency="medium", stage_gate=False,
            estimated_cost_usd=0, estimated_weeks=16,
            cro_type="Grant writing + program management",
        ),
    ]

    # ── Key findings ──────────────────────────────────────────────────────
    program.key_finding = (
        "Compound-14 (IC50 32nM) active against WT GyrA but shows 64× resistance fold-shift "
        "in gyrA D87N E.coli strain — mechanism unknown, structural class may bypass resistance."
    )
    program.blocking_question = (
        "Does Compound-14 retain GyrA enzyme inhibition against the D87N mutant, "
        "or is the 64× MIC fold-shift driven by efflux?"
    )

    # ── Execution guidance ────────────────────────────────────────────────
    program.execution = ExecutionGuidance(
        cro_needs=[
            CRONeed(need="Resistance mechanism (efflux vs target)", assay_type="microbiology",
                cro_examples=["IHMA","Micromyx","Eurofins DPMK"], urgency="blocking",
                estimated_cost_usd=12000, estimated_weeks=6),
            CRONeed(need="Enzyme inhibition assay (WT + D87N)", assay_type="biochemical",
                cro_examples=["Reaction Biology","BPS Bioscience","Carna Biosciences"],
                urgency="high", estimated_cost_usd=8000, estimated_weeks=4),
            CRONeed(need="Mammalian cytotoxicity (HepG2, Vero)", assay_type="cell_biology",
                cro_examples=["Eurofins","Charles River","Cyprotex"],
                urgency="high", estimated_cost_usd=4000, estimated_weeks=3),
            CRONeed(need="ADMET panel (solubility, stability, Caco-2)", assay_type="adme",
                cro_examples=["Cyprotex","QPS","SGS"],
                urgency="medium", estimated_cost_usd=12000, estimated_weeks=6),
        ],
        bioinformatics_needs=[
            "WGS of E.coli strain X → identify all resistance mutations (tools: samtools + BWA + GATK4)",
            "Structural docking: Compound-14 vs GyrA D87N (PDB: 2XCT) — tools: Vina + AutoSite",
            "Cross-pathogen conservation: GyrA QRDR across E.coli, K.pneumoniae, P.aeruginosa (MAFFT + FastTree)",
            "Efflux pump gene expression: AcrAB-TolC in strain X vs WT (RNA-seq differential expression)",
        ],
        grant_opportunities=[
            FundingOpportunity(name="BARDA CARB-X", amount="Up to $2M", mechanism="BARDA",
                fit_rationale="AMR drug discovery — Compound-14 vs resistant E. coli directly fits mandate",
                url="https://carb-x.org"),
            FundingOpportunity(name="NIH R21 (Exploratory Research)", amount="$275K/2yr", mechanism="NIH",
                fit_rationale="Mechanism of resistance study — NIAID DMID Study Section",
                url="https://grants.nih.gov"),
            FundingOpportunity(name="NIAID DMID contract", amount="Variable", mechanism="NIAID",
                fit_rationale="Antimicrobial drug development including hit-to-lead"),
        ],
        estimated_next_milestone_weeks=8,
        estimated_cost_next_phase_usd=25000,
        team_gaps=[
            "Microbiology expertise for resistance mechanism assays",
            "Structural bioinformatics for docking analysis",
            "Medicinal chemistry for SAR iteration",
        ],
    )

    # ── Agent trace ───────────────────────────────────────────────────────
    program.agent_trace = [
        {"step":1,"agent":"VCF Parser","action":"VCF parsing",
         "finding":"3 variants in gyrA/parC — D87N (CADD 28.4), S80I (CADD 22.1), T80A","source":"vcf"},
        {"step":2,"agent":"CSV Parser (Resistance)","action":"Resistance MIC parsing",
         "finding":"7 MIC values, 2 resistant strains, 64× fold-shift, n=1 replicates","source":"csv"},
        {"step":3,"agent":"CSV Parser (Screen)","action":"Compound screen parsing",
         "finding":"7 compounds, 3 TOP_HIT, lead: Compound-14 (IC50 32nM, MIC 0.125 μg/mL)","source":"csv"},
        {"step":4,"agent":"Universal Parser","action":"DrugProgram assembled",
         "finding":"Target: GyrA / E.coli, compound: Compound-14, evidence completeness: 30%","source":"schema"},
        {"step":5,"agent":"StageClassifier","action":"Stage classification",
         "finding":"Resistance Mechanism Characterization (93% confidence, heuristic)","source":"evidence"},
        {"step":6,"agent":"AssumptionAuditor","action":"Assumption audit",
         "finding":"4 flags (2 HIGH): no vehicle control, resistance mechanism not characterized","source":"audit"},
        {"step":7,"agent":"LiteratureAgent","action":"Literature retrieval",
         "finding":"4 papers — gyrA D87N + quinolone resistance mechanism","source":"lit"},
        {"step":8,"agent":"ContradictionDetector","action":"Contradiction detected",
         "finding":"Compound-14 IC50 32nM vs published 890nM for classic quinolones — 27.8× (novel scaffold may explain)","source":"contradiction"},
        {"step":9,"agent":"EpistemicGapMapper","action":"Knowledge frontier mapped",
         "finding":"WHITE SPACE: GyrA D87N × Compound-14 × E.coli = 0 published studies","source":"gap"},
        {"step":10,"agent":"TranslationalAgent","action":"Translational feasibility",
         "finding":"4-step synthesis tractable, CDMO not ready, 4 blocking evidence gaps, CARB-X fit","source":"manufacturing"},
        {"step":11,"agent":"ActionGenerator","action":"Action plan generated",
         "finding":"6 ranked actions — blocking: characterize resistance mechanism (efflux vs target)","source":"reason"},
    ]

    return program
