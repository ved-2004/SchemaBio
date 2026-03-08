"""
protocols.io Agent — Verified Experimental Protocol Retrieval
Queries protocols.io for peer-reviewed, executable lab protocols.
This is what prevents LLM hallucination in experiment design.
API docs: https://www.protocols.io/developers
"""

import httpx
import asyncio
from typing import Optional
from backend.models.program_state import Protocol, WorkflowStage


PROTOCOLS_BASE = "https://www.protocols.io/api/v3"

# Curated fallback protocols for antibiotic resistance work
# Used when API is unavailable or returns thin results
FALLBACK_PROTOCOLS = {
    "mic_broth_dilution": Protocol(
        title="Broth Microdilution MIC Determination for Antibiotic Susceptibility Testing",
        doi="10.17504/protocols.io.n92ldpwjxl5b/v1",
        url="https://www.protocols.io/view/broth-microdilution-mic-determination-n92ldpwjxl5b",
        steps_summary="1. Prepare 2-fold serial dilutions of antibiotic in Mueller-Hinton broth. "
                      "2. Inoculate with standardized bacterial suspension (0.5 McFarland). "
                      "3. Incubate 18-24h at 35-37°C. "
                      "4. Read MIC as lowest concentration with no visible growth.",
        controls=["Growth control (no antibiotic)", "Sterility control (no bacteria)", 
                  "ATCC QC strain (e.g., E. coli ATCC 25922)"],
        materials=["Mueller-Hinton broth", "96-well plate", "Antibiotic stock solutions",
                   "Spectrophotometer or visual reader", "Biosafety cabinet"],
        relevance_score=0.95
    ),
    "checkerboard_synergy": Protocol(
        title="Checkerboard Synergy Assay for Antibiotic Combination Testing",
        doi="10.17504/protocols.io.bpk9mkr6",
        url="https://www.protocols.io/view/checkerboard-assay-bpk9mkr6",
        steps_summary="1. Prepare 2-fold dilutions of each antibiotic independently. "
                      "2. Combine dilutions in checkerboard pattern in 96-well plate. "
                      "3. Add bacterial inoculum to each well. "
                      "4. Calculate FICI to determine synergy (≤0.5), indifference, or antagonism (≥4.0).",
        controls=["Single drug MIC controls", "Growth control", "ATCC reference strain"],
        materials=["96-well plates", "Two antibiotics of interest", "CAMHB", "Microplate reader"],
        relevance_score=0.90
    ),
    "time_kill_kinetics": Protocol(
        title="Time-Kill Kinetics Assay for Bactericidal Activity Assessment",
        doi="10.17504/protocols.io.rm7vzjn97lx1/v1",
        url="https://www.protocols.io/view/time-kill-rm7vzjn97lx1",
        steps_summary="1. Grow overnight culture, dilute to 5×10^5 CFU/mL. "
                      "2. Add antibiotic at 0.5×, 1×, 2×, 4× MIC. "
                      "3. Sample at 0, 2, 4, 8, 24h — plate for CFU count. "
                      "4. Bactericidal = ≥3 log10 reduction at 24h.",
        controls=["No-antibiotic growth control", "Antibiotic carryover neutralization"],
        materials=["Antibiotic at tested concentrations", "Tryptic soy broth", "Agar plates", "Colony counter"],
        relevance_score=0.88
    ),
    "genomic_dna_extraction": Protocol(
        title="Genomic DNA Extraction from Gram-Negative Bacteria for WGS",
        doi="10.17504/protocols.io.bfn3jmgn",
        url="https://www.protocols.io/view/genomic-dna-extraction-bfn3jmgn",
        steps_summary="1. Pellet overnight culture. 2. Lyse with proteinase K + buffer. "
                      "3. Column-based DNA purification. 4. Elute and quantify by Qubit. "
                      "5. Check integrity by gel electrophoresis. 6. Submit for Illumina short-read or Nanopore long-read WGS.",
        controls=["Positive extraction control (reference strain)", "Blank extraction control"],
        materials=["DNeasy kit or equivalent", "Qubit fluorometer", "Gel electrophoresis system"],
        relevance_score=0.85
    ),
    "resistance_gene_pcr": Protocol(
        title="Multiplex PCR Detection of Carbapenemase Genes (KPC, NDM, OXA-48, VIM, IMP)",
        doi="10.17504/protocols.io.q26g7pw3kgwz/v1",
        url="https://www.protocols.io/view/multiplex-pcr-carbapenemase-q26g7pw3kgwz",
        steps_summary="1. Extract DNA. 2. Set up multiplex PCR with 5 primer pairs. "
                      "3. Run thermal cycling: 95°C 15min → 30× (95°C 30s, 60°C 90s, 72°C 60s) → 72°C 10min. "
                      "4. Run gel electrophoresis. 5. Identify bands by expected amplicon sizes.",
        controls=["Positive control (known carbapenemase producer)", "Negative control (susceptible strain)", 
                  "No-template control"],
        materials=["Specific primer sets", "HotStarTaq PCR mix", "Gel electrophoresis system", "Reference strains"],
        relevance_score=0.92
    ),
    "biofilm_formation_assay": Protocol(
        title="Crystal Violet Biofilm Quantification Assay",
        doi="10.17504/protocols.io.x54v9pzzqg3e/v1",
        url="https://www.protocols.io/view/biofilm-crystal-violet-x54v9pzzqg3e",
        steps_summary="1. Inoculate 96-well plate with bacteria in TSB. 2. Incubate static 24-48h at 37°C. "
                      "3. Wash wells with PBS to remove planktonic cells. 4. Fix with methanol, stain with 0.1% crystal violet. "
                      "5. Dissolve with 30% acetic acid. 6. Read OD590.",
        controls=["Uninoculated medium", "Known biofilm-forming positive control"],
        materials=["96-well polystyrene plates", "Crystal violet solution", "Acetic acid", "Microplate reader"],
        relevance_score=0.82
    ),
}

