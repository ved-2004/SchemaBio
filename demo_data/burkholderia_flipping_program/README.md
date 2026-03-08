# Burkholderia resistance and sensitivity flipping — demo file stack

A realistic uploadable file stack for testing the SchemaBio ingestion layer, file-stack readiness logic, stage detection, and downstream handoff generation (experiment design and execution planning).

## Scientific story

- **Organism:** Burkholderia (B. cepacia complex)
- **Domain:** Antibiotic resistance and sensitivity flipping (collateral sensitivity)
- **Theme:** Mutation-driven resistance/sensitivity switching across lineages, with compound response context and literature rationale.

The demo represents a program where:
- Several Burkholderia isolates/lineages (L1, L2, L3, reference) are tracked.
- Some isolates show resistance to fluoroquinolones (ciprofloxacin, levofloxacin) with high fold-shift vs WT (ATCC 25609).
- Variant data (VCF) suggests gyrA, parC, and efflux (acrB) variants associated with resistance.
- Assay data shows MIC and fold-shift patterns; compound screen identifies leads (e.g. Bcep-Inh-01, Bcep-Inh-05) against gyrA.
- Target rationale and project notes describe mechanism characterization, follow-up validation, and need for expanded testing and translational planning.

## Files in this folder

| File | Purpose | Ingestion category (expected) |
|------|---------|------------------------------|
| **resistance_assay.csv** | MIC table: isolate, antibiotic, mic, fold_shift, replicate, assay_type | raw_assay_data |
| **compound_screen.csv** | Compound screen: compound_name, target, ic50_nm, z_score, hit_flag | compound_screen |
| **burkholderia_variants.vcf** | VCF with gyrA, parC, acrB variants (SnpEff ANN) | genomics_variants |
| **target_rationale.txt** | Scientific rationale (Burkholderia, resistance, flipping, validation, CRO) | notes_context |
| **project_notes.txt** | Internal notes (findings, gaps, next steps, reproducibility) | notes_context |
| **manifest.json** | Manifest describing the demo and expected ingestion behavior | (not uploaded) |
| **README.md** | This file | (not uploaded) |
| **lineage_metadata.csv** | Optional: lineage/isolate metadata, phenotype class | (CSV; may be resistance or compound_screen by content) |
| **sample_summary.csv** | Optional: sample_id, file_origin, quality_flag | (CSV; subtype by content) |
| **expected_ingestion_output.json** | Expected shape and key fields of ingestion response | (not uploaded) |

## What to upload

**Recommended first test (core stack):**  
Upload these five files together so the ingestion layer sees a full workspace:

1. `resistance_assay.csv`
2. `compound_screen.csv`
3. `burkholderia_variants.vcf`
4. `target_rationale.txt`
5. `project_notes.txt`

Optional: add `lineage_metadata.csv` and/or `sample_summary.csv` for extra CSV coverage (they may be classified as resistance or compound_screen depending on parser rules).

**Do not upload:** `manifest.json`, `README.md`, `expected_ingestion_output.json` (they are for your reference only).

## What the ingestion layer should detect

- **File stack:** Five (or seven) files with categories `raw_assay_data`, `compound_screen`, `genomics_variants`, `notes_context`.
- **Entities:** Organisms (e.g. Bcep_ATCC_25609, Bcep_L1_003), compounds (Bcep-Inh-01, Bcep-Inh-05), targets (gyrA, parC), variants (gyrA D87N, parC S80L), assay_type (MIC_broth).
- **Signals:** resistance_fold_shift (e.g. 32, 64), compound_hit, lead_ic50_nm, variant_count, resistance_associated_variant.
- **Stage:** Likely `resistance_mechanism_characterization` (or similar), given variant + assay + compound data.
- **Missing data flags:** e.g. no_vehicle_control_detected, no_reproducibility_summary_detected, no_target_engagement_data_detected, no_admet_data_detected, no_manufacturability_data_detected.
- **Progression:** `progression_status` = `ready_for_downstream_layers`; `supports_experiment_design` = true; `supports_execution_planning` = true (multiple evidence types).

## Folder location

- **Path:** `demo_data/burkholderia_flipping_program/`
- From repo root: `demo_data/burkholderia_flipping_program/`

Use the Ingestion UI to select the five (or seven) data files from this folder and run **Upload & parse**. Then check the File stack, Workspace readiness, and Downstream layers panels.

## Parser compatibility

- **Resistance CSV:** Columns `isolate_id`, `antibiotic`, `mic`, `fold_shift`, `replicate`, `assay_type` align with assay parser (strain/compound/mic/fold/replicate).
- **Compound CSV:** Columns `compound_name`, `target`, `ic50_nm`, `z_score`, `hit_flag` align with compound parser.
- **VCF:** Standard VCF 4.2 with `#CHROM`, `POS`, `REF`, `ALT`, `INFO`; SnpEff-style `ANN` for gene/effect/impact so gyrA, parC, acrB are recognized as resistance-related.
- **TXT:** Plain text; target rationale and project notes are parsed as notes/target context.

## Expected stage and readiness

- **Stage:** `resistance_mechanism_characterization` (or `experimental_validation_planning` if stage estimator favors validation).
- **supports_experiment_design:** true (strong anchor from assay + compound + VCF + notes).
- **supports_execution_planning:** true or partial; may still have missing evidence flags (vehicle control, ADMET, manufacturability, etc.).

See `expected_ingestion_output.json` for a concrete expected response structure (program_id and file_ids will vary at runtime).
