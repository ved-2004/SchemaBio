"""
LAYER 1 — Ingestion + Scientific State Builder
=========================================================
Takes raw user inputs (CSV, VCF, PDF, text) and produces
a structured ProgramState with detected workflow stage,
extracted evidence, and missing-data flags.

This layer is DETERMINISTIC. No LLM hallucination here.
Every output is derived from parsed data or validated rules.
"""

import csv
import io
import re
import uuid
import json
from typing import Optional
from pathlib import Path

from backend.models.program_state import (
    ProgramState, WorkflowStage, EvidenceStrength,
    MICEntry, ResistanceGene, Compound
)
from backend.agents.card_agent import extract_gene_names_from_text, get_organism_priority
from backend.agents.pubchem_agent import extract_compound_names_from_text


# ─────────────────────────────────────────────
# Stage detection rules
# ─────────────────────────────────────────────

STAGE_SIGNALS = {
    WorkflowStage.TARGET_IDENTIFICATION: [
        "target", "mechanism", "pathway", "virulence", "gene function",
        "protein structure", "binding site", "druggable"
    ],
    WorkflowStage.HIT_DISCOVERY: [
        "screen", "hit", "compound library", "ic50", "mic", "activity",
        "scaffold", "fragment", "high-throughput"
    ],
    WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION: [
        "resistance", "resistant", "bla", "van", "mcr", "carbapenem",
        "mechanism", "gene", "variant", "mutation", "efflux", "enzyme"
    ],
    WorkflowStage.EXPERIMENTAL_VALIDATION: [
        "validate", "confirm", "in vivo", "mouse model", "infection model",
        "efficacy", "pk/pd", "pharmacokinetics", "dose"
    ],
    WorkflowStage.PRECLINICAL_GAP_ANALYSIS: [
        "ind", "preclinical", "tox", "safety", "genotox", "ames",
        "mtd", "regulatory", "package", "gap analysis"
    ],
    WorkflowStage.MANUFACTURING_FEASIBILITY: [
        "cdmo", "gmp", "scale", "manufacture", "synthesis", "formulation",
        "cmc", "process", "batch", "yield", "purity"
    ],
}


def detect_stage(text: str, has_mic_data: bool, has_variant_file: bool) -> WorkflowStage:
    """
    Score text against stage signals and return most likely stage.
    Has special boosts for structural data presence.
    """
    text_lower = text.lower()
    scores = {stage: 0 for stage in WorkflowStage}

    for stage, signals in STAGE_SIGNALS.items():
        for signal in signals:
            if signal in text_lower:
                scores[stage] += 1

    # Structural boosts
    if has_mic_data:
        scores[WorkflowStage.HIT_DISCOVERY] += 3
        scores[WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION] += 2
    if has_variant_file:
        scores[WorkflowStage.RESISTANCE_MECHANISM_CHARACTERIZATION] += 4

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return WorkflowStage.UNKNOWN
    return best


# ─────────────────────────────────────────────
# CSV parser — resistance assay / compound screen
# ─────────────────────────────────────────────

def parse_assay_csv(content: str) -> tuple[list[MICEntry], list[str], list[str]]:
    """
    Parse resistance assay CSV.
    Auto-detects column names for: compound, organism, MIC value, unit.
    Returns: (mic_entries, compound_names, data_quality_notes)
    """
    mic_entries = []
    compound_names = []
    notes = []

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return [], [], ["CSV parse error: no headers detected"]

    headers_lower = [h.lower().strip() for h in reader.fieldnames]

    # Column detection
    def find_col(candidates):
        for c in candidates:
            for h in reader.fieldnames:
                if c in h.lower():
                    return h
        return None

    col_compound = find_col(["compound", "drug", "antibiotic", "molecule", "name"])
    col_organism = find_col(["organism", "strain", "bacteria", "species", "pathogen"])
    col_mic = find_col(["mic", "minimum inhibitory", "ic50", "ec50", "activity"])
    col_unit = find_col(["unit", "µg", "ug/ml", "ng/ml"])
    col_method = find_col(["method", "assay", "protocol"])

    if not col_compound:
        notes.append("⚠ No 'compound' column detected — using first column")
        col_compound = reader.fieldnames[0] if reader.fieldnames else None
    if not col_mic:
        notes.append("⚠ No 'MIC' or 'IC50' column detected — activity data may be missing")

    rows_parsed = 0
    for row in reader:
        try:
            compound = row.get(col_compound, "").strip() if col_compound else ""
            organism = row.get(col_organism, "Unknown organism").strip() if col_organism else "Unknown"
            mic_raw = row.get(col_mic, "").strip() if col_mic else ""
            unit = row.get(col_unit, "µg/mL").strip() if col_unit else "µg/mL"
            method = row.get(col_method, "").strip() if col_method else None

            # Parse MIC value (handle ">32", "<0.5", "32", "32.0")
            mic_val = None
            if mic_raw:
                clean = re.sub(r'[><=]', '', mic_raw).strip()
                try:
                    mic_val = float(clean)
                except ValueError:
                    notes.append(f"⚠ Could not parse MIC value: '{mic_raw}' for {compound}")

            if compound:
                compound_names.append(compound)
                if mic_val is not None:
                    mic_entries.append(MICEntry(
                        compound=compound,
                        organism=organism,
                        mic_value=mic_val,
                        unit=unit,
                        method=method,
                        source="assay_csv"
                    ))
            rows_parsed += 1
        except Exception as e:
            notes.append(f"⚠ Row parse error: {e}")

    if rows_parsed == 0:
        notes.append("⚠ No data rows parsed from CSV")

    return mic_entries, list(set(compound_names)), notes