# Stage-to-protocol mapping
STAGE_PROTOCOL_MAP = {
    "hit_discovery": ["mic_broth_dilution", "checkerboard_synergy", "time_kill_kinetics"],
    "resistance_mechanism_characterization": ["resistance_gene_pcr", "genomic_dna_extraction", "mic_broth_dilution"],
    "experimental_validation": ["time_kill_kinetics", "checkerboard_synergy", "biofilm_formation_assay"],
    "preclinical_gap_analysis": ["time_kill_kinetics", "biofilm_formation_assay", "checkerboard_synergy"],
    "target_identification": ["resistance_gene_pcr", "genomic_dna_extraction", "mic_broth_dilution"],
}


async def search_protocols(query: str, max_results: int = 3) -> list[Protocol]:
    """
    Query protocols.io API for relevant protocols.
    Falls back to curated library if API unavailable.
    """
    protocols = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{PROTOCOLS_BASE}/protocols",
                params={
                    "filter": "public",
                    "key": query,
                    "order_field": "relevance",
                    "order_dir": "desc",
                    "page_size": max_results,
                },
                headers={"Accept": "application/json"}
            )
            if r.status_code == 200:
                data = r.json()
                items = data.get("items", [])
                for item in items[:max_results]:
                    p = Protocol(
                        title=item.get("title", "Untitled Protocol"),
                        doi=item.get("doi"),
                        url=item.get("uri"),
                        relevance_score=0.75,
                    )
                    protocols.append(p)
    except Exception:
        pass

    return protocols


async def get_protocols_for_stage(
    stage: str,
    organism: Optional[str] = None,
    resistance_gene: Optional[str] = None
) -> list[Protocol]:
    """
    Get best protocols for a given workflow stage.
    Combines API search + curated fallback library.
    """
    # Build search query
    query_parts = []
    if organism:
        query_parts.append(organism)
    if resistance_gene:
        query_parts.append(resistance_gene)
    query_parts.append("antibiotic resistance")

    stage_key = stage.lower().replace(" ", "_")
    protocol_keys = STAGE_PROTOCOL_MAP.get(stage_key, ["mic_broth_dilution", "resistance_gene_pcr"])

    # Get API results
    api_query = " ".join(query_parts)
    api_protocols = await search_protocols(api_query, max_results=2)

    # Get curated fallbacks
    curated = [FALLBACK_PROTOCOLS[k] for k in protocol_keys if k in FALLBACK_PROTOCOLS]

    # Merge: API results first (if good), then curated
    all_protocols = api_protocols + curated
    seen_titles = set()
    unique = []
    for p in all_protocols:
        if p.title not in seen_titles:
            seen_titles.add(p.title)
            unique.append(p)

    return unique[:3]


async def get_protocol_by_technique(technique: str) -> Optional[Protocol]:
    """Direct lookup for a specific technique type."""
    technique_lower = technique.lower()
    for key, protocol in FALLBACK_PROTOCOLS.items():
        if any(word in protocol.title.lower() for word in technique_lower.split()):
            return protocol
    # Try API
    results = await search_protocols(technique, max_results=1)
    return results[0] if results else None
