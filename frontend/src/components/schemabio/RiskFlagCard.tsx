import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskFlagCardProps {
  title: string;
  description: string;
  severity: "critical" | "warning" | "info";
  className?: string;
}

const severityConfig = {
  critical: { icon: ShieldAlert, bg: "bg-destructive/10", text: "text-destructive", border: "border-destructive/20" },
  warning: { icon: AlertTriangle, bg: "bg-warning/10", text: "text-warning", border: "border-warning/20" },
  info: { icon: AlertTriangle, bg: "bg-info/10", text: "text-info", border: "border-info/20" },
};

export function RiskFlagCard({ title, description, severity, className }: RiskFlagCardProps) {
  const config = severityConfig[severity];
  const Icon = config.icon;

  return (
    <Card className={cn("border", config.border, className)}>
      <CardContent className="p-3 flex items-start gap-3">
        <div className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-md", config.bg)}>
          <Icon className={cn("h-3.5 w-3.5", config.text)} />
        </div>
        <div>
          <h4 className="text-xs font-medium">{title}</h4>
          <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}
