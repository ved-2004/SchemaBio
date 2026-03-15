/**
 * SchemaBio API client.
 *
 * Delegates to the real backend ingestion endpoint.
 */
import type { IngestionResponse } from "@/types/ingestion";
import { API_BASE_URL } from "./config";

export async function postIngest(formData: FormData): Promise<IngestionResponse> {
  const res = await fetch(`${API_BASE_URL}/api/upload-and-parse`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || "Upload and parse failed");
  }
  return res.json();
}
