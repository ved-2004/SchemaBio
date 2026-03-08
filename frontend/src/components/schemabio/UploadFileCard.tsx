import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Upload, FileSpreadsheet, FileText, File, Check, Loader2 } from "lucide-react";

interface UploadFileCardProps {
  fileName: string;
  fileType: string;
  status: "parsing" | "complete" | "error";
  confidence?: number;
  detectedType?: string;
  extractedFields?: number;
  className?: string;
}

const typeIcons: Record<string, typeof File> = {
  csv: FileSpreadsheet,
  pdf: FileText,
  txt: FileText,
};

export function UploadFileCard({
  fileName, fileType, status, confidence, detectedType, extractedFields, className,
}: UploadFileCardProps) {
  const Icon = typeIcons[fileType] || File;

  return (
    <Card className={cn("", className)}>
      <CardContent className="p-3 flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary">
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{fileName}</p>
          <div className="flex items-center gap-2 mt-0.5">
            {detectedType && <Badge variant="secondary" className="text-[10px]">{detectedType}</Badge>}
            {extractedFields && <span className="text-[10px] text-muted-foreground">{extractedFields} fields</span>}
            {confidence && <span className="text-[10px] font-mono text-primary">{Math.round(confidence * 100)}%</span>}
          </div>
        </div>
        <div>
          {status === "parsing" && <Loader2 className="h-4 w-4 text-primary animate-spin" />}
          {status === "complete" && <Check className="h-4 w-4 text-success" />}
          {status === "error" && <span className="text-xs text-destructive">Error</span>}
        </div>
      </CardContent>
    </Card>
  );
}
