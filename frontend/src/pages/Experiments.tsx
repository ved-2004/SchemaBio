import { PageHeader } from "@/components/layout/PageHeader";
import { RecommendationCard } from "@/components/schemabio/RecommendationCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Lightbulb, FlaskConical, Microscope, Code } from "lucide-react";

const recommendations = [
  {
    title: "Run MIC validation across resistant isolates",
    rationale: "Compare compound hit performance by mutation subgroup. Critical for dose-response in gyrA S83L vs wildtype.",
    confidence: 0.91,
    urgency: "high" as const,
    sources: ["Assay data", "Literature"],
    expectedValue: "Define lead compound potency range",
  },
  {
    title: "Time-kill kinetics for SB-7042 and SB-7118",
    rationale: "Establish bactericidal vs bacteriostatic activity to guide downstream translational decisions.",
    confidence: 0.84,
    urgency: "medium" as const,
    sources: ["Screen results"],
    expectedValue: "Characterize killing dynamics",
  },
  {
    title: "Checkerboard synergy assay with ciprofloxacin",
    rationale: "Evaluate whether SB-7042 can restore fluoroquinolone sensitivity in resistant strains.",
    confidence: 0.79,
    urgency: "medium" as const,
    sources: ["Literature", "Hypothesis"],
    expectedValue: "Identify combination therapy potential",
  },
  {
    title: "Whole-genome sequencing of resistant isolates",
    rationale: "Confirm gyrA S83L as primary mechanism and identify any secondary resistance mutations.",
    confidence: 0.76,
    urgency: "low" as const,
    sources: ["Genomics data"],
    expectedValue: "Validate resistance mechanism model",
  },
];

const hypotheses = [
  {
    title: "SB-7042 acts as a gyrA allosteric modulator",
    evidence: "Structural modeling suggests binding at the GyrA-DNA interface adjacent to S83 position.",
    status: "testing",
  },
  {
    title: "Resistance reversal is mutation-specific",
    evidence: "Preliminary MIC data shows differential activity between S83L and D87N variants.",
    status: "supported",
  },
  {
    title: "Combination with FQ restores susceptibility",
    evidence: "Literature precedent in E. coli gyrase inhibitor combinations.",
    status: "untested",
  },
];

const bioinfTasks = [
  "Variant calling pipeline for WGS data",
  "Resistance gene annotation (AMRFinder+)",
  "Phylogenetic analysis of Burkholderia isolates",
  "Structural modeling of gyrA-compound interaction",
];

const statusColors: Record<string, string> = {
  testing: "bg-info/10 text-info border-info/20",
  supported: "bg-success/10 text-success border-success/20",
  untested: "bg-secondary text-muted-foreground border-border",
};

export default function Experiments() {
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <PageHeader
        title="Experiment Design"
        description="Evidence-linked experimental recommendations ranked by confidence and urgency."
        actions={
          <Button size="sm" className="text-xs">
            <Lightbulb className="mr-1.5 h-3.5 w-3.5" /> Generate New
          </Button>
        }
      />

      <Tabs defaultValue="recommendations">
        <TabsList>
          <TabsTrigger value="recommendations" className="text-xs">Recommendations</TabsTrigger>
          <TabsTrigger value="hypotheses" className="text-xs">Hypotheses</TabsTrigger>
          <TabsTrigger value="bioinformatics" className="text-xs">Bioinformatics</TabsTrigger>
        </TabsList>

        <TabsContent value="recommendations" className="space-y-3 mt-4">
          {recommendations.map((r) => (
            <RecommendationCard key={r.title} {...r} />
          ))}
        </TabsContent>

        <TabsContent value="hypotheses" className="space-y-3 mt-4">
          {hypotheses.map((h) => (
            <Card key={h.title} className="hover:shadow-sm transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-info/10 text-info">
                    <Microscope className="h-4 w-4" />
                  </div>
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-medium">{h.title}</h4>
                      <Badge variant="outline" className={`text-[10px] ${statusColors[h.status]}`}>
                        {h.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{h.evidence}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="bioinformatics" className="mt-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Code className="h-4 w-4 text-primary" />
                <CardTitle className="text-sm font-medium">Bioinformatics Tasks</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {bioinfTasks.map((t) => (
                  <li key={t} className="flex items-center gap-3 text-xs">
                    <span className="h-1.5 w-1.5 rounded-full bg-info shrink-0" />
                    {t}
                    <Badge variant="secondary" className="text-[10px] ml-auto">Suggested</Badge>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Control Suggestions */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-warning" />
            <CardTitle className="text-sm font-medium">Control Suggestions</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 gap-3">
            {[
              { name: "ATCC reference strain (susceptible)", type: "Positive" },
              { name: "Vehicle-only control (DMSO)", type: "Negative" },
              { name: "Ciprofloxacin (known FQ)", type: "Comparator" },
              { name: "Growth kinetics baseline", type: "Baseline" },
            ].map((c) => (
              <div key={c.name} className="flex items-center gap-2.5 p-3 rounded-lg bg-secondary/50 border border-border">
                <Badge variant="outline" className="text-[10px] shrink-0">{c.type}</Badge>
                <span className="text-xs">{c.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
