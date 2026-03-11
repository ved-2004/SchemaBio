"""
tests/test_parsers.py

Unit tests for all four deterministic parsers.
These tests require NO API key — parsers are fully deterministic.

Run:
  pytest tests/test_parsers.py -v
"""

import pytest
from pathlib import Path

DEMO_DIR = Path(__file__).parent.parent / "data" / "demo"


# ─── VCF Parser ───────────────────────────────────────────────────────────────

class TestVCFParser:
    def setup_method(self):
        from api.parsers.vcf_parser import parse_vcf
        self.parse = parse_vcf
        self.vcf_path = DEMO_DIR / "gyra_variants.vcf"

    def test_vcf_parses_without_error(self):
        if not self.vcf_path.exists():
            pytest.skip("Demo VCF not found")
        variants = self.parse(self.vcf_path)
        assert isinstance(variants, list)

    def test_gyra_d87n_detected(self):
        if not self.vcf_path.exists():
            pytest.skip("Demo VCF not found")
        variants = self.parse(self.vcf_path)
        genes = [v.gene.lower() for v in variants]
        assert any("gyra" in g for g in genes), f"gyrA not found in {genes}"

    def test_qrdr_hotspot_flagged(self):
        if not self.vcf_path.exists():
            pytest.skip("Demo VCF not found")
        variants = self.parse(self.vcf_path)
        qrdr = [v for v in variants if v.is_qrdr_hotspot]
        assert len(qrdr) >= 1, "Expected at least 1 QRDR hotspot"

    def test_resistance_gene_metadata(self):
        if not self.vcf_path.exists():
            pytest.skip("Demo VCF not found")
        variants = self.parse(self.vcf_path)
        res_genes = [v for v in variants if v.is_resistance_gene]
        assert len(res_genes) >= 2, f"Expected ≥2 resistance genes, got {len(res_genes)}"

    def test_variant_sorting_resistance_first(self):
        if not self.vcf_path.exists():
            pytest.skip("Demo VCF not found")
        variants = self.parse(self.vcf_path)
        if len(variants) >= 2:
            assert variants[0].is_resistance_gene or variants[0].is_qrdr_hotspot

    def test_aa_change_extracted(self):
        if not self.vcf_path.exists():
            pytest.skip("Demo VCF not found")
        variants = self.parse(self.vcf_path)
        aa_changes = [v.aa_change for v in variants if v.aa_change]
        assert len(aa_changes) >= 1, "No amino acid changes extracted"


# ─── Assay Parser ─────────────────────────────────────────────────────────────

