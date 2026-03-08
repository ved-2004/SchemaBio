import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Bot, ChevronRight } from "lucide-react";

interface TraceEntry {
  step: string;
  detail: string;
  timestamp: string;
}

interface AgentTracePanelProps {
  traces: TraceEntry[];
  className?: string;
}

export function AgentTracePanel({ traces, className }: AgentTracePanelProps) {
  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm font-medium">Agent Reasoning Trace</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-0">
        {traces.map((trace, i) => (
          <div key={i} className="flex items-start gap-2.5 py-2.5 border-b border-border last:border-0">
            <ChevronRight className="h-3 w-3 mt-0.5 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium">{trace.step}</span>
                <span className="text-[10px] text-muted-foreground font-mono shrink-0">{trace.timestamp}</span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">{trace.detail}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
