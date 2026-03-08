import { cn } from "@/lib/utils";

interface ReadinessMeterProps {
  value: number;
  label: string;
  className?: string;
}

export function ReadinessMeter({ value, label, className }: ReadinessMeterProps) {
  const percent = Math.round(value * 100);
  const color = value >= 0.8 ? "bg-success" : value >= 0.5 ? "bg-primary" : value >= 0.3 ? "bg-warning" : "bg-destructive";

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs font-mono font-medium">{percent}%</span>
      </div>
      <div className="h-2 rounded-full bg-secondary">
        <div className={cn("h-full rounded-full transition-all duration-500", color)} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
