import { PageHeader } from "@/components/layout/PageHeader";
import { ReadinessMeter } from "@/components/schemabio/ReadinessMeter";
import { StageBadge } from "@/components/schemabio/StageBadge";
import { ConfidenceBadge } from "@/components/schemabio/ConfidenceBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Download, Printer } from "lucide-react";

export default function Reports() {
  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <PageHeader
        title="Program Report"
        description="Executive summary and translational execution roadmap."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="text-xs">
              <Printer className="mr-1.5 h-3.5 w-3.5" /> Print
            </Button>
            <Button size="sm" className="text-xs">
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
              <StageBadge stage="Experimental Validation" />
              <ConfidenceBadge value={0.87} />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Program</h4>
            <p className="text-sm">Fluoroquinolone Resistance Reversal Program</p>
            <p className="text-xs text-muted-foreground mt-1">
              Investigating gyrA-associated fluoroquinolone resistance pathways in Burkholderia species.
              Three compound hits identified. Program is in experimental validation phase.
            </p>
          </div>

          <Separator />

          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Key Entities</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: "Organism", value: "Burkholderia cenocepacia" },
                { label: "Target", value: "gyrA (S83L)" },
                { label: "Lead Compound", value: "SB-7042" },
                { label: "Assay Type", value: "MIC / Kill curve" },
                { label: "Data Sources", value: "4 files ingested" },
                { label: "Entities Extracted", value: "23" },
              ].map((e) => (
                <div key={e.label}>
                  <p className="text-[10px] text-muted-foreground">{e.label}</p>
                  <p className="text-xs font-medium">{e.value}</p>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Readiness</h4>
            <div className="space-y-3">
              <ReadinessMeter value={0.65} label="Evidence Score" />
              <ReadinessMeter value={0.42} label="Translational Readiness" />
              <ReadinessMeter value={0.15} label="Manufacturing Readiness" />
            </div>
          </div>

          <Separator />

          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Recommended Next Experiments</h4>
            <ol className="space-y-2">
              {[
                "Run MIC validation across resistant isolates — compare by mutation subgroup",
                "Time-kill kinetics for SB-7042 and SB-7118",
                "Checkerboard synergy assay with ciprofloxacin",
                "Initiate ADMET panel (cytotoxicity + metabolic stability)",
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-xs">
                  <span className="font-mono text-primary font-medium shrink-0">{i + 1}.</span>
                  {item}
                </li>
              ))}
            </ol>
          </div>

          <Separator />

          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Translational Execution Roadmap</h4>
            <div className="space-y-3">
              {[
                { phase: "Current", items: ["Complete MIC validation", "Generate time-kill data", "Begin ADMET screening"] },
                { phase: "Next 3 months", items: ["Independent lab replication", "WGS of isolate panel", "CRO engagement for ADMET"] },
                { phase: "6–12 months", items: ["In vivo efficacy study", "Scale-up synthesis route", "Pre-IND regulatory meeting"] },
              ].map((p) => (
                <div key={p.phase}>
                  <Badge variant="secondary" className="text-[10px] mb-1.5">{p.phase}</Badge>
                  <ul className="space-y-1 ml-1">
                    {p.items.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="h-1 w-1 rounded-full bg-primary shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Critical Blockers</h4>
            <ul className="space-y-1.5">
              <li className="text-xs text-muted-foreground flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-destructive shrink-0" />
                ADMET package incomplete — cytotoxicity and metabolic stability data not yet available
              </li>
              <li className="text-xs text-muted-foreground flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-destructive shrink-0" />
                No independent replication — single-lab data only
              </li>
              <li className="text-xs text-muted-foreground flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-warning shrink-0" />
                CDMO engagement not feasible until ADMET + reproducibility resolved
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
