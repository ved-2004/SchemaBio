import { Check, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Step {
  label: string;
  status: "complete" | "current" | "upcoming";
}

interface WorkflowStepperProps {
  steps: Step[];
  className?: string;
}

export function WorkflowStepper({ steps, className }: WorkflowStepperProps) {
  return (
    <div className={cn("flex items-center gap-0", className)}>
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center">
          <div className="flex flex-col items-center gap-1.5">
            <div
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-full border-2 text-xs font-medium transition-colors",
                step.status === "complete" && "bg-primary border-primary text-primary-foreground",
                step.status === "current" && "border-primary text-primary bg-primary/10",
                step.status === "upcoming" && "border-border text-muted-foreground"
              )}
            >
              {step.status === "complete" ? <Check className="h-3.5 w-3.5" /> : i + 1}
            </div>
            <span className={cn(
              "text-[10px] max-w-[72px] text-center leading-tight",
              step.status === "current" ? "text-foreground font-medium" : "text-muted-foreground"
            )}>
              {step.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={cn(
              "h-0.5 w-8 mx-1 mt-[-18px]",
              step.status === "complete" ? "bg-primary" : "bg-border"
            )} />
          )}
        </div>
      ))}
    </div>
  );
}