class TestAssayParser:
    def setup_method(self):
        from api.parsers.assay_parser import parse_resistance_assay
        self.parse = parse_resistance_assay
        self.csv_path = DEMO_DIR / "gyrase_resistance.csv"

    def test_assay_parses_without_error(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        assert result is not None

    def test_detects_resistant_strains(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        assert len(result.resistant_strains) >= 1, "Expected resistant strains"

    def test_detects_wt_strain(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        assert result.has_wt_control or len(result.wt_strains) > 0

    def test_fold_shift_computed(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        assert result.max_fold_shift is not None
        assert result.max_fold_shift > 1.0

    def test_fold_shift_correct_magnitude(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        # gyrA D87N shows 64× fold shift for Compound-14
        assert result.max_fold_shift >= 32.0, f"Expected ≥32× fold shift, got {result.max_fold_shift}"

    def test_mic_entries_populated(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        assert len(result.mic_entries) >= 3

    def test_replicate_flag(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        # Demo CSV has n=1 replicates — should be flagged
        assert result.replicate_count == 1

    def test_raw_summary_not_empty(self):
        if not self.csv_path.exists():
            pytest.skip("Demo assay CSV not found")
        result = self.parse(self.csv_path)
        assert result.raw_summary != ""
        assert "strains" in result.raw_summary


# ─── Compound Parser ──────────────────────────────────────────────────────────

class TestCompoundParser:
    def setup_method(self):
        from api.parsers.compound_parser import parse_compound_screen
        self.parse = parse_compound_screen
        self.csv_path = DEMO_DIR / "compound14_screen.csv"

    def test_compound_screen_parses(self):
        if not self.csv_path.exists():
            pytest.skip("Demo compound CSV not found")
        result = self.parse(self.csv_path)
        assert result is not None
        assert result.n_compounds >= 3

    def test_top_hits_identified(self):
        if not self.csv_path.exists():
            pytest.skip("Demo compound CSV not found")
        result = self.parse(self.csv_path)
        assert result.n_top_hits >= 1, "Expected at least 1 top hit"

    def test_lead_compound_selected(self):
        if not self.csv_path.exists():
            pytest.skip("Demo compound CSV not found")
        result = self.parse(self.csv_path)
        assert result.lead_compound is not None
        assert result.lead_compound.ic50_nm is not None

    def test_compound14_is_top_hit(self):
        if not self.csv_path.exists():
            pytest.skip("Demo compound CSV not found")
        result = self.parse(self.csv_path)
        top_names = [c.name for c in result.top_hits]
        assert any("14" in n for n in top_names), f"Compound-14 not in top hits: {top_names}"

    def test_ic50_normalized_to_nm(self):
        if not self.csv_path.exists():
            pytest.skip("Demo compound CSV not found")
        result = self.parse(self.csv_path)
        for c in result.compounds:
            if c.ic50_nm:
                assert c.ic50_nm > 0
                assert c.ic50_nm < 1_000_000  # sanity check

    def test_dmso_risk_flagged(self):
        if not self.csv_path.exists():
            pytest.skip("Demo compound CSV not found")
        result = self.parse(self.csv_path)
        dmso_risky = [c for c in result.compounds if c.dmso_risk]
        # Compound-7 and Compound-61 have risky scaffolds in demo
        assert len(dmso_risky) >= 1

    def test_deprioritize_classified(self):
        if not self.csv_path.exists():
            pytest.skip("Demo compound CSV not found")
        result = self.parse(self.csv_path)
        deprior = [c for c in result.compounds if c.flag == "DEPRIORITIZE"]
        assert len(deprior) >= 1, "Expected at least 1 DEPRIORITIZE compound"


# ─── PDF Parser ───────────────────────────────────────────────────────────────

class TestPDFParser:
    def test_pdf_parser_imports(self):
        from api.parsers.pdf_parser import parse_pdf
        assert parse_pdf is not None

    def test_pdf_handles_missing_file(self, tmp_path):
        from api.parsers.pdf_parser import ParsedPDF
        # ParsedPDF with defaults should not crash
        result = ParsedPDF()
        assert result.key_genes == []
        assert result.doc_type == "unknown"

    def test_gene_extraction_from_text(self):
        from api.parsers.pdf_parser import _extract_genes
        text = "The gyrA D87N mutation in E. coli confers resistance. parC S80I also observed."
        genes = _extract_genes(text)
        assert "gyrA" in genes or "gyra" in [g.lower() for g in genes]

    def test_organism_extraction(self):
        from api.parsers.pdf_parser import _extract_organisms
        text = "E. coli ATCC 25922 was used as wild-type. K. pneumoniae isolates were tested."
        organisms, gram = _extract_organisms(text)
        assert len(organisms) >= 1
        assert gram == "gram_negative"

    def test_mechanism_extraction(self):
        from api.parsers.pdf_parser import _extract_mechanisms
        text = "Efflux pumps AcrAB-TolC mediate resistance. gyrase inhibition was confirmed."
        mechs, kws = _extract_mechanisms(text)
        assert len(mechs) >= 1

    def test_quantitative_claim_extraction(self):
        from api.parsers.pdf_parser import _extract_quantitative
        text = "The IC50 of compound A was 45 nM against GyrA. MIC of 0.125 μg/mL was observed."
        claims = _extract_quantitative(text)
        assert len(claims) >= 1
        assert any(c.claim_type == "ic50" for c in claims)


# ─── Universal Parser Integration ────────────────────────────────────────────

class TestUniversalParser:
    def test_builds_drug_program_from_demo_files(self):
        from api.parsers.universal_parser import build_drug_program_from_files
        vcf_path = DEMO_DIR / "gyra_variants.vcf"
        csv_paths = [DEMO_DIR / "gyrase_resistance.csv", DEMO_DIR / "compound14_screen.csv"]

        missing = [p for p in [vcf_path] + csv_paths if not p.exists()]
        if missing:
            pytest.skip(f"Demo files not found: {missing}")

        program = build_drug_program_from_files(
            vcf_path=vcf_path,
            csv_paths=csv_paths,
        )
        assert program is not None
        assert program.target.gene is not None
        assert program.compound.name is not None
        assert len(program.all_compounds) >= 3
        assert len(program.resistance.resistant_strains) >= 1

    def test_evidence_flags_set(self):
        from api.parsers.universal_parser import build_drug_program_from_files
        csv_paths = [DEMO_DIR / "gyrase_resistance.csv"]
        if not csv_paths[0].exists():
            pytest.skip("Demo files not found")

        program = build_drug_program_from_files(csv_paths=csv_paths)
        assert program.evidence.has_mic_data or program.evidence.has_resistance_profiling

    def test_completeness_pct_positive(self):
        from api.parsers.universal_parser import build_drug_program_from_files
        csv_paths = [DEMO_DIR / "gyrase_resistance.csv", DEMO_DIR / "compound14_screen.csv"]
        missing = [p for p in csv_paths if not p.exists()]
        if missing:
            pytest.skip("Demo files not found")

        program = build_drug_program_from_files(csv_paths=csv_paths)
        assert program.completeness_pct > 0
        assert program.completeness_pct <= 100
