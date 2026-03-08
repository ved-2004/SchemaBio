import { PageHeader } from "@/components/layout/PageHeader";
import { ReadinessMeter } from "@/components/schemabio/ReadinessMeter";
import { RiskFlagCard } from "@/components/schemabio/RiskFlagCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Building2, CheckCircle2, Circle, DollarSign, Factory, Shield, Truck, Users,
} from "lucide-react";

const readinessItems = [
  { label: "Evidence Package", value: 0.65 },
  { label: "ADMET Completion", value: 0.20 },
  { label: "Reproducibility", value: 0.35 },
  { label: "Regulatory Alignment", value: 0.10 },
  { label: "Manufacturing Readiness", value: 0.08 },
];

const croTypes = [
  { type: "Microbiology CRO", desc: "MIC validation, time-kill, checkerboard assays", urgency: "Needed now", icon: Users },
  { type: "ADMET Testing Lab", desc: "Cytotoxicity, metabolic stability, hERG screening", urgency: "Next phase", icon: Building2 },
  { type: "WGS Service Provider", desc: "Whole-genome sequencing of resistant isolates", urgency: "Suggested", icon: Building2 },
];

const grants = [
  { name: "CARB-X", focus: "Antibacterial therapeutics", stage: "Preclinical", fit: "High" },
  { name: "NIH R21", focus: "Antimicrobial resistance", stage: "Early discovery", fit: "Medium" },
  { name: "Wellcome Trust", focus: "Drug-resistant infections", stage: "Translational", fit: "Medium" },
];

const evidenceChecklist = [
  { item: "MIC data across ≥3 resistant strains", done: true },
  { item: "Compound selectivity index", done: false },
  { item: "ADMET / cytotoxicity panel", done: false },
  { item: "Independent lab replication", done: false },
  { item: "Mechanism of action evidence", done: true },
  { item: "In vivo efficacy (mouse model)", done: false },
  { item: "Scale-up synthesis feasibility", done: false },
  { item: "Regulatory pre-IND meeting", done: false },
];

const manufacturingFlags = [
  { title: "Synthesis complexity", description: "SB-7042 requires 7-step synthesis. Scale-up route not optimized.", severity: "warning" as const },
  { title: "No GMP process defined", description: "Current synthesis is research-grade only. CMC work required.", severity: "critical" as const },
  { title: "Supply chain risk", description: "Key intermediate sourced from single supplier. Dual-sourcing recommended.", severity: "warning" as const },
];

export default function Execution() {
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <PageHeader
        title="Execution Planning"
        description="CRO recommendations, evidence checklist, funding opportunities, and translational readiness."
        actions={
          <Button size="sm" className="text-xs">
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
              <div key={c.type} className="flex items-start gap-3 p-3 rounded-lg bg-secondary/30 border border-border">
                <c.icon className="h-4 w-4 text-muted-foreground mt-0.5" />
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
              <div key={g.name} className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border">
                <div>
                  <span className="text-xs font-medium">{g.name}</span>
                  <p className="text-[11px] text-muted-foreground">{g.focus} · {g.stage}</p>
                </div>
                <Badge variant={g.fit === "High" ? "default" : "secondary"} className="text-[10px]">{g.fit} fit</Badge>
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
              {evidenceChecklist.filter((e) => e.done).length}/{evidenceChecklist.length} complete
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
                <span className={`text-xs ${e.done ? "text-foreground" : "text-muted-foreground"}`}>{e.item}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Manufacturing */}
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
    </div>
  );
}
