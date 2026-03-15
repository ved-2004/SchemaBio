import { PageHeader } from "@/components/layout/PageHeader";
import { ReadinessMeter } from "@/components/schemabio/ReadinessMeter";
import { StageBadge } from "@/components/schemabio/StageBadge";
import { ConfidenceBadge } from "@/components/schemabio/ConfidenceBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Download, Printer, Loader2 } from "lucide-react";
import { useIngestion } from "@/contexts/IngestionContext";

export default function Reports() {
  const {
    ingestionResponse,
    experimentDesignResponse,
    executionPlanningResponse,
    isPipelineRunning,
  } = useIngestion();

  // ── Loading ──
  if (isPipelineRunning) {
    return (
      <div className="p-6 flex flex-col items-center justify-center gap-3 min-h-[40vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Generating program report…</p>
      </div>
    );
  }

  // ── No data ──
  if (!ingestionResponse) {
    return (
      <div className="p-6 space-y-6 max-w-4xl">
        <PageHeader
          title="Program Report"
          description="Executive summary and translational execution roadmap."
        />
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground text-center">
            Upload or load demo data on the Ingestion page to generate the program report.
          </CardContent>
        </Card>
      </div>
    );
  }

  const ps = ingestionResponse.program_state;
  const entities = ps.entities ?? [];
  const signals = ps.signals ?? [];
  const stage = ps.stage_estimate;
  const missingFlags = ps.missing_data_flags ?? [];

  const recommendations = experimentDesignResponse?.recommendations ?? [];
  const readinessItems = executionPlanningResponse?.readinessItems ?? [];
  const evidenceChecklist = executionPlanningResponse?.evidenceChecklist ?? [];
  const manufacturingFlags = executionPlanningResponse?.manufacturingFlags ?? [];
  const grants = executionPlanningResponse?.grants ?? [];
  const croTypes = executionPlanningResponse?.croTypes ?? [];

  // Derive entity summary
  const organisms = entities.filter(e => e.type === "organism");
  const targets = entities.filter(e => e.type === "target");
  const compounds = entities.filter(e => e.type === "compound");

  const doneCount = evidenceChecklist.filter(e => e?.done).length;

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <PageHeader
        title="Program Report"
        description="Executive summary and translational execution roadmap."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="text-xs" onClick={() => window.print()}>
              <Printer className="mr-1.5 h-3.5 w-3.5" /> Print
            </Button>
            <Button size="sm" className="text-xs" onClick={() => window.print()}>
              <Download className="mr-1.5 h-3.5 w-3.5" /> Export PDF
            </Button>
          </div>
        }
      />

      {/* Executive Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold">Executive Summary</CardTitle>
            <div className="flex items-center gap-2">
              {stage && <StageBadge stage={stage.name} />}
              {stage && <ConfidenceBadge value={stage.confidence} />}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Program</h4>
            <p className="text-sm">Program ID: {ps.program_id}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {stage?.reasoning_basis || `${entities.length} entities extracted from ${(ps.uploaded_files ?? []).length} uploaded files.`}
            </p>
          </div>

          <Separator />

          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Key Entities</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: "Organism", value: organisms.map(e => e.value).join(", ") || "—" },
                { label: "Target", value: targets.map(e => e.value).join(", ") || "—" },
                { label: "Lead Compound", value: compounds[0]?.value ?? "—" },
                { label: "Data Sources", value: `${(ps.uploaded_files ?? []).length} files ingested` },
                { label: "Entities Extracted", value: String(entities.length) },
                { label: "Signals Detected", value: String(signals.length) },
              ].map((e) => (
                <div key={e.label}>
                  <p className="text-[10px] text-muted-foreground">{e.label}</p>
                  <p className="text-xs font-medium">{e.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Readiness */}
          {readinessItems.length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Readiness</h4>
                <div className="space-y-3">
                  {readinessItems.map((r) => (
                    <ReadinessMeter key={r.label} {...r} />
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Recommended Experiments */}
          {recommendations.length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Recommended Next Experiments</h4>
                <ol className="space-y-2">
                  {recommendations.slice(0, 5).map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs">
                      <span className="font-mono text-primary font-medium shrink-0">{i + 1}.</span>
                      <span>
                        <span className="font-medium">{r.title}</span>
                        {r.rationale && <span className="text-muted-foreground"> — {r.rationale}</span>}
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            </>
          )}

          {/* Translational Roadmap */}
          {(croTypes.length > 0 || grants.length > 0) && (
            <>
              <Separator />
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Translational Execution Roadmap</h4>
                <div className="space-y-3">
                  {croTypes.length > 0 && (
                    <div>
                      <Badge variant="secondary" className="text-[10px] mb-1.5">CRO / Partners</Badge>
                      <ul className="space-y-1 ml-1">
                        {croTypes.slice(0, 3).map((c) => (
                          <li key={c.type} className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="h-1 w-1 rounded-full bg-primary shrink-0" />
                            {c.type} — {c.desc}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {grants.length > 0 && (
                    <div>
                      <Badge variant="secondary" className="text-[10px] mb-1.5">Funding Opportunities</Badge>
                      <ul className="space-y-1 ml-1">
                        {grants.slice(0, 3).map((g) => (
                          <li key={g.name} className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="h-1 w-1 rounded-full bg-success shrink-0" />
                            {g.name} — {g.focus} ({g.fit} fit)
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {evidenceChecklist.length > 0 && (
                    <div>
                      <Badge variant="secondary" className="text-[10px] mb-1.5">
                        Evidence Package ({doneCount}/{evidenceChecklist.length})
                      </Badge>
                      <ul className="space-y-1 ml-1">
                        {evidenceChecklist.filter(e => !e.done).slice(0, 4).map((e) => (
                          <li key={e.item} className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="h-1 w-1 rounded-full bg-warning shrink-0" />
                            {e.item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Critical Blockers */}
          {(missingFlags.length > 0 || manufacturingFlags.length > 0) && (
            <>
              <Separator />
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Critical Blockers</h4>
                <ul className="space-y-1.5">
                  {missingFlags.map((flag) => (
                    <li key={flag} className="text-xs text-muted-foreground flex items-start gap-2">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-destructive shrink-0" />
                      {flag}
                    </li>
                  ))}
                  {manufacturingFlags.map((f) => (
                    <li key={f.title} className="text-xs text-muted-foreground flex items-start gap-2">
                      <span className={`mt-1 h-1.5 w-1.5 rounded-full shrink-0 ${f.severity === "critical" ? "bg-destructive" : "bg-warning"}`} />
                      {f.title} — {f.description}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
