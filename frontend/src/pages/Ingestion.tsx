import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { UploadFileCard } from "@/components/schemabio/UploadFileCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Upload, Check, ArrowRight, Loader2, Beaker, Rocket } from "lucide-react";
import { useIngestion } from "@/contexts/IngestionContext";
import { uploadAndParse } from "@/lib/ingestionApi";
import { fetchUserUploads, daysUntilExpiry, type UploadRecord } from "@/lib/uploadsApi";
import type { ProgramState, UploadedFileDescriptor } from "@/types/ingestion";

function mapStatus(s: UploadedFileDescriptor["parse_status"]): "parsing" | "complete" | "error" {
  if (s === "complete" || s === "error") return s;
  return "parsing";
}

function getFileExtension(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "txt";
}

export default function Ingestion() {
  const { ingestionResponse, setIngestionResponse, isLoadingLayer2, isLoadingLayer3 } = useIngestion();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadRecords, setUploadRecords] = useState<UploadRecord[]>([]);

  useEffect(() => {
    fetchUserUploads().then(setUploadRecords).catch(() => {});
  }, [ingestionResponse]);

  const runPipeline = useCallback(async (data: Parameters<typeof setIngestionResponse>[0]) => {
    setLoading(true);
    setError(null);
    try {
      await setIngestionResponse(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Pipeline failed");
    } finally {
      setLoading(false);
    }
  }, [setIngestionResponse]);

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files?.length) return;
      try {
        const data = await uploadAndParse(Array.from(files));
        await runPipeline(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      }
      e.target.value = "";
    },
    [runPipeline]
  );

  const state: ProgramState | null = ingestionResponse?.program_state ?? null;
  const hasData = !!state && !loading;

  // ── Pipeline running overlay ──────────────────────────────────────────────
  if (loading) {
    const step = isLoadingLayer3
      ? { label: "Running execution planning (Layer 3)…", icon: Rocket }
      : isLoadingLayer2
      ? { label: "Running experiment design (Layer 2)…", icon: Beaker }
      : { label: "Running ingestion pipeline (Layer 1)…", icon: Loader2 };

    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <PageHeader
          title="Data Ingestion"
          description="Upload and parse scientific data files. SchemaBio detects schema, extracts entities, and builds program state."
        />
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
              <Loader2 className="h-7 w-7 animate-spin text-primary" />
            </div>
            <div className="text-center space-y-1">
              <p className="text-sm font-medium">{step.label}</p>
              <p className="text-xs text-muted-foreground">
                Running all three pipeline layers — this takes 30–90 seconds.
              </p>
            </div>
            <div className="flex items-center gap-6 mt-2">
              {[
                { label: "Ingestion", done: true },
                { label: "Experiment Design", done: isLoadingLayer2 ? false : !isLoadingLayer2 },
                { label: "Execution Planning", done: !isLoadingLayer3 && !isLoadingLayer2 },
              ].map((s, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  {loading && !s.done ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                  ) : (
                    <Check className="h-3.5 w-3.5 text-success" />
                  )}
                  <span className="text-xs text-muted-foreground">{s.label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <PageHeader
        title="Data Ingestion"
        description="Upload and parse scientific data files. SchemaBio detects schema, extracts entities, and builds program state."
      />

      {error && (
        <div className="text-sm text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Drop zone + actions */}
      <Card className="border-2 border-dashed border-border hover:border-primary/40 transition-colors">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary mb-4">
            <Upload className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium">Drop files here or choose files</p>
          <p className="text-xs text-muted-foreground mt-1">Resistance CSV, compound screen CSV, VCF, PDF, TXT — up to 50MB</p>
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            <label className="cursor-pointer">
              <input type="file" className="hidden" multiple accept=".csv,.tsv,.vcf,.vcf.gz,.pdf,.txt,.md" onChange={handleFileSelect} disabled={loading} />
              <Button variant="default" size="sm" className="text-xs" asChild>
                <span>Upload & parse</span>
              </Button>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Results — only shown after ALL layers complete */}
      {hasData && (
        <>
          <div>
            <h3 className="text-sm font-semibold mb-3">Uploaded Files</h3>
            <div className="space-y-2">
              {state.uploaded_files.map((f) => {
                const record = uploadRecords.find((r) => r.filename === f.filename);
                const days = record ? daysUntilExpiry(record.expires_at) : null;
                return (
                  <div key={f.file_id || f.filename} className="relative">
                    <UploadFileCard
                      fileName={f.filename}
                      fileType={getFileExtension(f.filename)}
                      status={mapStatus(f.parse_status)}
                      confidence={f.schema_confidence}
                      detectedType={f.detected_type}
                      extractedFields={f.extracted_fields?.length ?? 0}
                    />
                    {days !== null && (
                      <span className="absolute bottom-1.5 right-3 text-[10px] text-muted-foreground/60">
                        Expires in {days} day{days !== 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Parse preview */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">Structured Parse Preview (entities)</CardTitle>
                <Badge variant="secondary" className="text-[10px]">
                  {state.uploaded_files.length} file(s) · {state.entities.length} entities
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs">Field</TableHead>
                    <TableHead className="text-xs">Extracted Value</TableHead>
                    <TableHead className="text-xs text-right">Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {state.entities.slice(0, 8).map((row) => (
                    <TableRow key={`${row.type}-${row.value}`}>
                      <TableCell className="text-xs font-mono text-muted-foreground">{row.type}</TableCell>
                      <TableCell className="text-xs font-medium">{row.value}</TableCell>
                      <TableCell className="text-xs text-right font-mono text-primary">
                        {row.confidence != null ? String(row.confidence) : "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Program State summary */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">Program State</CardTitle>
                <Badge variant="outline" className="text-[10px] bg-success/10 text-success border-success/20">
                  <Check className="mr-1 h-3 w-3" /> {state.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {state.stage_estimate && (
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">Stage estimate</p>
                  <p className="text-xs font-medium">
                    {state.stage_estimate.name.replace(/_/g, " ")} ({Math.round(state.stage_estimate.confidence * 100)}%)
                  </p>
                  {state.stage_estimate.reasoning_basis?.length > 0 && (
                    <ul className="text-xs text-muted-foreground mt-0.5 list-disc list-inside space-y-0.5">
                      {state.stage_estimate.reasoning_basis.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              {state.signals.length > 0 && (
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">Signals</p>
                  <div className="flex flex-wrap gap-2">
                    {state.signals.map((s, i) => (
                      <Badge key={i} variant="secondary" className="text-[10px]">
                        {s.kind}: {String(s.value)}{s.unit ? ` ${s.unit}` : ""}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {state.warnings.length > 0 && (
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">Warnings</p>
                  <ul className="text-xs text-muted-foreground list-disc list-inside space-y-0.5">
                    {state.warnings.slice(0, 5).map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
              {state.missing_data_flags.length > 0 && (
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase font-semibold mb-1">Missing data flags</p>
                  <ul className="text-xs text-muted-foreground list-disc list-inside space-y-0.5">
                    {state.missing_data_flags.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex justify-end pt-2">
                <Button size="sm" className="text-xs" asChild>
                  <Link to="/experiments">View Experiment Design <ArrowRight className="ml-1.5 h-3 w-3" /></Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Downstream inputs preview */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Downstream inputs (for Experiment Design & Execution)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground mb-2">
                experiment_design_input and execution_planning_input are available in context for the Experiment Design and Execution Planning pages.
              </p>
              <pre className="text-[10px] font-mono bg-secondary/30 rounded-lg p-3 overflow-x-auto text-muted-foreground leading-relaxed max-h-32 overflow-y-auto">
                {JSON.stringify(
                  {
                    experiment_design: {
                      stage: ingestionResponse?.experiment_design_input?.stage,
                      stage_confidence: ingestionResponse?.experiment_design_input?.stage_confidence,
                      biological_context: ingestionResponse?.experiment_design_input?.biological_context?.slice(0, 80) + "…",
                    },
                    execution_planning: {
                      stage: ingestionResponse?.execution_planning_input?.stage,
                      program_summary: ingestionResponse?.execution_planning_input?.program_summary?.slice(0, 80) + "…",
                    },
                  },
                  null,
                  2
                )}
              </pre>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
