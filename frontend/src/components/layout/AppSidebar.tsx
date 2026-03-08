import {
  Beaker,
  BarChart3,
  BookOpen,
  FileText,
  Import,
  Rocket,
  Settings,
  Dna,
  Loader2,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { useIngestion } from "@/contexts/IngestionContext";

const mainNav = [
  { title: "Program Dashboard", url: "/dashboard", icon: BarChart3 },
];

const workflowNav = [
  { title: "Ingestion",           url: "/ingestion",   icon: Import,  requiresData: false },
  { title: "Experiment Design",   url: "/experiments", icon: Beaker,  requiresData: true  },
  { title: "Execution Planning",  url: "/execution",   icon: Rocket,  requiresData: true  },
];

const insightNav = [
  { title: "Literature & Evidence", url: "/literature", icon: BookOpen },
  { title: "Reports",               url: "/reports",    icon: FileText },
];

const systemNav = [
  { title: "Settings", url: "/dashboard", icon: Settings },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const location = useLocation();
  const { isPipelineRunning, experimentDesignResponse } = useIngestion();

  // Downstream pages are only unlocked once data is available
  const dataReady = !!experimentDesignResponse && !isPipelineRunning;

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="p-4">
        <NavLink to="/dashboard" className="flex items-center gap-2.5 px-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Dna className="h-4 w-4 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight text-foreground">SchemaBio</span>
              <span className="text-[10px] text-muted-foreground">Drug Discovery OS</span>
            </div>
          )}
        </NavLink>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNav.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end
                      className="hover:bg-sidebar-accent/80"
                      activeClassName="bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    >
                      <item.icon className="mr-2 h-4 w-4" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Workflow</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {workflowNav.map((item) => {
                const locked = item.requiresData && !dataReady;
                const running = item.requiresData && isPipelineRunning;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild disabled={locked}>
                      {locked ? (
                        <div className="flex items-center gap-2 px-2 py-1.5 rounded-md text-muted-foreground/50 cursor-not-allowed select-none">
                          {running
                            ? <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            : <item.icon className="mr-2 h-4 w-4" />
                          }
                          {!collapsed && <span>{item.title}</span>}
                        </div>
                      ) : (
                        <NavLink
                          to={item.url}
                          end
                          className="hover:bg-sidebar-accent/80"
                          activeClassName="bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                        >
                          <item.icon className="mr-2 h-4 w-4" />
                          {!collapsed && <span>{item.title}</span>}
                        </NavLink>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Insights</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {insightNav.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end
                      className="hover:bg-sidebar-accent/80"
                      activeClassName="bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    >
                      <item.icon className="mr-2 h-4 w-4" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>System</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {systemNav.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end
                      className="hover:bg-sidebar-accent/80"
                      activeClassName="bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    >
                      <item.icon className="mr-2 h-4 w-4" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3">
        {!collapsed && (
          <div className="rounded-lg bg-secondary/50 p-3">
            <p className="text-xs font-medium text-foreground">Demo Program</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">FQ Resistance Reversal</p>
            <div className="mt-2 h-1.5 rounded-full bg-secondary">
              <div className="h-full w-[65%] rounded-full bg-primary" />
            </div>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
