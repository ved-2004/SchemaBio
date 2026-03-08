/**
 * SchemaBio API client.
 *
 * TODO (Backend integration): Implement real ingestion call when backend is ready.
 *
 * Expected backend endpoint:
 *   POST /api/ingest  (or POST /api/analyze)
 *   Body: FormData with keys such as vcf_file, csv_files[], pdf_file, txt_file
 *   Response: JSON matching IngestionResponse from @/types/ingestion
 *
 * Example usage once implemented:
 *   const formData = new FormData();
 *   formData.append("csv_files", file1);
 *   formData.append("csv_files", file2);
 *   const res = await fetch("/api/ingest", { method: "POST", body: formData });
 *   if (!res.ok) throw new Error(await res.text());
 *   const data: IngestionResponse = await res.json();
 *   return data;
 */
import type { IngestionResponse } from "@/types/ingestion";

export async function postIngest(_formData: FormData): Promise<IngestionResponse> {
  // TODO: Replace with real backend call. Backend ingestion layer will parse files
  // and return program_state, experiment_design_input, execution_planning_input.
  throw new Error("Ingestion API not yet implemented. Use mock data (Load demo) until backend is ready.");
}