# ─────────────────────────────────────────────
# VCF / variant file parser
# ─────────────────────────────────────────────

def parse_variant_file(content: str) -> tuple[list[str], list[str]]:
    """
    Parse VCF or annotated variant file.
    Extracts gene names. Returns (gene_names, notes).
    """
    gene_names = set()
    notes = []

    lines = content.splitlines()
    is_vcf = any(line.startswith("##fileformat=VCF") for line in lines[:5])

    if is_vcf:
        for line in lines:
            if line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 8:
                info = parts[7]
                # Extract gene names from INFO field (common annotators: ANN, GENE, CSQ)
                for pattern in [r'GENE=([^;]+)', r'ANN=[^|]+\|([^|]+)\|', r'gene_name=([^;]+)']:
                    matches = re.findall(pattern, info, re.IGNORECASE)
                    gene_names.update(matches)
    else:
        # Treat as annotated text file — extract gene mentions
        extracted = extract_gene_names_from_text(content)
        gene_names.update(extracted)

        # Also look for tabular format with "gene" column
        reader = csv.DictReader(io.StringIO(content), delimiter='\t')
        if reader.fieldnames:
            gene_col = next((h for h in reader.fieldnames if 'gene' in h.lower()), None)
            if gene_col:
                for row in reader:
                    g = row.get(gene_col, "").strip()
                    if g:
                        gene_names.add(g)

    if not gene_names:
        notes.append("⚠ No resistance genes extracted from variant file — check file format")

    return list(gene_names), notes


# ─────────────────────────────────────────────
# PDF text extractor
# ─────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> tuple[str, list[str]]:
    """
    Extract text from PDF using pymupdf (fitz).
    Returns (text, notes).
    """
    notes = []
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        full_text = "\n".join(text_parts)
        if len(full_text) < 100:
            notes.append("⚠ PDF text extraction returned very little text — may be scanned/image PDF")
        return full_text, notes
    except ImportError:
        notes.append("⚠ pymupdf not installed — PDF text extraction unavailable")
        return "", notes
    except Exception as e:
        notes.append(f"⚠ PDF parse error: {e}")
        return "", notes


# ─────────────────────────────────────────────
# Organism extractor
# ─────────────────────────────────────────────

ORGANISM_PATTERNS = [
    r'Klebsiella pneumoniae',
    r'Escherichia coli',
    r'Acinetobacter baumannii',
    r'Pseudomonas aeruginosa',
    r'Staphylococcus aureus',
    r'Enterococcus faecium',
    r'Enterococcus faecalis',
    r'Mycobacterium tuberculosis',
    r'Clostridioides difficile',
    r'Neisseria gonorrhoeae',
    r'Streptococcus pneumoniae',
]

def extract_organism(text: str) -> Optional[str]:
    for pattern in ORGANISM_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    # Abbreviation fallback
    abbrev = {"K. pneumoniae": "Klebsiella pneumoniae", "E. coli": "Escherichia coli",
              "P. aeruginosa": "Pseudomonas aeruginosa", "S. aureus": "Staphylococcus aureus",
              "A. baumannii": "Acinetobacter baumannii"}
    for abbr, full in abbrev.items():
        if abbr in text:
            return full
    return None


# ─────────────────────────────────────────────
# Missing data flag generator
# ─────────────────────────────────────────────

