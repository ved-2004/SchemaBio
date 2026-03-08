import { PageHeader } from "@/components/layout/PageHeader";
import { LitPaperCard } from "@/components/schemabio/LitPaperCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, Network } from "lucide-react";

const papers = [
  {
    title: "Mechanisms of fluoroquinolone resistance in Burkholderia cenocepacia clinical isolates",
    authors: "Chen et al.",
    journal: "J Antimicrob Chemother",
    year: 2023,
    relevance: "Key reference for gyrA S83L resistance mechanism. Establishes mutation frequency and MIC correlations in clinical Burkholderia strains.",
    tags: ["gyrA", "resistance", "Burkholderia", "clinical"],
  },
  {
    title: "Novel gyrase inhibitors as adjuvants to fluoroquinolone therapy in resistant Gram-negatives",
    authors: "Patel, Rodriguez & Kim",
    journal: "Nature Microbiology",
    year: 2024,
    relevance: "Demonstrates proof-of-concept for allosteric gyrase modulation restoring FQ sensitivity. Directly relevant to SB-7042 mechanism hypothesis.",
    tags: ["gyrase inhibitor", "combination therapy", "adjuvant"],
  },
  {
    title: "Genomic surveillance of antimicrobial resistance in Burkholderia complex species",
    authors: "Williams et al.",
    journal: "Genome Biology",
    year: 2023,
    relevance: "Comprehensive variant catalog for resistance genes in Burkholderia. Used for variant annotation pipeline validation.",
    tags: ["genomics", "AMR", "surveillance"],
  },
  {
    title: "ADMET profiling strategies for early-stage antimicrobial compounds",
    authors: "Nakamura & Ouellet",
    journal: "Drug Discovery Today",
    year: 2022,
    relevance: "Guidelines for ADMET package design in antimicrobial programs. Relevant for SB-7042 preclinical planning.",
    tags: ["ADMET", "preclinical", "antimicrobial"],
  },
];

export default function Literature() {
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <PageHeader
        title="Literature & Evidence"
        description="Scientific publications linked to your program data. Evidence-driven reasoning for every recommendation."
      />

      {/* Search */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search papers, genes, compounds..." className="pl-9 text-sm" />
        </div>
        <Button variant="outline" size="sm" className="text-xs">Filters</Button>
      </div>

      {/* Results */}
      <div className="space-y-3">
        {papers.map((p) => (
          <LitPaperCard key={p.title} {...p} />
        ))}
      </div>

      {/* Evidence Graph Placeholder */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-medium">Evidence Relationship Graph</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex h-[260px] items-center justify-center rounded-lg bg-secondary/30 border border-dashed border-border">
            <div className="text-center">
              <Network className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Evidence graph visualization</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">Linking uploaded data → papers → recommendations</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
