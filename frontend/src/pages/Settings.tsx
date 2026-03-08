import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Settings() {
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <PageHeader
        title="Settings"
        description="Application and account settings."
      />
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Preferences</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Settings and preferences will appear here.</p>
        </CardContent>
      </Card>
    </div>
  );
}
