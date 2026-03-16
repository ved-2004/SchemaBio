/**
 * Shared state for all three pipeline layers.
 *
 * After ingestion completes (setIngestionResponse is called), the context
 * automatically triggers Layer 2 then Layer 3 in sequence.
 *
 * retryPipeline() re-runs Layers 2 and 3 using the stored ingestionResponse.
 */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import type { IngestionResponse } from "@/types/ingestion";
import type {
  ExperimentDesignResponse,
  ExecutionPlanningResponse,
} from "@/types/layer2";
import { runExperimentDesign, runExecutionPlanning } from "@/lib/experimentApi";
import { useAuth } from "@/contexts/AuthContext";

type IngestionContextValue = {
  ingestionResponse:         IngestionResponse | null;
  experimentDesignResponse:  ExperimentDesignResponse | null;
  isLoadingLayer2:           boolean;
  layer2Error:               string | null;
  executionPlanningResponse: ExecutionPlanningResponse | null;
  isLoadingLayer3:           boolean;
  layer3Error:               string | null;
  isPipelineRunning:         boolean;
  setIngestionResponse: (data: IngestionResponse | null) => Promise<void>;
  retryPipeline: () => Promise<void>;
};

const IngestionContext = createContext<IngestionContextValue | null>(null);

export function IngestionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [ingestionResponse,         setRawIngestion]   = useState<IngestionResponse | null>(null);
  const [experimentDesignResponse,  setLayer2Result]   = useState<ExperimentDesignResponse | null>(null);
  const [executionPlanningResponse, setLayer3Result]   = useState<ExecutionPlanningResponse | null>(null);
  const [isLoadingLayer2,           setLoadingL2]      = useState(false);
  const [isLoadingLayer3,           setLoadingL3]      = useState(false);
  const [layer2Error,               setLayer2Error]    = useState<string | null>(null);
  const [layer3Error,               setLayer3Error]    = useState<string | null>(null);

  const isPipelineRunning = isLoadingLayer2 || isLoadingLayer3;

  // Keep a ref so retryPipeline always sees the latest ingestionResponse
  const ingestionRef = useRef<IngestionResponse | null>(null);

  /**
   * Runs Layers 2 and 3 sequentially for the given data.
   */
  const runLayers2And3 = useCallback(async (data: IngestionResponse) => {
    setLayer2Result(null);
    setLayer3Result(null);
    setLayer2Error(null);
    setLayer3Error(null);

    const run_id     = data.run_id ?? null;
    const user_id    = user?.id    ?? null;
    const program_id = data.program_state.program_id ?? null;

    // Layer 2
    setLoadingL2(true);
    let l2Result: ExperimentDesignResponse | null = null;
    try {
      l2Result = await runExperimentDesign(
        data.experiment_design_input,
        data.program_state,
        run_id,
        user_id,
      );
      setLayer2Result(l2Result);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setLayer2Error(msg);
      console.error("[Layer 2] Experiment design failed:", msg);
    } finally {
      setLoadingL2(false);
    }

    // Layer 3
    setLoadingL3(true);
    try {
      const l3Result = await runExecutionPlanning(
        data.execution_planning_input,
        l2Result?._layer2_output as Record<string, unknown> | undefined,
        run_id,
        user_id,
        program_id,
      );
      setLayer3Result(l3Result);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setLayer3Error(msg);
      console.error("[Layer 3] Execution planning failed:", msg);
    } finally {
      setLoadingL3(false);
    }
  }, [user]);

  const setIngestionResponse = useCallback(
    async (data: IngestionResponse | null): Promise<void> => {
      setRawIngestion(data);
      ingestionRef.current = data;
      if (!data) return;
      await runLayers2And3(data);
    },
    [runLayers2And3],
  );

  const retryPipeline = useCallback(async () => {
    const data = ingestionRef.current;
    if (!data) return;
    await runLayers2And3(data);
  }, [runLayers2And3]);

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
        retryPipeline,
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
