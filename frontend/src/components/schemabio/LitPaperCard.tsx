import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { FileText, ExternalLink } from "lucide-react";

interface LitPaperCardProps {
  title: string;
  authors: string;
  journal: string;
  year: number;
  relevance: string;
  tags: string[];
  className?: string;
}

export function LitPaperCard({ title, authors, journal, year, relevance, tags, className }: LitPaperCardProps) {
  return (
    <Card className={cn("hover:shadow-sm transition-shadow cursor-pointer group", className)}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
            <FileText className="h-4 w-4" />
          </div>
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-sm font-medium leading-tight group-hover:text-primary transition-colors">{title}</h4>
              <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-[11px] text-muted-foreground">{authors}</p>
            <p className="text-[10px] text-muted-foreground">{journal} · {year}</p>
            <p className="text-xs text-foreground/80 mt-1">{relevance}</p>
            <div className="flex items-center gap-1.5 flex-wrap pt-1">
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
