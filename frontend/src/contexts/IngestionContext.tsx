/**
 * Shared ingestion response state across Ingestion and Program Dashboard.
 * TODO: When backend is ready, replace setIngestionResponse with API call in Ingestion page:
 *   const formData = new FormData(); ... files ...
 *   const res = await fetch('/api/ingest', { method: 'POST', body: formData });
 *   const data: IngestionResponse = await res.json();
 *   setIngestionResponse(data);
 */
import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import type { IngestionResponse } from "@/types/ingestion";

type IngestionContextValue = {
  ingestionResponse: IngestionResponse | null;
  setIngestionResponse: (data: IngestionResponse | null) => void;
};

const IngestionContext = createContext<IngestionContextValue | null>(null);

export function IngestionProvider({ children }: { children: ReactNode }) {
  const [ingestionResponse, setIngestionResponse] = useState<IngestionResponse | null>(null);
  return (
    <IngestionContext.Provider value={{ ingestionResponse, setIngestionResponse }}>
      {children}
    </IngestionContext.Provider>
  );
}

export function useIngestion() {
  const ctx = useContext(IngestionContext);
  if (!ctx) throw new Error("useIngestion must be used within IngestionProvider");
  return ctx;
}
