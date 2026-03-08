"""
AIDEN-AMP Core Data Models
ProgramState is the canonical object that flows through all three layers.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


class WorkflowStage(str, Enum):
    UNKNOWN = "unknown"
    TARGET_IDENTIFICATION = "target_identification"
    HIT_DISCOVERY = "hit_discovery"
    RESISTANCE_MECHANISM_CHARACTERIZATION = "resistance_mechanism_characterization"
    EXPERIMENTAL_VALIDATION = "experimental_validation"
    PRECLINICAL_GAP_ANALYSIS = "preclinical_gap_analysis"
    MANUFACTURING_FEASIBILITY = "manufacturing_feasibility"


class EvidenceStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass
class MICEntry:
    compound: str
    organism: str
    mic_value: float
    unit: str = "µg/mL"
    method: Optional[str] = None
    source: Optional[str] = None


@dataclass
class ResistanceGene:
    gene_name: str
    mechanism: Optional[str] = None
    drug_class: Optional[str] = None
    card_accession: Optional[str] = None
    prevalence: Optional[str] = None


@dataclass
class Compound:
    name: str
    cid: Optional[str] = None          # PubChem CID
    smiles: Optional[str] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    hbd: Optional[int] = None          # H-bond donors
    hba: Optional[int] = None          # H-bond acceptors
    drug_likeness_score: Optional[float] = None
    mic_entries: list = field(default_factory=list)
    toxicity_flags: list = field(default_factory=list)


@dataclass
class Protocol:
    title: str
    doi: Optional[str] = None
    url: Optional[str] = None
    steps_summary: Optional[str] = None
    controls: list = field(default_factory=list)
    materials: list = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class ExperimentRecommendation:
    rank: int
    experiment_type: str
    rationale: str
    protocol: Optional[Protocol] = None
    missing_controls: list = field(default_factory=list)
    bioinformatics_steps: list = field(default_factory=list)
    expected_output: Optional[str] = None
    priority: str = "medium"  # low / medium / high / critical


@dataclass
class FundingTarget:
    program_name: str
    agency: str
    fit_score: float  # 0-1
    stage_match: bool = False
    eligibility_gaps: list = field(default_factory=list)
    url: Optional[str] = None
    award_size: Optional[str] = None


@dataclass
class TranslationalReadiness:
    cdmo_readiness_score: float = 0.0      # 0-100
    evidence_completeness_score: float = 0.0
    scale_up_blockers: list = field(default_factory=list)
    missing_ind_studies: list = field(default_factory=list)
    qidp_eligible: Optional[bool] = None
    fast_track_eligible: Optional[bool] = None
    lpad_eligible: Optional[bool] = None
    fda_pathway: Optional[str] = None
    cro_partner_type: Optional[str] = None
    formulation_data_present: bool = False
    in_vivo_data_present: bool = False


@dataclass
class ProgramState:
    """
    The canonical state object passed between all three layers.
    Built by Layer 1, enriched by Layer 2, executed on by Layer 3.
    """
    # Identity
    session_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Detected context
    stage: WorkflowStage = WorkflowStage.UNKNOWN
    organism: Optional[str] = None
    target_gene: Optional[str] = None
    project_summary: Optional[str] = None

    # Extracted evidence
    resistance_genes: list = field(default_factory=list)   # List[ResistanceGene]
    compounds: list = field(default_factory=list)           # List[Compound]
    mic_data: list = field(default_factory=list)            # List[MICEntry]

    # Input sources present
    has_assay_csv: bool = False
    has_variant_file: bool = False
    has_paper_pdf: bool = False
    has_compound_screen: bool = False
    has_free_text: bool = False

    # Quality signals
    evidence_strength: EvidenceStrength = EvidenceStrength.WEAK
    missing_flags: list = field(default_factory=list)
    data_quality_notes: list = field(default_factory=list)

    # Layer 2 outputs
    experiment_recommendations: list = field(default_factory=list)   # List[ExperimentRecommendation]
    hypothesis_card: Optional[str] = None
    literature_context: list = field(default_factory=list)

    # Layer 3 outputs
    funding_targets: list = field(default_factory=list)               # List[FundingTarget]
    translational_readiness: Optional[TranslationalReadiness] = None
    execution_brief: Optional[str] = None

    def to_dict(self) -> dict:
        import dataclasses
        def _convert(obj):
            if dataclasses.is_dataclass(obj):
                return {k: _convert(v) for k, v in dataclasses.asdict(obj).items()}
            elif isinstance(obj, list):
                return [_convert(i) for i in obj]
            elif isinstance(obj, Enum):
                return obj.value
            return obj
        return _convert(self)
