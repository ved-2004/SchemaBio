import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ArrowRight, Lightbulb } from "lucide-react";
import { ConfidenceBadge } from "./ConfidenceBadge";

interface RecommendationCardProps {
  title: string;
  rationale: string;
  confidence: number;
  urgency: "high" | "medium" | "low";
  sources: string[];
  expectedValue?: string;
  className?: string;
}

const urgencyStyles = {
  high: "bg-destructive/10 text-destructive border-destructive/20",
  medium: "bg-warning/10 text-warning border-warning/20",
  low: "bg-info/10 text-info border-info/20",
};

export function RecommendationCard({
  title, rationale, confidence, urgency, sources, expectedValue, className,
}: RecommendationCardProps) {
  return (
    <Card className={cn("hover:shadow-md transition-shadow cursor-pointer group", className)}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Lightbulb className="h-4 w-4" />
            </div>
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="text-sm font-medium leading-tight">{title}</h4>
                <Badge variant="outline" className={cn("text-[10px]", urgencyStyles[urgency])}>
                  {urgency}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{rationale}</p>
              <div className="flex items-center gap-2 flex-wrap pt-1">
                <ConfidenceBadge value={confidence} />
                {sources.map((s) => (
                  <Badge key={s} variant="secondary" className="text-[10px] font-normal">{s}</Badge>
                ))}
              </div>
              {expectedValue && (
                <p className="text-[10px] text-muted-foreground pt-1">Expected value: {expectedValue}</p>
              )}
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity mt-1" />
        </div>
      </CardContent>
    </Card>
  );
}
