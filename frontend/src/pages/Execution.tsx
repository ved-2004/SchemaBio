import { PageHeader } from "@/components/layout/PageHeader";
import { ReadinessMeter } from "@/components/schemabio/ReadinessMeter";
import { RiskFlagCard } from "@/components/schemabio/RiskFlagCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Building2, CheckCircle2, Circle, DollarSign, Factory, Loader2, Shield, Users, RefreshCw,
} from "lucide-react";
import { useIngestion } from "@/contexts/IngestionContext";

export default function Execution() {
  const { executionPlanningResponse, isLoadingLayer3, layer3Error, retryPipeline } = useIngestion();

  // ── Loading ────────────────────────────────────────────────────────────────
  if (isLoadingLayer3) {
    return (
      <div className="p-6 flex flex-col items-center justify-center gap-3 min-h-[40vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Running translational planning analysis…</p>
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (layer3Error) {
    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <PageHeader
          title="Execution Planning"
          description="CRO recommendations, evidence checklist, funding opportunities, and translational readiness."
        />
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="p-4 flex items-center justify-between">
            <span className="text-sm text-destructive">Layer 3 pipeline error: {layer3Error}</span>
            <Button variant="outline" size="sm" className="text-xs ml-4 shrink-0" onClick={retryPipeline}>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── No data yet ────────────────────────────────────────────────────────────
  if (!executionPlanningResponse) {
    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <PageHeader
          title="Execution Planning"
          description="CRO recommendations, evidence checklist, funding opportunities, and translational readiness."
        />
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground text-center">
            Upload or load demo data on the Ingestion page to generate the execution roadmap.
          </CardContent>
        </Card>
      </div>
    );
  }

  const readinessItems = executionPlanningResponse.readinessItems ?? [];
  const croTypes = executionPlanningResponse.croTypes ?? [];
  const grants = executionPlanningResponse.grants ?? [];
  const evidenceChecklist = executionPlanningResponse.evidenceChecklist ?? [];
  const manufacturingFlags = executionPlanningResponse.manufacturingFlags ?? [];

  const doneCount = evidenceChecklist.filter((e) => e?.done).length;

  // ── Loaded ─────────────────────────────────────────────────────────────────
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <PageHeader
        title="Execution Planning"
        description="CRO recommendations, evidence checklist, funding opportunities, and translational readiness."
        actions={
          <Button size="sm" className="text-xs" disabled>
            <Shield className="mr-1.5 h-3.5 w-3.5" /> Readiness Report
          </Button>
        }
      />

      {/* Readiness Overview */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Translational Readiness</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {readinessItems.map((r) => (
            <ReadinessMeter key={r.label} {...r} />
          ))}
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* CRO Recommendations */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-primary" />
              <CardTitle className="text-sm font-medium">CRO / Lab Partner Types</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {croTypes.map((c) => (
              <div
                key={c.type}
                className="flex items-start gap-3 p-3 rounded-lg bg-secondary/30 border border-border"
              >
                <Building2 className="h-4 w-4 text-muted-foreground mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium">{c.type}</span>
                    <Badge variant="outline" className="text-[10px]">{c.urgency}</Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{c.desc}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Funding */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-success" />
              <CardTitle className="text-sm font-medium">Relevant Funding</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {grants.map((g) => (
              <div
                key={g.name}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border"
              >
                <div>
                  <span className="text-xs font-medium">{g.name}</span>
                  <p className="text-[11px] text-muted-foreground">{g.focus} · {g.stage}</p>
                </div>
                <Badge
                  variant={g.fit === "High" ? "default" : "secondary"}
                  className="text-[10px]"
                >
                  {g.fit} fit
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Evidence Checklist */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Evidence Package Checklist</CardTitle>
            <span className="text-xs text-muted-foreground font-mono">
              {doneCount}/{evidenceChecklist.length} complete
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 gap-2">
            {evidenceChecklist.map((e) => (
              <div key={e.item} className="flex items-center gap-2.5 py-1.5">
                {e.done ? (
                  <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                ) : (
                  <Circle className="h-4 w-4 text-muted-foreground/40 shrink-0" />
                )}
                <span className={`text-xs ${e.done ? "text-foreground" : "text-muted-foreground"}`}>
                  {e.item}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Manufacturing Flags */}
      {manufacturingFlags.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Factory className="h-4 w-4 text-muted-foreground" />
            Manufacturability Flags
          </h3>
          <div className="space-y-2">
            {manufacturingFlags.map((f) => (
              <RiskFlagCard key={f.title} {...f} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
