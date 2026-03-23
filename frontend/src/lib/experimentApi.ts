/**
 * API client for Layer 2 and Layer 3.
 * Called by IngestionContext after a successful ingestion.
 */

import type { ExperimentDesignResponse, ExecutionPlanningResponse } from "@/types/layer2";
import type { ExperimentDesignInput, ProgramState } from "@/types/ingestion";
import { API_BASE_URL } from "./config";
import { authHeaders } from "@/contexts/AuthContext";

// ─── Layer 2 ──────────────────────────────────────────────────────────────────

export async function runExperimentDesign(
  experiment_design_input: ExperimentDesignInput,
  program_state: ProgramState,
  run_id: string | null,
  user_id: string | null,
): Promise<ExperimentDesignResponse> {
  const res = await fetch(`${API_BASE_URL}/api/experiment-design/run`, {
    method:      "POST",
    headers:     { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      experiment_design_input,
      program_state,
      run_id:  run_id  ?? undefined,
      user_id: user_id ?? undefined,
    }),
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
  experiment_design_output: Record<string, unknown> | null | undefined,
  run_id: string | null,
  user_id: string | null,
  program_id: string | null,
): Promise<ExecutionPlanningResponse> {
  const res = await fetch(`${API_BASE_URL}/api/execution-planning/run`, {
    method:      "POST",
    headers:     { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      execution_planning_input,
      experiment_design_output: experiment_design_output ?? null,
      run_id:     run_id     ?? undefined,
      user_id:    user_id    ?? undefined,
      program_id: program_id ?? undefined,
    }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Execution planning failed (${res.status}): ${detail}`);
  }
  return res.json();
}
