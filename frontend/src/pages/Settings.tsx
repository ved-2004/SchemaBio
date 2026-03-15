import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LogOut, User, Shield, Key } from "lucide-react";

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const initials = user?.name
    ? user.name.split(" ").slice(0, 2).map((p) => p[0]).join("").toUpperCase()
    : "?";

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <PageHeader title="Settings" description="Manage your account and preferences." />

      {/* Profile */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Profile</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {user && (
            <div className="flex items-center gap-4">
              <Avatar className="h-14 w-14">
                {user.avatar_url && (
                  <AvatarImage src={user.avatar_url} alt={user.name} referrerPolicy="no-referrer" />
                )}
                <AvatarFallback className="bg-primary/10 text-primary text-lg font-medium">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm font-medium">{user.name}</p>
                <p className="text-xs text-muted-foreground">{user.email}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">Signed in with Google</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data & Storage */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Key className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Data & Storage</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium">Uploaded files</p>
              <p className="text-[10px] text-muted-foreground">Files expire after 30 days</p>
            </div>
            <span className="text-xs text-muted-foreground font-mono">30-day TTL</span>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium">Max file size</p>
              <p className="text-[10px] text-muted-foreground">Per-file upload limit</p>
            </div>
            <span className="text-xs text-muted-foreground font-mono">50 MB</span>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium">Supported formats</p>
              <p className="text-[10px] text-muted-foreground">Accepted file types</p>
            </div>
            <span className="text-xs text-muted-foreground font-mono">CSV, VCF, PDF, TXT, TSV, MD</span>
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Security</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium">Sign out</p>
              <p className="text-[10px] text-muted-foreground">End your current session</p>
            </div>
            <Button variant="destructive" size="sm" className="text-xs" onClick={handleLogout}>
              <LogOut className="mr-1.5 h-3.5 w-3.5" /> Sign out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
