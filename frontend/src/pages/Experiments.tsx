import { PageHeader } from "@/components/layout/PageHeader";
import { RecommendationCard } from "@/components/schemabio/RecommendationCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Lightbulb, FlaskConical, Microscope, Code, Loader2 } from "lucide-react";
import { useIngestion } from "@/contexts/IngestionContext";

const statusColors: Record<string, string> = {
  testing:  "bg-info/10 text-info border-info/20",
  supported: "bg-success/10 text-success border-success/20",
  untested: "bg-secondary text-muted-foreground border-border",
};

export default function Experiments() {
  const { experimentDesignResponse, isLoadingLayer2, layer2Error } = useIngestion();

  // ── Loading state ──────────────────────────────────────────────────────────
  if (isLoadingLayer2) {
    return (
      <div className="p-6 flex flex-col items-center justify-center gap-3 min-h-[40vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Running experiment design analysis…</p>
      </div>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (layer2Error) {
    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <PageHeader
          title="Experiment Design"
          description="Evidence-linked experimental recommendations ranked by confidence and urgency."
        />
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="p-4 text-sm text-destructive">
            Layer 2 pipeline error: {layer2Error}
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── No data yet ────────────────────────────────────────────────────────────
  if (!experimentDesignResponse) {
    return (
      <div className="p-6 space-y-6 max-w-5xl">
        <PageHeader
          title="Experiment Design"
          description="Evidence-linked experimental recommendations ranked by confidence and urgency."
        />
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground text-center">
            Upload or load demo data on the Ingestion page to generate experiment recommendations.
          </CardContent>
        </Card>
      </div>
    );
  }

  const recommendations = experimentDesignResponse.recommendations ?? [];
  const hypotheses = experimentDesignResponse.hypotheses ?? [];
  const bioinfTasks = experimentDesignResponse.bioinfTasks ?? [];
  const controlSuggestions = experimentDesignResponse.controlSuggestions ?? [];

  // ── Loaded ─────────────────────────────────────────────────────────────────
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <PageHeader
        title="Experiment Design"
        description="Evidence-linked experimental recommendations ranked by confidence and urgency."
        actions={
          <Button size="sm" className="text-xs" disabled>
            <Lightbulb className="mr-1.5 h-3.5 w-3.5" /> Generate New
          </Button>
        }
      />

      <Tabs defaultValue="recommendations">
        <TabsList>
          <TabsTrigger value="recommendations" className="text-xs">Recommendations</TabsTrigger>
          <TabsTrigger value="hypotheses"      className="text-xs">Hypotheses</TabsTrigger>
          <TabsTrigger value="bioinformatics"  className="text-xs">Bioinformatics</TabsTrigger>
        </TabsList>

        {/* Recommendations */}
        <TabsContent value="recommendations" className="space-y-3 mt-4">
          {recommendations.map((r) => (
            <RecommendationCard key={r.title} {...r} />
          ))}
        </TabsContent>

        {/* Hypotheses */}
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
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${statusColors[h.status]}`}
                      >
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

        {/* Bioinformatics */}
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
      {controlSuggestions.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-warning" />
              <CardTitle className="text-sm font-medium">Control Suggestions</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 gap-3">
              {controlSuggestions.map((c) => (
                <div
                  key={c.name}
                  className="flex items-center gap-2.5 p-3 rounded-lg bg-secondary/50 border border-border"
                >
                  <Badge variant="outline" className="text-[10px] shrink-0">{c.type}</Badge>
                  <span className="text-xs">{c.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
