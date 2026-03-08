import { cn } from "@/lib/utils";

interface ConfidenceBadgeProps {
  value: number;
  className?: string;
}

export function ConfidenceBadge({ value, className }: ConfidenceBadgeProps) {
  const percent = Math.round(value * 100);
  const color = value >= 0.8 ? "text-success" : value >= 0.6 ? "text-warning" : "text-destructive";

  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs font-mono font-medium", color, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", value >= 0.8 ? "bg-success" : value >= 0.6 ? "bg-warning" : "bg-destructive")} />
      {percent}%
    </span>
  );
}
