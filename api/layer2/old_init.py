"""
Layer 2 — Bio Research Pipeline

Public API for downstream consumers (FastAPI routes, notebooks, etc.).
Import from here, not from individual submodules.
"""

from .models import (
    BioResearchContext,
    BioinformaticsAnalysis,
    ClarificationQuestion,
    EvidenceGrade,
    ExperimentDesign,
    Hypothesis,
    PipelineOutput,
    PipelineState,
    StudyPriority,
)
from .pipeline import BioResearchPipeline, print_pipeline_output

__all__ = [
    # Pipeline
    "BioResearchPipeline",
    "print_pipeline_output",
    # Input
    "BioResearchContext",
    # Output components
    "PipelineOutput",
    "PipelineState",
    "Hypothesis",
    "ExperimentDesign",
    "StudyPriority",
    "BioinformaticsAnalysis",
    "ClarificationQuestion",
    "EvidenceGrade",
]
