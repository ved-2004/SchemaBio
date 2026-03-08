"""
CARD Agent — Comprehensive Antibiotic Resistance Database
Queries CARD for resistance gene annotation, mechanism, and drug class mapping.
https://card.mcmaster.ca/
"""

import httpx
import asyncio
import re
from typing import Optional
from backend.models.program_state import ResistanceGene


CARD_BASE = "https://card.mcmaster.ca"

# CARD ontology term IDs for common resistance mechanisms
MECHANISM_MAP = {
    "blaKPC": {"mechanism": "carbapenemase (class A β-lactamase)", "drug_class": "Carbapenem", "family": "KPC"},
    "blaNDM": {"mechanism": "metallo-β-lactamase (class B)", "drug_class": "Carbapenem", "family": "NDM"},
    "blaOXA": {"mechanism": "oxacillinase (class D β-lactamase)", "drug_class": "β-lactam", "family": "OXA"},
    "blaVIM": {"mechanism": "metallo-β-lactamase (class B)", "drug_class": "Carbapenem", "family": "VIM"},
    "blaIMP": {"mechanism": "metallo-β-lactamase (class B)", "drug_class": "Carbapenem", "family": "IMP"},
    "mcr": {"mechanism": "phosphoethanolamine transferase — lipid A modification", "drug_class": "Colistin", "family": "MCR"},
    "vanA": {"mechanism": "D-Ala-D-Lac ligase substitution", "drug_class": "Glycopeptide/Vancomycin", "family": "van"},
    "vanB": {"mechanism": "D-Ala-D-Lac ligase substitution (inducible)", "drug_class": "Vancomycin", "family": "van"},
    "aac": {"mechanism": "aminoglycoside acetyltransferase", "drug_class": "Aminoglycoside", "family": "AAC"},
    "qnr": {"mechanism": "quinolone resistance protein — protects DNA gyrase", "drug_class": "Fluoroquinolone", "family": "Qnr"},
    "tet": {"mechanism": "tetracycline efflux pump / ribosomal protection", "drug_class": "Tetracycline", "family": "Tet"},
    "sul": {"mechanism": "dihydropteroate synthase variant", "drug_class": "Sulfonamide", "family": "Sul"},
    "ermB": {"mechanism": "rRNA methyltransferase — 23S rRNA modification", "drug_class": "Macrolide/MLSB", "family": "Erm"},
    "cfr": {"mechanism": "rRNA methyltransferase — 23S rRNA modification", "drug_class": "Oxazolidinone/Phenicol", "family": "Cfr"},
}

# Known ESKAPE pathogens
ESKAPE_ORGANISMS = {
    "enterococcus faecium": "ESKAPE",
    "staphylococcus aureus": "ESKAPE",
    "klebsiella pneumoniae": "ESKAPE / Priority 1 (WHO)",
    "acinetobacter baumannii": "ESKAPE / Priority 1 (WHO)",
    "pseudomonas aeruginosa": "ESKAPE / Priority 1 (WHO)",
    "enterobacter": "ESKAPE",
    "escherichia coli": "Priority 1 (WHO)",
}


async def query_card_gene(gene_name: str) -> ResistanceGene:
    """
    Query CARD for a resistance gene. Falls back to local map if API unavailable.
    CARD's public API is at https://card.mcmaster.ca/aro/search
    """
    gene = ResistanceGene(gene_name=gene_name)

    # 1. Try local lookup first (fast, reliable for demo)
    gene_upper = gene_name.upper()
    gene_lower = gene_name.lower()
    for key, val in MECHANISM_MAP.items():
        if key.lower() in gene_lower or gene_lower in key.lower():
            gene.mechanism = val["mechanism"]
            gene.drug_class = val["drug_class"]
            break

    # 2. Try CARD API
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            # CARD search endpoint
            r = await client.get(
                f"{CARD_BASE}/aro/search",
                params={"query": gene_name, "format": "json"}
            )
            if r.status_code == 200:
                data = r.json()
                if data and isinstance(data, list) and len(data) > 0:
                    top = data[0]
                    gene.card_accession = top.get("accession")
                    if not gene.mechanism:
                        gene.mechanism = top.get("name", "")
    except Exception:
        # API unavailable — local map already set above
        pass

    # 3. Assign prevalence signal based on WHO priority
    if any(fam in gene_lower for fam in ["blaKPC", "blaNDM", "blaOXA-48", "mcr"]):
        gene.prevalence = "High — globally disseminated"
    elif any(fam in gene_lower for fam in ["vanA", "vanB"]):
        gene.prevalence = "Moderate — primarily hospital-acquired"
    else:
        gene.prevalence = "Variable — regional surveillance data recommended"

    return gene


async def annotate_genes_from_list(gene_names: list[str]) -> list[ResistanceGene]:
    """Parallel annotation of multiple genes."""
    tasks = [query_card_gene(g) for g in gene_names]
    return await asyncio.gather(*tasks)


def extract_gene_names_from_text(text: str) -> list[str]:
    """
    Regex-based extraction of resistance gene mentions from free text or PDF.
    Matches patterns like: blaKPC-2, vanA, mcr-1, blaNDM-5, ermB
    """
    patterns = [
        r'\bbla[A-Z]{2,6}[-_]?\d*\b',   # β-lactamases: blaKPC-2, blaNDM-5
        r'\bvan[A-Z]\b',                  # Glycopeptide: vanA, vanB
        r'\bmcr-?\d\b',                   # Colistin: mcr-1, mcr-2
        r'\berm[A-Z0-9]+\b',              # MLSB: ermB, ermA
        r'\btet[A-Z0-9()\-]+\b',          # Tetracycline: tetA, tet(M)
        r'\bqnr[A-Z]\d?\b',               # Quinolone: qnrA, qnrB
        r'\baac\([0-9\'\"]+\)-[A-Za-z]+', # Aminoglycoside: aac(6')-Ib
        r'\bsul[0-9]\b',                  # Sulfonamide: sul1, sul2
        r'\bcfr[A-Z]?\b',                 # Oxazolidinone: cfr, cfrB
    ]
    found = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.update(matches)
    return list(found)


def get_organism_priority(organism_name: str) -> Optional[str]:
    """Check if organism is in ESKAPE / WHO priority list."""
    org_lower = organism_name.lower()
    for key, val in ESKAPE_ORGANISMS.items():
        if key in org_lower or org_lower in key:
            return val
    return None
