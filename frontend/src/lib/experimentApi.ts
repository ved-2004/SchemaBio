/**
 * API client for Layer 2 and Layer 3.
 * Called by IngestionContext after a successful ingestion.
 */

import type { ExperimentDesignResponse, ExecutionPlanningResponse } from "@/types/layer2";
import type { ExperimentDesignInput, ProgramState } from "@/types/ingestion";
import { API_BASE_URL } from "./config";

// ─── Layer 2 ──────────────────────────────────────────────────────────────────

export async function runExperimentDesign(
  experiment_design_input: ExperimentDesignInput,
  program_state: ProgramState,
): Promise<ExperimentDesignResponse> {
  const res = await fetch(`${API_BASE_URL}/api/experiment-design/run`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ experiment_design_input, program_state }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Experiment design failed (${res.status}): ${detail}`);
  }
  return res.json();
}

// ─── Layer 3 ──────────────────────────────────────────────────────────────────

export async function runExecutionPlanning(
  execution_planning_input: unknown,
  experiment_design_output?: Record<string, unknown>,
): Promise<ExecutionPlanningResponse> {
  const res = await fetch(`${API_BASE_URL}/api/execution-planning/run`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({
      execution_planning_input,
      experiment_design_output: experiment_design_output ?? null,
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Execution planning failed (${res.status}): ${detail}`);
  }
  return res.json();
}
