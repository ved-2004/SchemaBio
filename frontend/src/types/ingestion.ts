/**
 * SchemaBio Ingestion Layer — Frontend Contracts
 *
 * These types mirror the backend ingestion API response exactly.
 * Backend: POST /api/upload-and-parse, GET /api/demo-ingestion
 */

/** Single uploaded file descriptor from ingestion (matches backend UploadedFileDescriptor) */
export interface UploadedFileDescriptor {
  file_id: string;
  filename: string;
  detected_type: string;
  schema_confidence: number;
  parse_status: "pending" | "parsing" | "complete" | "error";
  extracted_fields: string[];
  warnings: string[];
}

/** Entity extracted from parsed files (e.g. organism, target, compound) */
export interface ExtractedEntity {
  type: string;
  value: string;
  source?: string;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

/** Signal derived from data (e.g. resistance fold-shift, compound hit) */
export interface ExtractedSignal {
  kind: string;
  value: string | number | boolean;
  unit?: string;
  source?: string;
  evidence_ref?: string;
}

/** Stage estimate from ingestion (deterministic heuristics) */
export interface StageEstimate {
  name: string;
  confidence: number;
  reasoning_basis: string[];
}

/**
 * Program state produced by the ingestion layer.
 * Built deterministically from uploaded files; no LLM in this layer.
 */
export interface ProgramState {
  program_id: string;
  status: string;
  uploaded_files: UploadedFileDescriptor[];
  entities: ExtractedEntity[];
  signals: ExtractedSignal[];
  stage_estimate: StageEstimate | null;
  missing_data_flags: string[];
  warnings: string[];
  evidence_index: Record<string, string[]>;
}

/** Evidence bundle for experiment design or execution handoff */
export interface EvidenceBundle {
  literature_refs: string[];
  quantitative_claims: Array<{ type: string; value: string | number; unit?: string; target?: string }>;
  audit_refs: string[];
  gap_refs: string[];
  file_refs?: string[];
}

/**
 * Input to the experiment design layer (handoff from ingestion).
 */
export interface ExperimentDesignInput {
  stage: string;
  stage_confidence: number;
  biological_context: string;
  assay_context: string[];
  priority_signals: ExtractedSignal[];
  missing_experiment_context: string[];
  evidence_bundle: EvidenceBundle;
}

/**
 * Input to the execution / translational planning layer (handoff from ingestion).
 */
export interface ExecutionPlanningInput {
  stage: string;
  stage_confidence: number;
  program_summary: string;
  development_signals: ExtractedSignal[];
  missing_development_inputs: string[];
  readiness_constraints: string[];
  evidence_bundle: EvidenceBundle;
}

/**
 * Top-level ingestion API response.
 * Returned by GET /api/demo-ingestion or POST /api/upload-and-parse.
 */
export interface IngestionResponse {
  program_state: ProgramState;
  experiment_design_input: ExperimentDesignInput;
  execution_planning_input: ExecutionPlanningInput;
  run_id: string | null;
}
