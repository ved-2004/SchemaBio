import { useMemo } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { ProgramHeroCard } from "@/components/schemabio/ProgramHeroCard";
import { WorkflowStepper } from "@/components/schemabio/WorkflowStepper";
import { ReadinessMeter } from "@/components/schemabio/ReadinessMeter";
import { RiskFlagCard } from "@/components/schemabio/RiskFlagCard";
import { RecommendationCard } from "@/components/schemabio/RecommendationCard";
import { ChartCard } from "@/components/schemabio/ChartCard";
import { DataTableCard } from "@/components/schemabio/DataTableCard";
import { AgentTracePanel } from "@/components/schemabio/AgentTracePanel";
import { EvidenceCard } from "@/components/schemabio/EvidenceCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload, FileSpreadsheet, Clock } from "lucide-react";
import { useIngestion } from "@/contexts/IngestionContext";
import { MOCK_INGESTION_RESPONSE } from "@/lib/mockIngestionResponse";

// TODO: Replace with data from real ingestion API. Dashboard consumes ingestionResponse from context.
function useDashboardData() {
  const { ingestionResponse } = useIngestion();
  const data = ingestionResponse ?? MOCK_INGESTION_RESPONSE;
  const ps = data.program_state;
  const expIn = data.experiment_design_input;
  const execIn = data.execution_planning_input;

  return useMemo(() => {
    const organism = ps.entities.find((e) => e.type === "organism")?.value ?? "—";
    const target = ps.entities.find((e) => e.type === "target" || e.type === "target_gene" || e.type === "mutation")?.value ?? "—";
    const compound = ps.entities.find((e) => e.type === "compound")?.value ?? "—";
    const assay = ps.entities.find((e) => e.type === "assay_type")?.value ?? "—";
    const programData = {
      title: "Gyrase Inhibitor Program — Compound-14",
      stage: ps.stage_estimate?.name?.replace(/_/g, " ") ?? "Resistance Characterization",
      confidence: ps.stage_estimate?.confidence ?? 0.93,
      summary: expIn.biological_context,
      entities: {
        organism,
        target: target + (ps.entities.find((e) => e.type === "variant" || e.type === "mutation") ? ` (${ps.entities.find((e) => e.type === "variant" || e.type === "mutation")?.value ?? ""})` : ""),
        compound,
        variant: ps.entities.filter((e) => e.type === "variant" || e.type === "mutation").map((e) => e.value).join(", ") || "—",
        assay: assay || "MIC / compound screen",
      },
    };
    return { data: programData, ps, expIn, execIn, recentUploads: ps.uploaded_files };
  }, [ps, expIn, execIn]);
}

const workflowSteps = [
  { label: "Ingestion", status: "complete" as const },
  { label: "Stage Detection", status: "complete" as const },
  { label: "Exp. Validation", status: "current" as const },
  { label: "Preclinical", status: "upcoming" as const },
  { label: "Manufacturing", status: "upcoming" as const },
];

const nextActions = [
  {
    title: "Run MIC validation across resistant isolates",
    rationale: "Compare compound hit performance by mutation subgroup. Critical for establishing dose-response relationship in gyrA D87N vs wildtype.",
    confidence: 0.91,
    urgency: "high" as const,
    sources: ["Assay data", "Literature"],
    expectedValue: "Define lead compound potency range",
  },
  {
    title: "Time-kill kinetics for top 2 compounds",
    rationale: "Establish bactericidal vs bacteriostatic activity. Required for downstream translational planning.",
    confidence: 0.84,
    urgency: "medium" as const,
    sources: ["Screen results"],
    expectedValue: "Characterize killing dynamics",
  },
];

const risks = [
  { title: "ADMET package incomplete", description: "Cytotoxicity and metabolic stability data not yet available for Compound-14.", severity: "warning" as const },
  { title: "Reproducibility gap", description: "Initial MIC data from single lab. Independent replication needed before CRO engagement.", severity: "critical" as const },
  { title: "CDMO not ready", description: "Not ready for CDMO engagement until ADMET and reproducibility package are complete.", severity: "info" as const },
];

const missingControls = [
  "Wildtype susceptible strain control (ATCC reference)",
  "Solvent-only vehicle control for Compound-14",
  "Positive control antibiotic (ciprofloxacin)",
  "Growth kinetics baseline control",
];

