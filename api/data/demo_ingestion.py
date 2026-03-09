"""
data/demo_ingestion.py

Fully mocked antibiotic resistance demo IngestionResponse for GET /api/demo-ingestion.
Matches the exact ingestion contract; no real parsing.
"""

from ..models.ingestion import (
    IngestionResponse,
    ProgramState,
    ExperimentDesignInput,
    ExecutionPlanningInput,
    UploadedFileDescriptor,
    ExtractedEntity,
    ExtractedSignal,
    StageEstimate,
    EvidenceBundle,
)


def get_demo_ingestion_response() -> IngestionResponse:
    """Return a complete mocked ingestion response for the antibiotic resistance demo."""
    return IngestionResponse(
        program_state=ProgramState(
            program_id="DEMO01",
            status="ok",
            uploaded_files=[
                UploadedFileDescriptor(
                    file_id="file_gyrase_resistance_1",
                    filename="gyrase_resistance.csv",
                    detected_type="Resistance Assay CSV",
                    schema_confidence=0.96,
                    parse_status="complete",
                    extracted_fields=["strain_id", "compound_name", "mic", "fold_shift", "replicate", "assay_type"],
                    warnings=[],
                ),
                UploadedFileDescriptor(
                    file_id="file_compound14_2",
                    filename="compound14_screen.csv",
                    detected_type="Compound Screen CSV",
                    schema_confidence=0.94,
                    parse_status="complete",
                    extracted_fields=["compound_name", "ic50", "z_score", "hit_flag", "target"],
                    warnings=[],
                ),
                UploadedFileDescriptor(
                    file_id="file_gyra_variants_3",
                    filename="gyra_variants.vcf",
                    detected_type="Genomics / VCF",
                    schema_confidence=0.91,
                    parse_status="complete",
                    extracted_fields=["chrom", "pos", "ref", "alt", "gene", "impact", "clinvar"],
                    warnings=[],
                ),
                UploadedFileDescriptor(
                    file_id="file_target_rationale_4",
                    filename="target_rationale.pdf",
                    detected_type="Research Notes / PDF",
                    schema_confidence=0.72,
                    parse_status="complete",
                    extracted_fields=["title", "target references", "organism references", "drug class", "mechanism keywords"],
                    warnings=["No target or organism references extracted from PDF"],
                ),
            ],
            entities=[
                ExtractedEntity(type="organism", value="E. coli (ATCC 25922 + clinical isolates)", source="gyrase_resistance.csv", confidence=0.97),
                ExtractedEntity(type="target", value="GyrA", source="gyra_variants.vcf", confidence=0.98),
                ExtractedEntity(type="variant", value="GyrA D87N", source="gyra_variants.vcf", confidence=0.95),
                ExtractedEntity(type="variant", value="parC S80I", source="gyra_variants.vcf", confidence=0.93),
                ExtractedEntity(type="compound", value="Compound-14", source="compound14_screen.csv", confidence=0.96),
                ExtractedEntity(type="assay_type", value="MIC", source="gyrase_resistance.csv", confidence=0.99),
                ExtractedEntity(type="compound", value="Compound-31", source="compound14_screen.csv", confidence=0.88),
            ],
            signals=[
                ExtractedSignal(kind="resistance_fold_shift", value=64, unit="×", source="gyrase_resistance.csv"),
                ExtractedSignal(kind="compound_hit", value="Compound-14", source="compound14_screen.csv"),
                ExtractedSignal(kind="lead_ic50_nm", value=32, unit="nM", source="compound14_screen.csv"),
                ExtractedSignal(kind="top_hit_count", value=3, source="compound14_screen.csv"),
                ExtractedSignal(kind="variant_count", value=3, unit="variants", source="gyra_variants.vcf"),
                ExtractedSignal(kind="resistance_associated_variant", value="GyrA D87N", source="gyra_variants.vcf"),
            ],
            stage_estimate=StageEstimate(
                name="resistance_mechanism_characterization",
                confidence=0.93,
                reasoning_basis=[
                    "Variant data + resistance assay + compound hit data present.",
                    "Mechanism characterization is the natural next step.",
                ],
            ),
            missing_data_flags=[
                "no_vehicle_control_detected",
                "no_reproducibility_summary_detected",
                "no_target_engagement_data_detected",
                "no_admet_data_detected",
                "no_manufacturability_data_detected",
            ],
            warnings=[
                "No vehicle/DMSO control in compound screen",
                "Single replicate (n=1) detected",
            ],
            evidence_index={
                "file_gyrase_resistance_1": ["E. coli", "MIC", "64"],
                "file_compound14_2": ["Compound-14", "32", "compound_hit:Compound-14"],
                "file_gyra_variants_3": ["GyrA", "GyrA D87N", "resistance_associated_variant:GyrA D87N"],
                "file_target_rationale_4": [],
            },
        ),
        experiment_design_input=ExperimentDesignInput(
            stage="resistance_mechanism_characterization",
            stage_confidence=0.93,
            biological_context="E. coli (ATCC 25922 + clinical isolates); GyrA; GyrA D87N; parC S80I; Compound-14; MIC",
            assay_context=["MIC"],
            priority_signals=[
                ExtractedSignal(kind="resistance_fold_shift", value=64, unit="×"),
                ExtractedSignal(kind="compound_hit", value="Compound-14", source="compound14_screen.csv"),
            ],
            missing_experiment_context=[
                "Efflux vs target mutation mechanism",
                "MIC across ≥5 strains including WT",
                "Time-kill kinetics",
                "Enzyme inhibition (WT vs D87N)",
            ],
            evidence_bundle=EvidenceBundle(
                literature_refs=["37104821", "36892011", "32217743", "30110579"],
                quantitative_claims=[
                    {"type": "IC50", "value": 890, "unit": "nM", "target": "GyrA D87N (published quinolone)"},
                    {"type": "IC50", "value": 32, "unit": "nM", "target": "Compound-14 (this program)"},
                ],
                audit_refs=["audit_001", "audit_002"],
                gap_refs=["gap_001", "gap_002"],
                file_refs=["file_gyrase_resistance_1", "file_compound14_2", "file_gyra_variants_3", "file_target_rationale_4"],
            ),
        ),
        execution_planning_input=ExecutionPlanningInput(
            stage="resistance_mechanism_characterization",
            stage_confidence=0.93,
            program_summary="Program DEMO01. Stage: resistance_mechanism_characterization (confidence 93%). Gyrase inhibitor program (Compound-14) vs gyrA D87N E. coli. 64× resistance fold-shift; mechanism unknown. Evidence completeness ~30%; GMP readiness ~20%.",
            development_signals=[
                ExtractedSignal(kind="synthesis_steps", value=4, unit="steps"),
                ExtractedSignal(kind="evidence_completeness_pct", value=30, unit="%"),
                ExtractedSignal(kind="gmp_readiness_pct", value=20, unit="%"),
            ],
            missing_development_inputs=[
                "no_vehicle_control_detected",
                "no_reproducibility_summary_detected",
                "no_target_engagement_data_detected",
                "no_admet_data_detected",
                "no_manufacturability_data_detected",
            ],
            readiness_constraints=[
                "CDMO not ready until ADMET + reproducibility package complete",
                "BARDA CARB-X fit for AMR discovery — up to $2M",
            ],
            evidence_bundle=EvidenceBundle(
                literature_refs=["37104821", "36892011"],
                quantitative_claims=[
                    {"type": "IC50", "value": 890, "unit": "nM", "target": "GyrA D87N (published)"},
                    {"type": "IC50", "value": 32, "unit": "nM", "target": "Compound-14"},
                ],
                file_refs=["file_gyrase_resistance_1", "file_compound14_2", "file_gyra_variants_3", "file_target_rationale_4"],
            ),
        ),
    )
