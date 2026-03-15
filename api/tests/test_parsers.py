"""
Tests for SchemaBio deterministic parsers (Layer 1).
Covers VCF, compound screen, and resistance assay parsing.
"""
from __future__ import annotations
import textwrap
from pathlib import Path
import tempfile

import pytest


# ─── VCF Parser ───────────────────────────────────────────────────────────────

class TestVCFParser:
    def _write_vcf(self, content: str) -> Path:
        p = Path(tempfile.mktemp(suffix=".vcf"))
        p.write_text(textwrap.dedent(content).strip())
        return p

    def test_parse_demo_vcf(self):
        from api.ingestion.parsers.vcf_parser import parse_vcf
        demo = Path(__file__).resolve().parent.parent.parent / "data" / "demo" / "gyra_variants.vcf"
        if not demo.exists():
            pytest.skip("Demo VCF not found")
        variants = parse_vcf(demo)
        assert len(variants) == 5
        genes = {v.gene for v in variants if v.gene}
        assert "gyrA" in genes
        assert "parC" in genes

    def test_parse_minimal_vcf(self):
        from api.ingestion.parsers.vcf_parser import parse_vcf
        vcf = self._write_vcf("""\
            ##fileformat=VCFv4.2
            #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
            chr1\t100\t.\tA\tG\t50\tPASS\tANN=G|missense_variant|MODERATE|gyrA|b1|transcript|t1|protein_coding|1/1|c.1A>G|p.Ser83Leu|||83/100|
        """)
        try:
            variants = parse_vcf(vcf)
            assert len(variants) >= 1
            assert variants[0].gene == "gyrA"
        finally:
            vcf.unlink(missing_ok=True)

    def test_empty_vcf(self):
        from api.ingestion.parsers.vcf_parser import parse_vcf
        vcf = self._write_vcf("""\
            ##fileformat=VCFv4.2
            #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
        """)
        try:
            variants = parse_vcf(vcf)
            assert len(variants) == 0
        finally:
            vcf.unlink(missing_ok=True)

    def test_resistance_gene_detection(self):
        from api.ingestion.parsers.vcf_parser import parse_vcf
        vcf = self._write_vcf("""\
            ##fileformat=VCFv4.2
            #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
            chr1\t100\t.\tC\tT\t500\tPASS\tANN=T|missense_variant|MODERATE|gyrA|b2231|transcript|t1|protein_coding|1/1|c.247C>T|p.Ser83Leu|||83/875|;CADD_PHRED=26.1
            chr1\t200\t.\tA\tG\t100\tPASS\tANN=G|synonymous_variant|LOW|someGene|b1234|transcript|t2|protein_coding|1/1|c.300A>G|p.Ala100Ala|||100/500|
        """)
        try:
            variants = parse_vcf(vcf)
            resistance_variants = [v for v in variants if v.is_resistance_gene]
            assert len(resistance_variants) >= 1
            assert resistance_variants[0].gene == "gyrA"
        finally:
            vcf.unlink(missing_ok=True)


# ─── Compound Screen Parser ──────────────────────────────────────────────────

class TestCompoundParser:
    def _write_csv(self, content: str) -> Path:
        p = Path(tempfile.mktemp(suffix=".csv"))
        p.write_text(textwrap.dedent(content).strip())
        return p

    def test_parse_demo_compound_screen(self):
        from api.ingestion.parsers.compound_parser import parse_compound_screen
        demo = Path(__file__).resolve().parent.parent.parent / "data" / "demo" / "compound14_screen.csv"
        if not demo.exists():
            pytest.skip("Demo compound screen not found")
        result = parse_compound_screen(demo)
        assert result.n_compounds > 0
        assert len(result.compounds) > 0

    def test_ic50_classification(self):
        from api.ingestion.parsers.compound_parser import parse_compound_screen
        csv = self._write_csv("""\
            compound_id,compound_name,target,ic50_nm,zscore
            CPD_001,TestDrug,GyrA,28,4.5
            CPD_002,WeakDrug,GyrA,800,1.5
        """)
        try:
            result = parse_compound_screen(csv)
            assert result.n_compounds == 2
            assert len(result.top_hits) >= 1
        finally:
            csv.unlink(missing_ok=True)

    def test_empty_csv(self):
        from api.ingestion.parsers.compound_parser import parse_compound_screen
        csv = self._write_csv("compound_id,compound_name,target,ic50_nm\n")
        try:
            result = parse_compound_screen(csv)
            assert result.n_compounds == 0
        finally:
            csv.unlink(missing_ok=True)

    def test_mic_based_screen(self):
        from api.ingestion.parsers.compound_parser import parse_compound_screen
        csv = self._write_csv("""\
            compound_id,compound_name,target,mic_ugml,zscore
            CPD_A,CompA,GyrA,0.125,3.8
            CPD_B,CompB,GyrA,4.0,0.5
        """)
        try:
            result = parse_compound_screen(csv)
            assert result.n_compounds == 2
        finally:
            csv.unlink(missing_ok=True)


# ─── Resistance Assay Parser ─────────────────────────────────────────────────

