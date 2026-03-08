import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { BookOpen, ExternalLink } from "lucide-react";

interface EvidenceCardProps {
  title: string;
  summary: string;
  source: string;
  relevance: number;
  tags: string[];
  className?: string;
}

export function EvidenceCard({ title, summary, source, relevance, tags, className }: EvidenceCardProps) {
  return (
    <Card className={cn("hover:shadow-sm transition-shadow", className)}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-info/10 text-info">
            <BookOpen className="h-4 w-4" />
          </div>
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-sm font-medium leading-tight">{title}</h4>
              <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">{summary}</p>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] text-muted-foreground">{source}</span>
              <span className="text-[10px] font-mono text-primary">rel: {Math.round(relevance * 100)}%</span>
              {tags.map((t) => (
                <Badge key={t} variant="secondary" className="text-[10px] font-normal">{t}</Badge>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
