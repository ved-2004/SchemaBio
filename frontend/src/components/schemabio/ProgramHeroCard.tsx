import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StageBadge } from "./StageBadge";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { cn } from "@/lib/utils";
import { Dna, Target, FlaskConical, Bug, TestTube } from "lucide-react";

interface ProgramHeroCardProps {
  title: string;
  stage: string;
  confidence: number;
  summary: string;
  entities: { organism: string; target: string; compound: string; variant: string; assay: string };
  className?: string;
}

const entityIcons = [
  { key: "organism", icon: Bug, label: "Organism" },
  { key: "target", icon: Target, label: "Target" },
  { key: "compound", icon: FlaskConical, label: "Compound" },
  { key: "variant", icon: Dna, label: "Variant" },
  { key: "assay", icon: TestTube, label: "Assay" },
] as const;

export function ProgramHeroCard({ title, stage, confidence, summary, entities, className }: ProgramHeroCardProps) {
  return (
    <Card className={cn("", className)}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
              <StageBadge stage={stage} />
            </div>
            <div className="flex items-center gap-3">
              <ConfidenceBadge value={confidence} />
              <span className="text-xs text-muted-foreground">Program confidence</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">{summary}</p>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-5 pt-5 border-t border-border">
          {entityIcons.map(({ key, icon: Icon, label }) => (
            <div key={key} className="flex items-center gap-2 p-2.5 rounded-lg bg-secondary/50">
              <Icon className="h-4 w-4 text-primary shrink-0" />
              <div className="min-w-0">
                <p className="text-[10px] text-muted-foreground">{label}</p>
                <p className="text-xs font-medium truncate">{entities[key as keyof typeof entities]}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
