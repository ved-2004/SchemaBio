/**
 * Layer 2 — Experiment Design types
 * Mirrors the response shape from POST /api/experiment-design/run
 */

export interface Recommendation {
  title:         string;
  rationale:     string;
  confidence:    number;         // 0.0–1.0
  urgency:       "high" | "medium" | "low";
  sources:       string[];
  expectedValue?: string;
}

export interface Hypothesis {
  title:    string;
  evidence: string;
  status:   "testing" | "supported" | "untested";
}

export interface ControlSuggestion {
  name: string;
  type: "Positive" | "Negative" | "Comparator" | "Baseline";
}

export interface ExperimentDesignResponse {
  recommendations:    Recommendation[];
  hypotheses:         Hypothesis[];
  bioinfTasks:        string[];
  controlSuggestions: ControlSuggestion[];
  stageConfirmed:     string;
  keyHypothesis:      string;
  literatureQueries:  string[];
  pipelineNotes:      string[];
  status:             string;
  // Opaque Layer 2 output forwarded to Layer 3
  _layer2_output:     Record<string, unknown>;
}

/**
 * Layer 3 — Execution Planning types
 * Mirrors the response shape from POST /api/execution-planning/run
 */

export interface ReadinessItem {
  label: string;
  value: number;   // 0.0–1.0
}

export interface CROType {
  type:    string;
  desc:    string;
  urgency: string;
}

export interface Grant {
  name:  string;
  focus: string;
  stage: string;
  fit:   string;
}

export interface EvidenceChecklistItem {
  item: string;
  done: boolean;
}

export interface ManufacturingFlag {
  title:       string;
  description: string;
  severity:    "warning" | "critical";
}

export interface ExecutionPlanningResponse {
  readinessItems:      ReadinessItem[];
  croTypes:            CROType[];
  grants:              Grant[];
  evidenceChecklist:   EvidenceChecklistItem[];
  manufacturingFlags:  ManufacturingFlag[];
  fdaPathway:          Record<string, unknown>;
  competitiveLandscape: unknown[];
  executionBrief:      string;
  stageTimeline:       Record<string, unknown>;
  probabilityOfSuccess: Record<string, unknown>;
  grantStacking:       unknown[];
}