def generate_missing_flags(state: ProgramState) -> list[str]:
    flags = []
    if not state.mic_data:
        flags.append("No MIC data found — cannot assess compound potency")
    if not state.resistance_genes:
        flags.append("No resistance genes identified — mechanism unknown")
    if not state.organism:
        flags.append("No target organism specified")
    if not state.has_paper_pdf:
        flags.append("No literature context provided — rationale may be weak")
    if not state.has_variant_file:
        flags.append("No variant/genomics file — genotypic confirmation unavailable")
    if not state.compounds:
        flags.append("No compounds identified for prioritization")
    if state.stage == WorkflowStage.UNKNOWN:
        flags.append("Program stage could not be determined — review input data")
    return flags


def score_evidence(state: ProgramState) -> EvidenceStrength:
    score = 0
    if state.mic_data: score += 2
    if state.resistance_genes: score += 2
    if state.organism: score += 1
    if state.has_paper_pdf: score += 1
    if state.has_variant_file: score += 2
    if state.stage != WorkflowStage.UNKNOWN: score += 1

    if score >= 7:
        return EvidenceStrength.STRONG
    elif score >= 4:
        return EvidenceStrength.MODERATE
    return EvidenceStrength.WEAK


# ─────────────────────────────────────────────
# Main ingestion entry point
# ─────────────────────────────────────────────

async def build_program_state(
    assay_csv: Optional[str] = None,
    variant_file: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
    free_text: Optional[str] = None,
    compound_screen_csv: Optional[str] = None,
) -> ProgramState:
    """
    Main Layer 1 entry point.
    Takes all available inputs, parses deterministically, returns ProgramState.
    """
    state = ProgramState(session_id=str(uuid.uuid4()))
    all_text = ""
    
    # ── Process assay CSV ──
    if assay_csv:
        state.has_assay_csv = True
        mic_entries, compound_names, notes = parse_assay_csv(assay_csv)
        state.mic_data.extend(mic_entries)
        state.data_quality_notes.extend(notes)
        all_text += assay_csv

        for name in compound_names:
            if not any(c.name.lower() == name.lower() for c in state.compounds):
                state.compounds.append(Compound(name=name))

    # ── Process compound screen ──
    if compound_screen_csv:
        state.has_compound_screen = True
        mic_entries, compound_names, notes = parse_assay_csv(compound_screen_csv)
        state.mic_data.extend(mic_entries)
        state.data_quality_notes.extend(notes)
        all_text += compound_screen_csv

    # ── Process variant/genomics file ──
    if variant_file:
        state.has_variant_file = True
        gene_names, notes = parse_variant_file(variant_file)
        state.data_quality_notes.extend(notes)
        all_text += variant_file
        for gene in gene_names:
            if not any(g.gene_name.lower() == gene.lower() for g in state.resistance_genes):
                state.resistance_genes.append(ResistanceGene(gene_name=gene))

    # ── Process PDF ──
    if pdf_bytes:
        state.has_paper_pdf = True
        pdf_text, notes = extract_pdf_text(pdf_bytes)
        state.data_quality_notes.extend(notes)
        all_text += pdf_text

    # ── Process free text ──
    if free_text:
        state.has_free_text = True
        all_text += " " + free_text

    # ── Extract entities from all text ──
    if all_text:
        # Genes from text
        text_genes = extract_gene_names_from_text(all_text)
        for gene in text_genes:
            if not any(g.gene_name.lower() == gene.lower() for g in state.resistance_genes):
                state.resistance_genes.append(ResistanceGene(gene_name=gene))

        # Compounds from text
        text_compounds = extract_compound_names_from_text(all_text)
        for name in text_compounds:
            if not any(c.name.lower() == name.lower() for c in state.compounds):
                state.compounds.append(Compound(name=name))

        # Organism
        state.organism = extract_organism(all_text)

    # ── Detect stage ──
    state.stage = detect_stage(
        all_text,
        has_mic_data=len(state.mic_data) > 0,
        has_variant_file=state.has_variant_file
    )

    # ── Quality scoring ──
    state.missing_flags = generate_missing_flags(state)
    state.evidence_strength = score_evidence(state)

    # ── Project summary ──
    genes_str = ", ".join(g.gene_name for g in state.resistance_genes[:3]) or "unknown"
    compounds_str = ", ".join(c.name for c in state.compounds[:3]) or "unknown"
    org_str = state.organism or "unspecified organism"
    state.project_summary = (
        f"Program targeting {org_str} with resistance genes [{genes_str}]. "
        f"Compounds identified: [{compounds_str}]. "
        f"Stage: {state.stage.value.replace('_', ' ').title()}. "
        f"Evidence strength: {state.evidence_strength.value}."
    )

    return state