class TestAssayParser:
    def _write_csv(self, content: str) -> Path:
        p = Path(tempfile.mktemp(suffix=".csv"))
        p.write_text(textwrap.dedent(content).strip())
        return p

    def test_parse_demo_assay(self):
        from api.ingestion.parsers.assay_parser import parse_resistance_assay
        demo = Path(__file__).resolve().parent.parent.parent / "data" / "demo" / "gyrase_resistance.csv"
        if not demo.exists():
            pytest.skip("Demo resistance assay not found")
        result = parse_resistance_assay(demo)
        assert result.n_strains > 0
        assert result.assay_type == "mic"

    def test_fold_shift_detection(self):
        from api.ingestion.parsers.assay_parser import parse_resistance_assay
        csv = self._write_csv("""\
            strain,compound,mic_ugml,fold_shift,mutation
            WT_ATCC,DrugA,0.125,1.0,
            Mutant_1,DrugA,8.0,64.0,gyrA D87N
            Mutant_2,DrugA,4.0,32.0,parC S80I
        """)
        try:
            result = parse_resistance_assay(csv)
            assert result.n_strains >= 2
            assert result.max_fold_shift >= 32.0
        finally:
            csv.unlink(missing_ok=True)

    def test_resistant_strain_count(self):
        from api.ingestion.parsers.assay_parser import parse_resistance_assay
        csv = self._write_csv("""\
            strain,antibiotic,mic,fold_shift
            WT,ciprofloxacin,0.03,1.0
            Resistant_1,ciprofloxacin,32.0,1066.0
            Sensitive_1,ciprofloxacin,0.5,16.7
        """)
        try:
            result = parse_resistance_assay(csv)
            assert len(result.resistant_strains) >= 1
        finally:
            csv.unlink(missing_ok=True)


# ─── Stage Estimator ─────────────────────────────────────────────────────────

class TestStageEstimator:
    def _entity(self, type_: str, value: str):
        from api.schemas.ingestion import ExtractedEntity
        return ExtractedEntity(type=type_, value=value, source="test", confidence=1.0)

    def _signal(self, kind: str, value):
        from api.schemas.ingestion import ExtractedSignal
        return ExtractedSignal(kind=kind, value=str(value), source="test")

    def _file(self, name: str, detected_type: str):
        from api.schemas.ingestion import UploadedFileDescriptor
        return UploadedFileDescriptor(filename=name, detected_type=detected_type, size_bytes=100)

    def test_hit_discovery_stage(self):
        from api.ingestion.stage_estimator import estimate_stage
        result = estimate_stage(
            uploaded_files=[self._file("screen.csv", "compound_screen")],
            entities=[self._entity("compound", "DrugA")],
            signals=[self._signal("compound_hit", "DrugA")],
            missing_data_flags=["vehicle_control", "reproducibility", "target_engagement", "admet"],
        )
        assert result.name in [
            "hit_discovery",
            "resistance_mechanism_characterization",
            "experimental_validation_planning",
            "preclinical_package_gap_analysis",
            "manufacturing_feasibility_review",
        ]
        assert 0.0 <= result.confidence <= 1.0

    def test_stage_confidence_increases_with_data(self):
        from api.ingestion.stage_estimator import estimate_stage
        minimal = estimate_stage(
            uploaded_files=[self._file("screen.csv", "compound_screen")],
            entities=[self._entity("compound", "X")],
            signals=[],
            missing_data_flags=["everything"],
        )
        rich = estimate_stage(
            uploaded_files=[
                self._file("screen.csv", "compound_screen"),
                self._file("variants.vcf", "vcf"),
                self._file("assay.csv", "resistance_assay"),
            ],
            entities=[
                self._entity("compound", "X"),
                self._entity("target", "GyrA"),
                self._entity("organism", "E. coli"),
                self._entity("variant", "D87N"),
            ],
            signals=[
                self._signal("compound_hit", "X"),
                self._signal("resistance_fold_shift", 64),
            ],
            missing_data_flags=[],
        )
        assert rich.confidence >= minimal.confidence


# ─── Ingestion Service ────────────────────────────────────────────────────────

class TestIngestionService:
    def test_run_ingestion_with_demo_files(self):
        from api.ingestion.service import run_ingestion
        demo_dir = Path(__file__).resolve().parent.parent.parent / "data" / "demo"
        files = list(demo_dir.glob("*"))
        if not files:
            pytest.skip("No demo files")
        result = run_ingestion(files)
        assert result.program_state.program_id
        assert len(result.program_state.entities) > 0
        assert result.experiment_design_input is not None
        assert result.execution_planning_input is not None

    def test_run_ingestion_produces_stage(self):
        from api.ingestion.service import run_ingestion
        demo_dir = Path(__file__).resolve().parent.parent.parent / "data" / "demo"
        files = list(demo_dir.glob("*"))
        if not files:
            pytest.skip("No demo files")
        result = run_ingestion(files)
        assert result.program_state.stage_estimate is not None
        assert result.program_state.stage_estimate.name


# ─── API Routes (using httpx TestClient) ──────────────────────────────────────

class TestAPIRoutes:
    @pytest.fixture
    def client(self):
        from httpx import AsyncClient, ASGITransport
        from api.main import app
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_health(self, client):
        async with client as c:
            r = await c.get("/api/health")
            assert r.status_code == 200
            data = r.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_demo_ingestion_removed(self, client):
        async with client as c:
            r = await c.get("/api/demo-ingestion")
            assert r.status_code == 404  # demo endpoint removed from production

    @pytest.mark.asyncio
    async def test_upload_no_files(self, client):
        async with client as c:
            r = await c.post("/api/upload-and-parse")
            assert r.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_upload_invalid_extension(self, client):
        async with client as c:
            r = await c.post(
                "/api/upload-and-parse",
                files=[("files", ("malware.exe", b"bad content", "application/octet-stream"))],
            )
            assert r.status_code == 400
            assert "Unsupported" in r.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_program_not_found(self, client):
        async with client as c:
            r = await c.get("/api/program/NONEXISTENT")
            assert r.status_code == 404
