import { useEffect, useState } from "react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  BarChart3, Beaker, BookOpen, FileText, Import, Rocket, Search,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

export function CommandMenu() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const go = (path: string) => {
    navigate(path);
    setOpen(false);
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search commands, programs, or data..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => go("/dashboard")}>
            <BarChart3 className="mr-2 h-4 w-4" /> Dashboard
          </CommandItem>
          <CommandItem onSelect={() => go("/ingestion")}>
            <Import className="mr-2 h-4 w-4" /> Ingestion
          </CommandItem>
          <CommandItem onSelect={() => go("/experiments")}>
            <Beaker className="mr-2 h-4 w-4" /> Experiments
          </CommandItem>
          <CommandItem onSelect={() => go("/execution")}>
            <Rocket className="mr-2 h-4 w-4" /> Execution
          </CommandItem>
          <CommandItem onSelect={() => go("/literature")}>
            <BookOpen className="mr-2 h-4 w-4" /> Literature
          </CommandItem>
          <CommandItem onSelect={() => go("/reports")}>
            <FileText className="mr-2 h-4 w-4" /> Reports
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Actions">
          <CommandItem>Load Demo Program</CommandItem>
          <CommandItem>Upload Files</CommandItem>
          <CommandItem>Generate Report</CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
