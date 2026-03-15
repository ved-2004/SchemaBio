import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight, Beaker, BookOpen, ChevronRight, Dna, FlaskConical,
  Import, Layers, Lightbulb, Rocket, Shield, Target, Zap,
} from "lucide-react";
import { GoogleSignInButton } from "@/components/auth/GoogleSignInButton";
import { useAuth } from "@/contexts/AuthContext";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};

const workflowSteps = [
  { icon: Import, title: "Ingest Context", desc: "CSV, genomics, papers, compound screens — any scientific data format" },
  { icon: Layers, title: "Detect Program Stage", desc: "Hit discovery → validation → preclinical → manufacturing review" },
  { icon: Lightbulb, title: "Recommend Actions", desc: "Next experiments, controls, prioritization with literature-backed reasoning" },
  { icon: Rocket, title: "Execution Guidance", desc: "CRO matching, bioinformatics needs, funding, missing evidence" },
  { icon: Shield, title: "Translational Feasibility", desc: "CDMO readiness, manufacturability, scale-up blockers, de-risking" },
];

const architectureLayers = [
  { title: "Ingestion + Program State", desc: "Schema detection, entity extraction, workflow stage classification", icon: Import, color: "bg-info/10 text-info" },
  { title: "Experiment Design Engine", desc: "Evidence-linked recommendations, control suggestions, hypothesis ranking", icon: Beaker, color: "bg-primary/10 text-primary" },
  { title: "Drug-to-Market Execution", desc: "CRO matching, GMP readiness, manufacturability, translational planning", icon: Rocket, color: "bg-success/10 text-success" },
];

const useCases = [
  { title: "Antibiotic Resistance", desc: "Map resistance mechanisms to compound candidates with structured experimental validation", icon: FlaskConical },
  { title: "Target Prioritization", desc: "Rank biological targets by druggability, evidence quality, and translational feasibility", icon: Target },
  { title: "Preclinical Planning", desc: "Identify gaps in ADMET, reproducibility, and regulatory readiness before scale-up", icon: BookOpen },
];

