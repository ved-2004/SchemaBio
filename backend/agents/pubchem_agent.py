"""
PubChem Agent — Compound Property Retrieval
Fetches molecular properties, drug-likeness scoring, and toxicity flags.
Uses PubChem PUG REST API (free, no auth required).
https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""

import httpx
import asyncio
from typing import Optional
from backend.models.program_state import Compound


PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Known antibiotic compounds with pre-seeded data (fallback + enrichment)
ANTIBIOTIC_SEED = {
    "meropenem":    {"cid": "441130",  "class": "Carbapenem", "mw": 383.46, "logp": -0.1},
    "imipenem":     {"cid": "104838",  "class": "Carbapenem", "mw": 317.36, "logp": -2.9},
    "colistin":     {"cid": "5311054", "class": "Polymyxin",  "mw": 1169.0, "logp": -1.6},
    "vancomycin":   {"cid": "14969",   "class": "Glycopeptide","mw": 1449.3,"logp": -3.1},
    "linezolid":    {"cid": "441401",  "class": "Oxazolidinone","mw": 337.35,"logp": 0.9},
    "ceftazidime":  {"cid": "5481173", "class": "Cephalosporin","mw": 546.58,"logp": -1.4},
    "avibactam":    {"cid": "9835049", "class": "β-lactamase inhibitor","mw": 265.26,"logp": -3.0},
    "aztreonam":    {"cid": "5353980", "class": "Monobactam", "mw": 435.43, "logp": -0.9},
    "rifampicin":   {"cid": "135398513","class": "Rifamycin", "mw": 822.94, "logp": 2.7},
    "ciprofloxacin":{"cid": "2764",    "class": "Fluoroquinolone","mw": 331.35,"logp": 0.3},
    "daptomycin":   {"cid": "16134395","class": "Lipopeptide","mw": 1620.67,"logp": 2.2},
}


async def get_compound_properties(compound_name: str) -> Compound:
    """
    Fetch compound properties from PubChem.
    Returns Compound with MW, logP, HBD/HBA, drug-likeness score.
    """
    comp = Compound(name=compound_name)
    name_lower = compound_name.lower().strip()

    # Seed data fast-path
    seed = ANTIBIOTIC_SEED.get(name_lower)
    if seed:
        comp.cid = seed["cid"]
        comp.molecular_weight = seed["mw"]
        comp.logp = seed["logp"]

    # Try PubChem API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: Get CID by name
            if not comp.cid:
                r = await client.get(
                    f"{PUBCHEM_BASE}/compound/name/{compound_name}/cids/JSON"
                )
                if r.status_code == 200:
                    data = r.json()
                    cids = data.get("IdentifierList", {}).get("CID", [])
                    if cids:
                        comp.cid = str(cids[0])

            # Step 2: Get properties by CID
            if comp.cid:
                props = "MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,TPSA,IsomericSMILES"
                r2 = await client.get(
                    f"{PUBCHEM_BASE}/compound/cid/{comp.cid}/property/{props}/JSON"
                )
                if r2.status_code == 200:
                    p = r2.json()["PropertyTable"]["Properties"][0]
                    comp.molecular_weight = p.get("MolecularWeight", comp.molecular_weight)
                    comp.logp = p.get("XLogP", comp.logp)
                    comp.hbd = p.get("HBondDonorCount")
                    comp.hba = p.get("HBondAcceptorCount")
                    comp.smiles = p.get("IsomericSMILES")

    except Exception:
        pass  # Use seed data

    # Score drug-likeness (Lipinski Ro5, adapted for antibiotics)
    comp.drug_likeness_score = _score_drug_likeness(comp)
    comp.toxicity_flags = _flag_toxicity(comp)

    return comp


def _score_drug_likeness(comp: Compound) -> float:
    """
    Modified Lipinski Ro5 scoring for antibiotics.
    Note: Many antibiotics violate classical Ro5 — we use relaxed criteria.
    Score: 0.0 (bad) to 1.0 (ideal)
    """
    score = 1.0
    deductions = []

    if comp.molecular_weight:
        if comp.molecular_weight > 900:
            score -= 0.4    # Very large — likely peptide, bioavailability concern
            deductions.append("MW > 900: likely IV-only")
        elif comp.molecular_weight > 600:
            score -= 0.15
            deductions.append("MW > 600: bioavailability reduced")

    if comp.logp is not None:
        if comp.logp > 5:
            score -= 0.3
            deductions.append("logP > 5: high lipophilicity")
        elif comp.logp < -3:
            score -= 0.1
            deductions.append("logP < -3: poor membrane permeability")

    if comp.hbd is not None and comp.hbd > 5:
        score -= 0.15
        deductions.append("HBD > 5: absorption concern")

    if comp.hba is not None and comp.hba > 10:
        score -= 0.1
        deductions.append("HBA > 10: permeability concern")

    return max(0.0, round(score, 2))


def _flag_toxicity(comp: Compound) -> list[str]:
    """Rule-based toxicity flagging from known antibiotic safety profiles."""
    flags = []
    name_lower = comp.name.lower()

    nephrotoxicity_risk = ["colistin", "aminoglycoside", "vancomycin", "amphotericin"]
    hepatotoxicity_risk = ["rifampicin", "isoniazid", "pyrazinamide", "linezolid"]
    qt_prolongation = ["azithromycin", "clarithromycin", "moxifloxacin", "ciprofloxacin"]
    neurotoxicity = ["colistin", "metronidazole", "linezolid"]

    for compound in nephrotoxicity_risk:
        if compound in name_lower:
            flags.append("⚠ Nephrotoxicity risk — monitor creatinine/BUN")
    for compound in hepatotoxicity_risk:
        if compound in name_lower:
            flags.append("⚠ Hepatotoxicity risk — monitor LFTs")
    for compound in qt_prolongation:
        if compound in name_lower:
            flags.append("⚠ QT prolongation — ECG monitoring advised")
    for compound in neurotoxicity:
        if compound in name_lower:
            flags.append("⚠ Neurotoxicity risk — monitor for adverse neuro events")

    return flags


async def batch_get_compounds(compound_names: list[str]) -> list[Compound]:
    """Parallel compound lookup."""
    tasks = [get_compound_properties(name) for name in compound_names]
    return await asyncio.gather(*tasks)


def extract_compound_names_from_text(text: str) -> list[str]:
    """Identify antibiotic compound mentions in text."""
    known = list(ANTIBIOTIC_SEED.keys()) + [
        "amoxicillin", "ampicillin", "piperacillin", "tazobactam",
        "cefepime", "ceftriaxone", "ertapenem", "doripenem",
        "tigecycline", "fosfomycin", "trimethoprim", "sulfamethoxazole",
        "gentamicin", "tobramycin", "amikacin", "nitrofurantoin",
        "metronidazole", "clindamycin", "azithromycin", "clarithromycin",
    ]
    found = []
    text_lower = text.lower()
    for compound in known:
        if compound in text_lower:
            found.append(compound)
    return list(set(found))
