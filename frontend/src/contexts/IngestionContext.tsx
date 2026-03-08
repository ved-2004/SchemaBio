/**
 * Shared state for all three pipeline layers.
 *
 * After ingestion completes (setIngestionResponse is called), the context
 * automatically triggers Layer 2 then Layer 3 in sequence:
 *
 *   Layer 1 (ingestion)  → IngestionResponse  → stored in ingestionResponse
 *   Layer 2 (LLM)        → ExperimentDesignResponse → stored in experimentDesignResponse
 *   Layer 3 (execution)  → ExecutionPlanningResponse → stored in executionPlanningResponse
 *
 * Experiments.tsx and Execution.tsx read from this context rather than making
 * their own API calls.
 */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { IngestionResponse } from "@/types/ingestion";
import type {
  ExperimentDesignResponse,
  ExecutionPlanningResponse,
} from "@/types/layer2";
import { runExperimentDesign, runExecutionPlanning } from "@/lib/experimentApi";

type IngestionContextValue = {
  // Layer 1
  ingestionResponse:         IngestionResponse | null;
  // Layer 2
  experimentDesignResponse:  ExperimentDesignResponse | null;
  isLoadingLayer2:           boolean;
  layer2Error:               string | null;
  // Layer 3
  executionPlanningResponse: ExecutionPlanningResponse | null;
  isLoadingLayer3:           boolean;
  layer3Error:               string | null;
  // True while any downstream layer is still running
  isPipelineRunning:         boolean;
  // Setter — triggers the full sequential pipeline; returns a Promise
  setIngestionResponse: (data: IngestionResponse | null) => Promise<void>;
};

const IngestionContext = createContext<IngestionContextValue | null>(null);

export function IngestionProvider({ children }: { children: ReactNode }) {
  const [ingestionResponse,         setRawIngestion]   = useState<IngestionResponse | null>(null);
  const [experimentDesignResponse,  setLayer2Result]   = useState<ExperimentDesignResponse | null>(null);
  const [executionPlanningResponse, setLayer3Result]   = useState<ExecutionPlanningResponse | null>(null);
  const [isLoadingLayer2,           setLoadingL2]      = useState(false);
  const [isLoadingLayer3,           setLoadingL3]      = useState(false);
  const [layer2Error,               setLayer2Error]    = useState<string | null>(null);
  const [layer3Error,               setLayer3Error]    = useState<string | null>(null);

  const isPipelineRunning = isLoadingLayer2 || isLoadingLayer3;

  /**
   * Main entry point. Called by Ingestion.tsx after a successful upload or demo load.
   * Stores the Layer 1 result, then sequentially triggers Layers 2 and 3.
   * Returns a Promise that resolves only after all three layers complete.
   */
  const setIngestionResponse = useCallback(
    async (data: IngestionResponse | null): Promise<void> => {
      setRawIngestion(data);
      setLayer2Result(null);
      setLayer3Result(null);
      setLayer2Error(null);
      setLayer3Error(null);

      if (!data) return;

      // ── Layer 2 ─────────────────────────────────────────────────────────
      setLoadingL2(true);
      let l2Result: ExperimentDesignResponse | null = null;
      try {
        l2Result = await runExperimentDesign(
          data.experiment_design_input,
          data.program_state,
        );
        setLayer2Result(l2Result);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setLayer2Error(msg);
        console.error("[Layer 2] Experiment design failed:", msg);
      } finally {
        setLoadingL2(false);
      }

      // ── Layer 3 (runs after Layer 2 regardless of success) ──────────────
      setLoadingL3(true);
      try {
        const l3Result = await runExecutionPlanning(
          data.execution_planning_input,
          l2Result?._layer2_output as Record<string, unknown> | undefined,
        );
        setLayer3Result(l3Result);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setLayer3Error(msg);
        console.error("[Layer 3] Execution planning failed:", msg);
      } finally {
        setLoadingL3(false);
      }
    },
    [],
  );

  return (
    <IngestionContext.Provider
      value={{
        ingestionResponse,
        experimentDesignResponse,
        isLoadingLayer2,
        layer2Error,
        executionPlanningResponse,
        isLoadingLayer3,
        layer3Error,
        isPipelineRunning,
        setIngestionResponse,
      }}
    >
      {children}
    </IngestionContext.Provider>
  );
}

export function useIngestion() {
  const ctx = useContext(IngestionContext);
  if (!ctx) throw new Error("useIngestion must be used within IngestionProvider");
  return ctx;
}
