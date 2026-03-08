import { cn } from "@/lib/utils";
import { Beaker, FlaskConical } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: "beaker" | "flask";
  className?: string;
  children?: React.ReactNode;
}

export function EmptyState({ title, description, icon = "beaker", className, children }: EmptyStateProps) {
  const Icon = icon === "flask" ? FlaskConical : Beaker;

  return (
    <div className={cn("flex flex-col items-center justify-center py-16 px-4", className)}>
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary mb-4">
        <Icon className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="text-xs text-muted-foreground mt-1 text-center max-w-sm">{description}</p>
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}
