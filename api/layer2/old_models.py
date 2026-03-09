"""
Data structures for the bio research pipeline.

These are intentionally kept separate so other teams can modify them without
touching pipeline logic or prompts. Add or remove fields here and update the
corresponding JSON schema in prompts.py accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvidenceGrade(str, Enum):
    """GRADE-inspired evidence grading for scientific recommendations."""
    HIGH        = "HIGH"        # consistent, mechanistically understood, replicated
    MODERATE    = "MODERATE"    # plausible mechanism, some replication
    LOW         = "LOW"         # mechanistic hypothesis, limited empirical support
    VERY_LOW    = "VERY_LOW"    # speculative, model-based, or single observation
    CONFLICTING = "CONFLICTING" # evidence points in multiple directions


# ---------------------------------------------------------------------------
# Input context
# ---------------------------------------------------------------------------

@dataclass
class BioResearchContext:
    """
    All user-provided biological data plus RAG-fetched documents.
    Pipeline does not implement loading or retrieval — populate externally.
    """
    research_papers:         list[dict[str, Any]] = field(default_factory=list)
    assay_data:              list[dict[str, Any]] = field(default_factory=list)
    genomics_data:           list[dict[str, Any]] = field(default_factory=list)
    compound_screen_results: list[dict[str, Any]] = field(default_factory=list)
    bioinformatics_data:     list[dict[str, Any]] = field(default_factory=list)
    rag_documents:           list[dict[str, Any]] = field(default_factory=list)
    # Q&A pairs injected by the pipeline across iterations (do not set manually)
    resolved_questions:      list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Output components
# ---------------------------------------------------------------------------

@dataclass
class Hypothesis:
    statement:        str
    mechanism:        str            # mechanistic chain: receptor → pathway → effector → phenotype
    predictions:      list[str]      # concrete, falsifiable predictions
    supporting_refs:  list[str]      # titles/keys from provided papers or RAG docs only
    evidence_grade:   EvidenceGrade
    confidence:       float          # 0.0–1.0
    counter_evidence: list[str]      # known findings that complicate this hypothesis


@dataclass
class ExperimentDesign:
    title:                 str
    rationale:             str
    hypothesis:            str
    falsifiability:        str       # what result would disprove the hypothesis
    experimental_arms:     list[dict[str, str]]   # [{"arm": ..., "description": ...}]
    positive_controls:     list[dict[str, str]]   # [{"control": ..., "rationale": ...}]
    negative_controls:     list[dict[str, str]]
    constant_variables:    list[str]
    confounders_addressed: list[str]
    primary_endpoint:      str
    secondary_endpoints:   list[str]
    statistical_approach:  str
    sample_size_rationale: str
    evidence_grade:        EvidenceGrade
    confidence:            float


@dataclass
class StudyPriority:
    rank:                 int
    study_description:    str
    scientific_rationale: str
    expected_impact:      str        # which gap this closes
    dependencies:         list[str]  # what must complete first
    risk_assessment:      str
    confidence:           float


@dataclass
class BioinformaticsAnalysis:
    analysis_type:      str          # e.g. "differential expression", "variant enrichment"
    tools_suggested:    list[str]
    rationale:          str
    input_requirements: list[str]
    expected_outputs:   list[str]
    caveats:            list[str]
    confidence:         float


@dataclass
class ClarificationQuestion:
    """A targeted scientific question the pipeline cannot resolve from data alone."""
    question:             str
    why_needed:           str        # which downstream decision this unlocks
    option_a:             str        # concrete option A
    option_b:             str        # concrete option B
    impact_if_unresolved: str        # what the pipeline will assume if unanswered


# ---------------------------------------------------------------------------
# Pipeline I/O
# ---------------------------------------------------------------------------

@dataclass
class PipelineOutput:
    iteration:               int
    status:                  str    # "final" | "needs_clarification" | "forced_output" | "pending"
    needs_clarification:     bool
    overall_confidence:      float
    divergence_flags:        list[str]
    pipeline_notes:          list[str]
    reasoning_trace:         str    # full chain-of-thought — scientific audit trail
    hypotheses:              list[Hypothesis]
    experiment_designs:      list[ExperimentDesign]
    study_priorities:        list[StudyPriority]
    bioinformatics_analyses: list[BioinformaticsAnalysis]
    clarification_questions: list[ClarificationQuestion]


@dataclass
class PipelineState:
    """Mutable state carried across iterations. Not exposed externally."""
    iteration:            int = 0
    prior_outputs:        list[PipelineOutput]        = field(default_factory=list)
    cumulative_questions: list[ClarificationQuestion] = field(default_factory=list)
    resolved_qa:          list[dict[str, str]]        = field(default_factory=list)
    clarification_rounds: int  = 0
    converged:            bool = False