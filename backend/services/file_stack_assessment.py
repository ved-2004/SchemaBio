"""
services/file_stack_assessment.py

Evaluates the file stack and determines progression status and downstream readiness.
Deterministic rules only; no LLM.
"""

from __future__ import annotations
import logging
from typing import Optional

from backend.models.ingestion import (
    FileStackItem,
    FileStackAssessment,
    ProgressionStatus,
)

logger = logging.getLogger(__name__)

# Categories that can "anchor" a workflow (single strong file can be enough)
ANCHOR_CATEGORIES = {
    "raw_assay_data",
    "compound_screen",
    "genomics_variants",
    "scientific_document",
    "notes_context",
}

# For recommendation text
CATEGORY_LABELS = {
    "sequencing_data": "Sequencing data (FASTQ/FASTA/BAM/SAM)",
    "genomics_variants": "Genomics/variants (VCF)",
    "raw_assay_data": "Resistance/assay data (CSV)",
    "compound_screen": "Compound screen (CSV/TSV)",
    "scientific_document": "Paper/rationale (PDF)",
    "notes_context": "Notes/target rationale (TXT/MD)",
    "unknown": "Unknown or unsupported file",
}


def _detected_categories_from_items(items: list[FileStackItem]) -> list[str]:
    return list({i.detected_category for i in items if i.detected_category and i.detected_category != "unknown"})


def _recommended_next(detected: set[str]) -> list[str]:
    """Recommend file types that would strengthen the workspace (not required)."""
    rec = []
    if "genomics_variants" not in detected and ("raw_assay_data" in detected or "compound_screen" in detected):
        rec.append(CATEGORY_LABELS.get("genomics_variants", "Genomics/variants (VCF)"))
    if "raw_assay_data" not in detected and "compound_screen" in detected:
        rec.append(CATEGORY_LABELS.get("raw_assay_data", "Resistance/assay data (CSV)"))
    if "compound_screen" not in detected and "raw_assay_data" in detected:
        rec.append(CATEGORY_LABELS.get("compound_screen", "Compound screen (CSV)"))
    if "scientific_document" not in detected and "notes_context" not in detected:
        rec.append(CATEGORY_LABELS.get("scientific_document", "Paper/rationale (PDF)"))
    return rec


def assess_file_stack(
    items: list[FileStackItem],
    entity_count: int,
    signal_count: int,
    has_stage_estimate: bool,
) -> tuple[FileStackAssessment, bool, bool]:
    """
    Evaluate file stack and return (assessment, supports_experiment_design, supports_execution_planning).
    """
    detected = set(_detected_categories_from_items(items))
    contributing = [i for i in items if i.contributes_to_readiness]
    anchor_present = any(i.detected_category in ANCHOR_CATEGORIES and i.parse_status == "complete" for i in items)
    multiple_evidence = len(detected) >= 2
    has_meaningful_content = entity_count > 0 or signal_count > 0 or has_stage_estimate

    # Blocked: no usable files
    if not items or all(i.parse_status == "error" for i in items):
        reasoning = ["No parseable files in the workspace."]
        return (
            FileStackAssessment(
                files=items,
                detected_categories=[],
                missing_required_categories=[],
                recommended_next_files=[CATEGORY_LABELS.get("raw_assay_data", "Resistance assay CSV"), CATEGORY_LABELS.get("compound_screen", "Compound screen CSV")],
                progression_status=ProgressionStatus.blocked,
                progression_reasoning=reasoning,
                supports_experiment_design=False,
                supports_execution_planning=False,
            ),
            False,
            False,
        )

    # Unknown-only: all files are unknown/unparseable
    if all(i.detected_category == "unknown" or i.parse_status == "error" for i in items):
        reasoning = ["Only unknown or unparseable files. Add resistance assay CSV, compound screen CSV, VCF, or PDF."]
        return (
            FileStackAssessment(
                files=items,
                detected_categories=[],
                missing_required_categories=[],
                recommended_next_files=list(CATEGORY_LABELS.values())[:4],
                progression_status=ProgressionStatus.blocked,
                progression_reasoning=reasoning,
                supports_experiment_design=False,
                supports_execution_planning=False,
            ),
            False,
            False,
        )

    # Needs more context: we have some anchor but weak or partial
    if anchor_present and not has_meaningful_content:
        reasoning = ["At least one file type is recognized but little context was extracted. Try a different file or add more files."]
        return (
            FileStackAssessment(
                files=items,
                detected_categories=_detected_categories_from_items(items),
                missing_required_categories=[],
                recommended_next_files=_recommended_next(detected),
                progression_status=ProgressionStatus.needs_more_context,
                progression_reasoning=reasoning,
                supports_experiment_design=False,
                supports_execution_planning=False,
            ),
            False,
            False,
        )

    # Ready: at least one strong anchor with meaningful content
    if anchor_present and has_meaningful_content:
        reasoning = ["Workspace has sufficient context to generate downstream handoffs."]
        if multiple_evidence:
            reasoning.append("Multiple evidence types present — stronger confidence.")
        supports_exp = True
        supports_exec = multiple_evidence or (signal_count >= 3 and entity_count >= 2)
        return (
            FileStackAssessment(
                files=items,
                detected_categories=_detected_categories_from_items(items),
                missing_required_categories=[],
                recommended_next_files=_recommended_next(detected),
                progression_status=ProgressionStatus.ready_for_downstream_layers,
                progression_reasoning=reasoning,
                supports_experiment_design=supports_exp,
                supports_execution_planning=supports_exec,
            ),
            supports_exp,
            supports_exec,
        )

    # Partial: we have some categories but no strong anchor with content
    reasoning = ["Add at least one of: resistance assay CSV, compound screen CSV, VCF, or target rationale PDF."]
    return (
        FileStackAssessment(
            files=items,
            detected_categories=_detected_categories_from_items(items),
            missing_required_categories=[],
            recommended_next_files=_recommended_next(detected) or [CATEGORY_LABELS.get("raw_assay_data", "Resistance assay CSV"), CATEGORY_LABELS.get("compound_screen", "Compound screen CSV")],
            progression_status=ProgressionStatus.needs_more_context,
            progression_reasoning=reasoning,
            supports_experiment_design=False,
            supports_execution_planning=False,
        ),
        False,
        False,
    )