const traces = [
  { step: "Schema Detection", detail: "Detected MIC assay CSV, compound screen CSV, VCF. Organism and target columns identified.", timestamp: "2m ago" },
  { step: "Entity Extraction", detail: "Extracted: E. coli, GyrA, D87N, parC S80I, Compound-14, MIC 0.125 μg/mL, IC50 32 nM.", timestamp: "2m ago" },
  { step: "Stage Classification", detail: "Program classified as Resistance Characterization (confidence: 0.93). Key signal: 64× fold-shift, mechanism uncharacterized.", timestamp: "1m ago" },
  { step: "Action Generation", detail: "Generated recommended actions. Top priority: characterize resistance mechanism.", timestamp: "45s ago" },
];

const tableData = [
  { compound: "Compound-14", mic_wt: "0.125 μg/mL", mic_mut: "8 μg/mL", fold_change: "64×", status: <Badge variant="secondary" className="text-[10px]">Lead</Badge> },
  { compound: "Compound-31", mic_wt: "0.06 μg/mL", mic_mut: "2 μg/mL", fold_change: "33×", status: <Badge variant="outline" className="text-[10px]">Backup</Badge> },
  { compound: "Ciprofloxacin", mic_wt: "0.03 μg/mL", mic_mut: ">32 μg/mL", fold_change: ">1000×", status: <Badge variant="outline" className="text-[10px] text-muted-foreground">Comparator</Badge> },
];

export default function Dashboard() {
  const { data: programData, recentUploads } = useDashboardData();
  const uploadsForList = recentUploads.map((f) => ({ name: f.filename, type: f.detected_type, time: "recent" }));

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <PageHeader
        title="Program Dashboard"
        description={programData.title}
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

      <ProgramHeroCard {...programData} />

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
          <div>
            <h3 className="text-sm font-semibold mb-3">Top Next Actions</h3>
            <div className="space-y-3">
              {nextActions.map((a) => (
                <RecommendationCard key={a.title} {...a} />
              ))}
            </div>
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Missing Controls</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {missingControls.map((c) => (
                  <li key={c} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="mt-1 h-1.5 w-1.5 rounded-full bg-warning shrink-0" />
                    {c}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Tabs defaultValue="chart">
            <TabsList>
              <TabsTrigger value="chart" className="text-xs">MIC Distribution</TabsTrigger>
              <TabsTrigger value="table" className="text-xs">Compound Data</TabsTrigger>
            </TabsList>
            <TabsContent value="chart">
              <ChartCard title="MIC Distribution by Mutation Subgroup" description="Compound performance across gyrA variants" />
            </TabsContent>
            <TabsContent value="table">
              <DataTableCard
                title="Compound Screening Results"
                columns={[
                  { key: "compound", label: "Compound" },
                  { key: "mic_wt", label: "MIC (WT)" },
                  { key: "mic_mut", label: "MIC (Mutant)" },
                  { key: "fold_change", label: "Fold Change" },
                  { key: "status", label: "Status" },
                ]}
                data={tableData}
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Right: Scores, Risks, Trace */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Readiness Scores</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ReadinessMeter value={0.65} label="Evidence Score" />
              <ReadinessMeter value={0.42} label="Translational Readiness" />
              <ReadinessMeter value={0.15} label="Manufacturing Readiness" />
              <ReadinessMeter value={0.78} label="Data Completeness" />
            </CardContent>
          </Card>

          <div>
            <h3 className="text-sm font-semibold mb-3">Risk & Blockers</h3>
            <div className="space-y-2">
              {risks.map((r) => (
                <RiskFlagCard key={r.title} {...r} />
              ))}
            </div>
          </div>

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

          <AgentTracePanel traces={traces} />

          <EvidenceCard
            title="gyrA mutations in fluoroquinolone resistance"
            summary="D87N substitution in gyrA confers high-level FQ resistance in E. coli through altered DNA gyrase binding. Compound-14 (32 nM) vs published 890 nM for quinolones."
            source="J Antimicrob Chemother, 2023"
            relevance={0.94}
            tags={["gyrA", "resistance", "E. coli", "Compound-14"]}
          />
        </div>
      </div>
    </div>
  );
}
