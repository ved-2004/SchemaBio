import { useMemo } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { ProgramHeroCard } from "@/components/schemabio/ProgramHeroCard";
import { WorkflowStepper } from "@/components/schemabio/WorkflowStepper";
import { ReadinessMeter } from "@/components/schemabio/ReadinessMeter";
import { RiskFlagCard } from "@/components/schemabio/RiskFlagCard";
import { RecommendationCard } from "@/components/schemabio/RecommendationCard";
import { AgentTracePanel } from "@/components/schemabio/AgentTracePanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileSpreadsheet, Clock } from "lucide-react";
import { useIngestion } from "@/contexts/IngestionContext";

export default function Dashboard() {
  const {
    ingestionResponse,
    experimentDesignResponse,
    executionPlanningResponse,
  } = useIngestion();

  const ps   = ingestionResponse?.program_state ?? null;
  const expIn = ingestionResponse?.experiment_design_input ?? null;

  const programData = useMemo(() => {
    if (!ps || !expIn) return null;
    const organism = ps.entities.find((e) => e.type === "organism")?.value ?? "—";
    const target   = ps.entities.find((e) => e.type === "target" || e.type === "target_gene")?.value ?? "—";
    const compound = ps.entities.find((e) => e.type === "compound")?.value ?? "—";
    const variant  = ps.entities.filter((e) => e.type === "variant" || e.type === "mutation").map((e) => e.value).join(", ") || "—";
    const assay    = ps.entities.find((e) => e.type === "assay_type")?.value ?? "MIC / compound screen";
    return {
      title:      `${organism} — ${compound} Program`,
      stage:      ps.stage_estimate?.name?.replace(/_/g, " ") ?? "Unknown",
      confidence: ps.stage_estimate?.confidence ?? 0,
      summary:    expIn.biological_context,
      entities:   { organism, target: `${target}${variant !== "—" ? ` (${variant})` : ""}`, compound, variant, assay },
    };
  }, [ps, expIn]);

  // Derive workflow steps from pipeline state
  const workflowSteps = useMemo(() => [
    { label: "Ingestion",       status: ingestionResponse ? "complete" as const : "current" as const },
    { label: "Stage Detection", status: ps?.stage_estimate ? "complete" as const : ingestionResponse ? "current" as const : "upcoming" as const },
    { label: "Exp. Design",     status: experimentDesignResponse ? "complete" as const : ingestionResponse ? "current" as const : "upcoming" as const },
    { label: "Execution Plan",  status: executionPlanningResponse ? "complete" as const : "upcoming" as const },
    { label: "Manufacturing",   status: "upcoming" as const },
  ], [ingestionResponse, ps, experimentDesignResponse, executionPlanningResponse]);

  // Derive agent traces from real Layer 1 parsing output
  const traces = useMemo(() => {
    if (!ps) return [];
    const t = [];
    if (ps.uploaded_files.length > 0) {
      const types = [...new Set(ps.uploaded_files.map((f) => f.detected_type).filter(Boolean))].join(", ");
      t.push({ step: "Schema Detection", detail: `Detected: ${ps.uploaded_files.map((f) => f.filename).join(", ")}${types ? `. Types: ${types}` : ""}`, timestamp: "recent" });
    }
    if (ps.entities.length > 0) {
      t.push({ step: "Entity Extraction", detail: `Extracted ${ps.entities.length} entities: ${ps.entities.slice(0, 4).map((e) => `${e.type}:${e.value}`).join(", ")}${ps.entities.length > 4 ? "…" : ""}`, timestamp: "recent" });
    }
    if (ps.stage_estimate) {
      t.push({ step: "Stage Classification", detail: `Stage: ${ps.stage_estimate.name.replace(/_/g, " ")} (confidence ${Math.round(ps.stage_estimate.confidence * 100)}%). ${ps.stage_estimate.reasoning_basis?.[0] ?? ""}`, timestamp: "recent" });
    }
    if (experimentDesignResponse) {
      t.push({ step: "Experiment Design", detail: `Generated ${experimentDesignResponse.recommendations.length} recommendations. Key hypothesis: ${experimentDesignResponse.hypotheses[0]?.title ?? "see Experiments page"}`, timestamp: "recent" });
    }
    return t;
  }, [ps, experimentDesignResponse]);

  // ── Empty state ──────────────────────────────────────────────────────────
  if (!ingestionResponse) {
    return (
      <div className="p-6 space-y-6 max-w-7xl">
        <PageHeader
          title="Program Dashboard"
          description="Upload data to get started."
          actions={
            <Button size="sm" className="text-xs" asChild>
              <Link to="/ingestion"><Upload className="mr-1.5 h-3.5 w-3.5" /> Upload Data</Link>
            </Button>
          }
        />
        <Card>
          <CardContent className="p-12 text-center text-sm text-muted-foreground">
            No program loaded. Go to{" "}
            <Link to="/ingestion" className="text-primary underline underline-offset-2">Ingestion</Link>{" "}
            to upload your data files and run the full pipeline.
          </CardContent>
        </Card>
      </div>
    );
  }

  const uploadsForList = ps?.uploaded_files.map((f) => ({ name: f.filename, type: f.detected_type, time: "recent" })) ?? [];
  const nextActions    = experimentDesignResponse?.recommendations ?? [];
  const risks          = executionPlanningResponse?.manufacturingFlags ?? [];
  const missingControls = experimentDesignResponse?.controlSuggestions.map((c) => `${c.type}: ${c.name}`) ?? ps?.missing_data_flags ?? [];
  const readinessItems = executionPlanningResponse?.readinessItems ?? [];

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <PageHeader
        title="Program Dashboard"
        description={programData?.title ?? "Program Overview"}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="text-xs" asChild>
              <Link to="/ingestion"><Upload className="mr-1.5 h-3.5 w-3.5" /> Upload Data</Link>
            </Button>
            <Button size="sm" className="text-xs" asChild>
              <Link to="/reports">Generate Report</Link>
            </Button>
          </div>
        }
      />

      {programData && <ProgramHeroCard {...programData} />}

      {/* Workflow Progress */}
      <Card>
        <CardContent className="py-5 flex items-center justify-center">
          <WorkflowStepper steps={workflowSteps} />
        </CardContent>
      </Card>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: Actions & Controls */}
        <div className="lg:col-span-2 space-y-6">
          {nextActions.length > 0 ? (
            <div>
              <h3 className="text-sm font-semibold mb-3">Top Next Actions</h3>
              <div className="space-y-3">
                {nextActions.slice(0, 3).map((a) => (
                  <RecommendationCard key={a.title} {...a} />
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-6 text-sm text-muted-foreground text-center">
                Experiment recommendations will appear here after the pipeline completes.
              </CardContent>
            </Card>
          )}

          {missingControls.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Missing Controls</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {missingControls.slice(0, 6).map((c) => (
                    <li key={c} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-warning shrink-0" />
                      {c}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Signals from Layer 1 */}
          {ps && ps.signals.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Extracted Signals</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {ps.signals.slice(0, 8).map((s, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground font-mono">{s.kind}</span>
                      <span className="font-medium">{String(s.value)}{s.unit ? ` ${s.unit}` : ""}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: Scores, Risks, Trace */}
        <div className="space-y-6">
          {readinessItems.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Readiness Scores</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {readinessItems.map((r) => (
                  <ReadinessMeter key={r.label} label={r.label} value={r.value} />
                ))}
              </CardContent>
            </Card>
          )}

          {risks.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold mb-3">Risk & Blockers</h3>
              <div className="space-y-2">
                {risks.map((r) => (
                  <RiskFlagCard key={r.title} {...r} />
                ))}
              </div>
            </div>
          )}

          {uploadsForList.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Recent Uploads</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {uploadsForList.map((u) => (
                  <div key={u.name} className="flex items-center gap-2.5 py-1.5">
                    <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{u.name}</p>
                      <p className="text-[10px] text-muted-foreground">{u.type}</p>
                    </div>
                    <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {u.time}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {traces.length > 0 && <AgentTracePanel traces={traces} />}
        </div>
      </div>
    </div>
  );
}