export default function Landing() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-md">
        <div className="container flex h-14 items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <Dna className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-sm tracking-tight">SchemaBio</span>
          </Link>
          <div className="flex items-center gap-3">
            {user ? (
              <Button size="sm" className="text-xs" asChild>
                <Link to="/dashboard">Open Workspace <ArrowRight className="ml-1.5 h-3 w-3" /></Link>
              </Button>
            ) : (
              <GoogleSignInButton />
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="container py-20 md:py-32">
        <motion.div
          className="max-w-3xl mx-auto text-center"
          initial="hidden"
          animate="visible"
        >
          <motion.div custom={0} variants={fadeUp}>
            <Badge variant="secondary" className="mb-4 text-xs font-normal">
              Bio × AI Workflow Platform
            </Badge>
          </motion.div>
          <motion.h1 custom={1} variants={fadeUp} className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1]">
            The operating layer for{" "}
            <span className="gradient-text">scientific decision‑making</span>
          </motion.h1>
          <motion.p custom={2} variants={fadeUp} className="mt-5 text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed">
            Turn biological data into structured experiment plans and translational execution roadmaps. From resistance assays to CDMO readiness — in one platform.
          </motion.p>
          <motion.div custom={3} variants={fadeUp} className="flex items-center justify-center gap-3 mt-8">
            <Button size="lg" asChild>
              <Link to="/dashboard">Open Workspace <ArrowRight className="ml-2 h-4 w-4" /></Link>
            </Button>
          </motion.div>
        </motion.div>

        {/* Product preview */}
        <motion.div
          custom={4}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mt-16 max-w-5xl mx-auto"
        >
          <div className="rounded-2xl border border-border bg-card p-2 shadow-xl shadow-foreground/5">
            <div className="rounded-xl bg-secondary/30 border border-border overflow-hidden">
              <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-border bg-card/50">
                <div className="h-2.5 w-2.5 rounded-full bg-destructive/40" />
                <div className="h-2.5 w-2.5 rounded-full bg-warning/40" />
                <div className="h-2.5 w-2.5 rounded-full bg-success/40" />
                <span className="ml-3 text-[10px] text-muted-foreground font-mono">SchemaBio — Dashboard</span>
              </div>
              <div className="p-6 grid grid-cols-3 gap-4 scientific-grid min-h-[280px]">
                <div className="col-span-2 space-y-3">
                  <div className="rounded-lg bg-card p-4 border border-border">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="h-3 w-24 rounded bg-foreground/20" />
                      <Badge variant="secondary" className="text-[9px] h-4">Experimental Validation</Badge>
                    </div>
                    <div className="h-2 w-3/4 rounded bg-muted-foreground/10 mb-1.5" />
                    <div className="h-2 w-1/2 rounded bg-muted-foreground/10" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-card p-3 border border-border">
                      <div className="h-2 w-16 rounded bg-primary/30 mb-2" />
                      <div className="h-16 rounded bg-primary/5" />
                    </div>
                    <div className="rounded-lg bg-card p-3 border border-border">
                      <div className="h-2 w-20 rounded bg-info/30 mb-2" />
                      <div className="h-16 rounded bg-info/5" />
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="rounded-lg bg-card p-3 border border-border">
                    <div className="h-2 w-16 rounded bg-warning/30 mb-2" />
                    <div className="space-y-1.5">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-2 rounded bg-muted-foreground/10" style={{ width: `${90 - i * 15}%` }} />
                      ))}
                    </div>
                  </div>
                  <div className="rounded-lg bg-card p-3 border border-border">
                    <div className="h-2 w-14 rounded bg-success/30 mb-2" />
                    <div className="flex gap-1">
                      {[65, 45, 80, 55].map((h, i) => (
                        <div key={i} className="flex-1 rounded bg-primary/15" style={{ height: h }} />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Architecture */}
      <section className="border-t border-border bg-card/50">
        <div className="container py-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Three-layer intelligence architecture</h2>
            <p className="text-sm text-muted-foreground mt-2 max-w-lg mx-auto">
              From raw data ingestion through experimental design to translational execution.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {architectureLayers.map((layer, i) => (
              <motion.div
                key={layer.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
              >
                <Card className="h-full hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${layer.color} mb-4`}>
                      <layer.icon className="h-5 w-5" />
                    </div>
                    <h3 className="text-sm font-semibold mb-1.5">{layer.title}</h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">{layer.desc}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="border-t border-border">
        <div className="container py-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Five-step scientific workflow</h2>
            <p className="text-sm text-muted-foreground mt-2 max-w-lg mx-auto">
              Structured progression from messy scientific data to translational execution.
            </p>
          </div>
          <div className="max-w-3xl mx-auto space-y-4">
            {workflowSteps.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-4 p-4 rounded-xl border border-border bg-card hover:bg-secondary/30 transition-colors"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary font-mono text-sm font-semibold">
                  {i + 1}
                </div>
                <div>
                  <h3 className="text-sm font-semibold">{step.title}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="border-t border-border bg-card/50">
        <div className="container py-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Built for real drug discovery</h2>
            <p className="text-sm text-muted-foreground mt-2">Structured workflows for every stage of the pipeline.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {useCases.map((uc) => (
              <Card key={uc.title} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-muted-foreground mb-4">
                    <uc.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-semibold mb-1.5">{uc.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{uc.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border">
        <div className="container py-20 text-center">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Ready to accelerate your program?</h2>
          <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
            Upload your scientific data and get a structured development roadmap in minutes.
          </p>
          <div className="flex items-center justify-center gap-3 mt-6">
            <Button size="lg" asChild>
              <Link to="/dashboard">Open Workspace <ArrowRight className="ml-2 h-4 w-4" /></Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card/50">
        <div className="container py-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
              <Dna className="h-3 w-3 text-primary-foreground" />
            </div>
            <span className="text-xs font-medium">SchemaBio</span>
          </div>
          <p className="text-xs text-muted-foreground">The intelligent operating layer for drug discovery.</p>
        </div>
      </footer>
    </div>
  );
}
