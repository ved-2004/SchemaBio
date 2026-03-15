import { Bell, Moon, Search, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { useTheme } from "next-themes";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { useLocation } from "react-router-dom";
import { UserMenu } from "@/components/layout/UserMenu";

const routeNames: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/ingestion": "Ingestion",
  "/experiments": "Experiments",
  "/execution": "Execution",
  "/literature": "Literature",
  "/reports": "Reports",
  "/settings": "Settings",
};

export function TopNav() {
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const currentRoute = routeNames[location.pathname] || "Dashboard";

  return (
    <header className="flex h-14 items-center gap-3 border-b border-border bg-card/50 px-4">
      <SidebarTrigger className="h-8 w-8" />
      <Separator orientation="vertical" className="h-5" />

      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/" className="text-xs text-muted-foreground">
              SchemaBio
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage className="text-xs font-medium">{currentRoute}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex-1" />

      <Button
        variant="outline"
        size="sm"
        className="hidden md:flex items-center gap-2 text-xs text-muted-foreground h-8 px-3 w-56 justify-start"
        onClick={() => document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
      >
        <Search className="h-3.5 w-3.5" />
        <span>Search or command...</span>
        <kbd className="ml-auto text-[10px] bg-secondary px-1.5 py-0.5 rounded font-mono">⌘K</kbd>
      </Button>

      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      >
        <Sun className="h-4 w-4 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
        <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
      </Button>

      <Button variant="ghost" size="icon" className="h-8 w-8 relative">
        <Bell className="h-4 w-4" />
        <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-primary" />
      </Button>

      <UserMenu />
    </header>
  );
}
