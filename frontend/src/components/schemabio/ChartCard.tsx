import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface ChartCardProps {
  title: string;
  description?: string;
  children?: ReactNode;
  className?: string;
  action?: ReactNode;
}

export function ChartCard({ title, description, children, className, action }: ChartCardProps) {
  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
            {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
          </div>
          {action}
        </div>
      </CardHeader>
      <CardContent>
        {children || (
          <div className="flex h-[200px] items-center justify-center rounded-lg bg-secondary/30 border border-dashed border-border">
            <p className="text-xs text-muted-foreground">Chart visualization ready</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
