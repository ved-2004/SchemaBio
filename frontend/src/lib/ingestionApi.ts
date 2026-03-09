/**
 * SchemaBio ingestion API client.
 */
import type { IngestionResponse } from "@/types/ingestion";
import { API_BASE_URL } from "./config";

const API_BASE = `${API_BASE_URL}/api`;

export async function fetchDemoIngestion(): Promise<IngestionResponse> {
  const res = await fetch(`${API_BASE}/demo-ingestion`);
  if (!res.ok) throw new Error(`Demo ingestion failed: ${res.status}`);
  return res.json();
}

export async function uploadAndParse(files: File[]): Promise<IngestionResponse> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  const res = await fetch(`${API_BASE}/upload-and-parse`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || "Upload and parse failed");
  }
  return res.json();
}
