import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface StageBadgeProps {
  stage: string;
  className?: string;
}

const stageColors: Record<string, string> = {
  "Hit Discovery": "bg-info/10 text-info border-info/20",
  "Resistance Characterization": "bg-warning/10 text-warning border-warning/20",
  "Experimental Validation": "bg-primary/10 text-primary border-primary/20",
  "Preclinical Gap Analysis": "bg-warning/10 text-warning border-warning/20",
  "Manufacturing Review": "bg-success/10 text-success border-success/20",
};

export function StageBadge({ stage, className }: StageBadgeProps) {
  const colorClass = stageColors[stage] || "bg-secondary text-secondary-foreground border-border";
  return (
    <Badge variant="outline" className={cn("font-medium text-xs", colorClass, className)}>
      {stage}
    </Badge>
  );
}
