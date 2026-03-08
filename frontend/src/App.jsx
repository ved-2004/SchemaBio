import { useState, useCallback, useRef } from "react";

const API_BASE = "http://localhost:8000";

// ─── Color system ───────────────────────────────────────────────────────────
const C = {
  bg: "#070B0F",
  surface: "#0D1318",
  border: "#1C2733",
  borderBright: "#2A3D4F",
  green: "#00E5A0",
  greenDim: "#007A55",
  amber: "#F5A623",
  amberDim: "#7A5010",
  red: "#FF4D4D",
  blue: "#3B9EFF",
  text: "#C8D8E8",
  textDim: "#5A7080",
  textBright: "#EEF5FF",
};

// ─── Priority badges ─────────────────────────────────────────────────────────
const PRIORITY_COLORS = {
  critical: { bg: "#3D0000", border: "#FF4D4D", text: "#FF4D4D" },
  high:     { bg: "#3D2000", border: "#F5A623", text: "#F5A623" },
  medium:   { bg: "#003D2A", border: "#00E5A0", text: "#00E5A0" },
  low:      { bg: "#1A2233", border: "#3B9EFF", text: "#3B9EFF" },
};

// ─── Sample demo data ─────────────────────────────────────────────────────────
const DEMO_RESULT = {
  session_id: "demo-kpc-kpn-001",
  stage: "resistance_mechanism_characterization",
  organism: "Klebsiella pneumoniae",
  project_summary: "Program targeting Klebsiella pneumoniae with resistance genes [blaKPC-2, blaTEM-1]. Compounds identified: [meropenem, colistin, ceftazidime-avibactam]. Stage: Resistance Mechanism Characterization. Evidence strength: strong.",
  evidence_strength: "strong",
  resistance_genes: [
    { gene_name: "blaKPC-2", mechanism: "carbapenemase (class A β-lactamase)", drug_class: "Carbapenem", prevalence: "High — globally disseminated" },
    { gene_name: "blaTEM-1", mechanism: "broad-spectrum β-lactamase", drug_class: "β-lactam", prevalence: "Very High — ubiquitous" },
  ],
  compounds: [
    { name: "meropenem", cid: "441130", molecular_weight: 383.46, logp: -0.1, drug_likeness_score: 0.85, toxicity_flags: [] },
    { name: "ceftazidime-avibactam", cid: "N/A", molecular_weight: 546.58, logp: -1.4, drug_likeness_score: 0.82, toxicity_flags: [] },
    { name: "colistin", cid: "5311054", molecular_weight: 1169.0, logp: -1.6, drug_likeness_score: 0.45, toxicity_flags: ["⚠ Nephrotoxicity risk — monitor creatinine/BUN"] },
  ],
  mic_data: [
    { compound: "meropenem", organism: "Klebsiella pneumoniae", mic_value: 64, unit: "µg/mL" },
    { compound: "ceftazidime", organism: "Klebsiella pneumoniae", mic_value: 128, unit: "µg/mL" },
    { compound: "colistin", organism: "Klebsiella pneumoniae", mic_value: 1, unit: "µg/mL" },
    { compound: "ceftazidime-avibactam", organism: "Klebsiella pneumoniae", mic_value: 2, unit: "µg/mL" },
  ],
  missing_flags: [
    "No literature context provided — rationale may be weak",
    "No paper PDF uploaded",
  ],
  experiment_recommendations: [
    {
      rank: 1, priority: "critical",
      experiment_type: "Multiplex PCR — Carbapenemase Gene Detection",
      rationale: "Genotypically confirm resistance mechanism in Klebsiella pneumoniae. PCR for KPC, NDM, OXA-48, VIM, IMP provides definitive mechanism assignment required for compound selection strategy.",
      protocol: { title: "Multiplex PCR Detection of Carbapenemase Genes (KPC, NDM, OXA-48, VIM, IMP)", url: "https://www.protocols.io/view/multiplex-pcr-carbapenemase-q26g7pw3kgwz", doi: "10.17504/protocols.io.q26g7pw3kgwz" },
      missing_controls: ["Known carbapenemase-producing positive control", "Susceptible negative control", "No-template control"],
      bioinformatics_steps: ["CARD RGI (Resistance Gene Identifier)", "ResFinder v4.0", "ABRicate"],
      expected_output: "Gene identity + enzyme class assignment",
    },
    {
      rank: 2, priority: "critical",
      experiment_type: "Broth Microdilution MIC Panel — 12 Antibiotic Classes",
      rationale: "Establish full susceptibility profile for Klebsiella pneumoniae. Systematic MIC panel across drug classes identifies cross-resistance patterns and narrows viable treatment options.",
      protocol: { title: "Broth Microdilution MIC Determination for Antibiotic Susceptibility Testing", url: "https://www.protocols.io/view/broth-microdilution-mic-determination-n92ldpwjxl5b", doi: "10.17504/protocols.io.n92ldpwjxl5b" },
      missing_controls: ["ATCC QC strain", "Growth control", "Sterility control"],
      bioinformatics_steps: ["WHONET susceptibility interpretation", "AMRFinder+"],
      expected_output: "Full MIC table with EUCAST/CLSI interpretation (S/I/R)",
    },
    {
      rank: 3, priority: "high",
      experiment_type: "Whole Genome Sequencing (Illumina Short-Read)",
      rationale: "Capture full resistome and identify co-resistance genes, plasmid replicons, and integrons in Klebsiella pneumoniae. Enables AMR transmission network analysis.",
      protocol: { title: "Genomic DNA Extraction from Gram-Negative Bacteria for WGS", url: "https://www.protocols.io/view/genomic-dna-extraction-bfn3jmgn", doi: "10.17504/protocols.io.bfn3jmgn" },
      missing_controls: ["Reference strain with known genome", "Extraction blank"],
      bioinformatics_steps: ["Prokka annotation", "MLST typing", "Plasmid Finder", "SRST2"],
      expected_output: "Annotated genome with resistance gene catalog + plasmid map",
    },
  ],
  hypothesis_card: "SCIENTIFIC HYPOTHESIS\n──────────────────────────────────────────────────\nTarget organism: Klebsiella pneumoniae\nResistance determinants: blaKPC-2 (carbapenemase class A β-lactamase), blaTEM-1\nCandidate compounds: meropenem, ceftazidime-avibactam, colistin\nProgram stage: Resistance Mechanism Characterization\n\nCentral hypothesis: blaKPC-2-mediated carbapenem resistance requires covalent enzyme inhibition or compound structural features that evade β-lactamase hydrolysis. Ceftazidime-avibactam (MIC 2 µg/mL) retains activity via diazabicyclooctane inhibitor scaffold.\n\nPredicted path: Mechanism confirmation → compound optimization → in vitro validation → PK/PD modeling → in vivo proof-of-concept.\nKey decision gate: MIC ≤ EUCAST clinical breakpoint in at least 3 independent isolates before advancing.",
  funding_targets: [
    { program_name: "CARB-X Explorer Award", agency: "CARB-X (Wellcome / BARDA / Gates Foundation)", fit_score: 0.80, stage_match: true, award_size: "Up to $2M", url: "https://carb-x.org/apply/", eligibility_gaps: [] },
    { program_name: "NIH NIAID R01 — Drug-Resistant Bacteria", agency: "NIH NIAID", fit_score: 0.70, stage_match: true, award_size: "Up to $500K/year × 5 years", url: "https://grants.nih.gov", eligibility_gaps: [] },
    { program_name: "Wellcome Trust Innovator Award — AMR", agency: "Wellcome Trust", fit_score: 0.55, stage_match: true, award_size: "Up to £500K", url: "https://wellcome.org", eligibility_gaps: ["Need: global health impact statement"] },
  ],
  translational_readiness: {
    cdmo_readiness_score: 23,
    evidence_completeness_score: 27.3,
    qidp_eligible: true,
    fast_track_eligible: false,
    lpad_eligible: true,
    fda_pathway: "Pre-IND consultation with FDA CDER (Division of Anti-Infectives) recommended",
    cro_partner_type: "Clinical Microbiology CRO (BSL-2 certified)",
    scale_up_blockers: [
      "No in vivo efficacy data — required before any scale-up discussion",
      "No ADME/tox profile — PK properties unknown",
      "No defined lead compound — optimization not started",
    ],
    missing_ind_studies: [
      "In vivo efficacy (murine model)", "ADME profiling", "hERG cardiac safety assay",
      "Acute toxicity study (GLP)", "28-day repeat-dose toxicity", "Genotoxicity panel",
      "Formulation development + stability data", "GMP drug substance batch", "CMC documentation"
    ],
  },
  execution_brief: "Execution brief generated. See dashboard.",
};

// ─── Utility components ───────────────────────────────────────────────────────
function Badge({ label, color = C.green, bg = C.surface }) {
  return (
    <span style={{
      display: "inline-block", padding: "2px 10px", borderRadius: 4,
      border: `1px solid ${color}`, color, background: bg,
      fontSize: 11, fontFamily: "monospace", fontWeight: 700, letterSpacing: 1,
    }}>{label}</span>
  );
}

function EvidenceBar({ score, label }) {
  const pct = typeof score === "number" ? Math.min(score, 100) : 0;
  const color = pct > 60 ? C.green : pct > 30 ? C.amber : C.red;
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ color: C.textDim, fontSize: 11, fontFamily: "monospace" }}>{label}</span>
        <span style={{ color, fontSize: 11, fontFamily: "monospace", fontWeight: 700 }}>{pct.toFixed(0)}%</span>
      </div>
      <div style={{ height: 4, background: C.border, borderRadius: 2 }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2, transition: "width 1s ease" }} />
      </div>
    </div>
  );
}

function PulsingDot({ color = C.green }) {
  return (
    <span style={{
      display: "inline-block", width: 8, height: 8, borderRadius: "50%",
      background: color, boxShadow: `0 0 6px ${color}`, marginRight: 6,
      animation: "pulse 2s infinite"
    }} />
  );
}

function Section({ title, children, accent = C.green }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 10, marginBottom: 14,
        borderBottom: `1px solid ${C.border}`, paddingBottom: 8
      }}>
        <div style={{ width: 3, height: 16, background: accent, borderRadius: 2 }} />
        <span style={{ color: C.textBright, fontSize: 11, fontFamily: "monospace", fontWeight: 700, letterSpacing: 2 }}>
          {title}
        </span>
      </div>
      {children}
    </div>
  );
}

function Card({ children, style = {} }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 8, padding: 16, ...style
    }}>
      {children}
    </div>
  );
}

// ─── Upload zone ──────────────────────────────────────────────────────────────
function UploadZone({ label, accept, onFile, file }) {
  const ref = useRef();
  return (
    <div
      onClick={() => ref.current?.click()}
      style={{
        border: `1px dashed ${file ? C.greenDim : C.border}`,
        borderRadius: 6, padding: "12px 14px", cursor: "pointer",
        background: file ? "#001A10" : C.bg, transition: "all 0.2s",
        display: "flex", alignItems: "center", gap: 10,
      }}
    >
      <input ref={ref} type="file" accept={accept} style={{ display: "none" }}
        onChange={e => onFile(e.target.files[0])} />
      <span style={{ fontSize: 18 }}>{file ? "✓" : "+"}</span>
      <div>
        <div style={{ color: file ? C.green : C.textDim, fontSize: 12, fontFamily: "monospace" }}>
          {file ? file.name : label}
        </div>
        {!file && <div style={{ color: C.textDim, fontSize: 10 }}>{accept}</div>}
      </div>
    </div>
  );
}

// ─── Layer panels ─────────────────────────────────────────────────────────────
function Layer1Panel({ data }) {
  if (!data) return null;
  const stageLabel = data.stage?.replace(/_/g, " ").toUpperCase() || "UNKNOWN";
  const evidColor = data.evidence_strength === "strong" ? C.green : data.evidence_strength === "moderate" ? C.amber : C.red;

  return (
    <div>
      <Section title="PROGRAM STATE" accent={C.blue}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
          <Card>
            <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 4 }}>WORKFLOW STAGE</div>
            <div style={{ color: C.amber, fontSize: 12, fontFamily: "monospace", fontWeight: 700 }}>{stageLabel}</div>
          </Card>
          <Card>
            <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 4 }}>TARGET ORGANISM</div>
            <div style={{ color: C.text, fontSize: 11, fontFamily: "monospace", fontStyle: "italic" }}>
              {data.organism || "Not identified"}
            </div>
          </Card>
        </div>
        <Card style={{ marginBottom: 10 }}>
          <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 6 }}>EVIDENCE STRENGTH</div>
          <Badge label={data.evidence_strength?.toUpperCase()} color={evidColor} />
        </Card>
        <Card>
          <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 6 }}>PROJECT SUMMARY</div>
          <div style={{ color: C.text, fontSize: 11, lineHeight: 1.6 }}>{data.project_summary}</div>
        </Card>
      </Section>

      <Section title="RESISTANCE GENES" accent={C.red}>
        {data.resistance_genes?.length ? data.resistance_genes.map((g, i) => (
          <Card key={i} style={{ marginBottom: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
              <span style={{ color: C.amber, fontFamily: "monospace", fontWeight: 700, fontSize: 13 }}>{g.gene_name}</span>
              {g.drug_class && <Badge label={g.drug_class} color={C.amber} bg="#1A1000" />}
            </div>
            {g.mechanism && <div style={{ color: C.text, fontSize: 11, marginBottom: 4 }}>{g.mechanism}</div>}
            {g.prevalence && <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace" }}>↗ {g.prevalence}</div>}
          </Card>
        )) : <div style={{ color: C.textDim, fontSize: 12 }}>No resistance genes identified</div>}
      </Section>

      <Section title="MIC DATA" accent={C.green}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, fontFamily: "monospace" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                {["COMPOUND", "ORGANISM", "MIC", "UNIT"].map(h => (
                  <th key={h} style={{ color: C.textDim, textAlign: "left", padding: "4px 8px", fontSize: 10 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.mic_data?.map((m, i) => {
                const isHigh = m.mic_value >= 32;
                const isLow = m.mic_value <= 2;
                return (
                  <tr key={i} style={{ borderBottom: `1px solid ${C.border}30` }}>
                    <td style={{ color: C.text, padding: "5px 8px" }}>{m.compound}</td>
                    <td style={{ color: C.textDim, padding: "5px 8px", fontStyle: "italic" }}>{m.organism?.replace("Klebsiella pneumoniae", "K. pneumoniae")}</td>
                    <td style={{ color: isHigh ? C.red : isLow ? C.green : C.amber, padding: "5px 8px", fontWeight: 700 }}>
                      {isHigh ? ">" : isLow ? "✓" : ""}{m.mic_value}
                    </td>
                    <td style={{ color: C.textDim, padding: "5px 8px" }}>{m.unit}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Section>

      {data.missing_flags?.length > 0 && (
        <Section title="DATA GAPS" accent={C.amber}>
          {data.missing_flags.map((f, i) => (
            <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start", marginBottom: 6 }}>
              <span style={{ color: C.amber, marginTop: 1 }}>⚑</span>
              <span style={{ color: C.textDim, fontSize: 11 }}>{f}</span>
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}

function Layer2Panel({ data }) {
  if (!data) return null;
  const [expanded, setExpanded] = useState(null);

  return (
    <div>
      <Section title="EXPERIMENT RECOMMENDATIONS" accent={C.green}>
        {data.experiment_recommendations?.map((rec, i) => {
          const pc = PRIORITY_COLORS[rec.priority] || PRIORITY_COLORS.medium;
          const isOpen = expanded === i;
          return (
            <Card key={i} style={{ marginBottom: 10, borderColor: isOpen ? pc.border : C.border, cursor: "pointer" }}
              onClick={() => setExpanded(isOpen ? null : i)}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{
                    width: 22, height: 22, borderRadius: "50%",
                    background: pc.bg, border: `1px solid ${pc.border}`,
                    color: pc.text, fontSize: 11, fontWeight: 700, fontFamily: "monospace",
                    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0
                  }}>{rec.rank}</span>
                  <div>
                    <div style={{ color: C.textBright, fontSize: 12, fontWeight: 600, marginBottom: 2 }}>
                      {rec.experiment_type}
                    </div>
                    <Badge label={rec.priority?.toUpperCase()} color={pc.text} bg={pc.bg} />
                  </div>
                </div>
                <span style={{ color: C.textDim, fontSize: 16 }}>{isOpen ? "▲" : "▼"}</span>
              </div>

              {isOpen && (
                <div style={{ marginTop: 14, borderTop: `1px solid ${C.border}`, paddingTop: 14 }}>
                  <div style={{ color: C.text, fontSize: 11, lineHeight: 1.7, marginBottom: 12 }}>
                    {rec.rationale}
                  </div>

                  {rec.protocol && (
                    <div style={{ marginBottom: 12, padding: 10, background: "#001A0D", borderRadius: 6, border: `1px solid ${C.greenDim}` }}>
                      <div style={{ color: C.green, fontSize: 10, fontFamily: "monospace", marginBottom: 4 }}>
                        📋 PROTOCOLS.IO — VERIFIED PROTOCOL
                      </div>
                      <div style={{ color: C.text, fontSize: 11, marginBottom: 4 }}>{rec.protocol.title}</div>
                      {rec.protocol.doi && (
                        <div style={{ color: C.greenDim, fontSize: 10, fontFamily: "monospace" }}>DOI: {rec.protocol.doi}</div>
                      )}
                      {rec.protocol.url && (
                        <a href={rec.protocol.url} target="_blank" rel="noopener noreferrer"
                          style={{ color: C.green, fontSize: 10, fontFamily: "monospace" }}
                          onClick={e => e.stopPropagation()}>
                          → Open protocol ↗
                        </a>
                      )}
                    </div>
                  )}

                  {rec.missing_controls?.length > 0 && (
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 4 }}>REQUIRED CONTROLS</div>
                      {rec.missing_controls.map((c, j) => (
                        <div key={j} style={{ color: C.text, fontSize: 11, paddingLeft: 10, marginBottom: 2 }}>• {c}</div>
                      ))}
                    </div>
                  )}

                  {rec.bioinformatics_steps?.length > 0 && (
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 4 }}>BIOINFORMATICS PIPELINE</div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                        {rec.bioinformatics_steps.map((s, j) => (
                          <Badge key={j} label={s} color={C.blue} bg="#001020" />
                        ))}
                      </div>
                    </div>
                  )}

                  {rec.expected_output && (
                    <div>
                      <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 4 }}>EXPECTED OUTPUT</div>
                      <div style={{ color: C.amber, fontSize: 11, fontFamily: "monospace" }}>→ {rec.expected_output}</div>
                    </div>
                  )}
                </div>
              )}
            </Card>
          );
        })}
      </Section>

      <Section title="SCIENTIFIC HYPOTHESIS" accent={C.amber}>
        <Card>
          <pre style={{
            color: C.text, fontSize: 10.5, fontFamily: "monospace",
            whiteSpace: "pre-wrap", lineHeight: 1.8, margin: 0
          }}>{data.hypothesis_card}</pre>
        </Card>
      </Section>

      {data.compounds?.length > 0 && (
        <Section title="COMPOUND ANALYSIS" accent={C.blue}>
          {data.compounds.map((c, i) => (
            <Card key={i} style={{ marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <span style={{ color: C.textBright, fontFamily: "monospace", fontWeight: 700, fontSize: 13 }}>{c.name}</span>
                {c.cid && <span style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace" }}>CID: {c.cid}</span>}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginBottom: 8 }}>
                {c.molecular_weight && (
                  <div style={{ textAlign: "center", padding: "6px", background: C.bg, borderRadius: 4 }}>
                    <div style={{ color: C.textDim, fontSize: 9, fontFamily: "monospace" }}>MW</div>
                    <div style={{ color: C.text, fontSize: 12, fontFamily: "monospace", fontWeight: 700 }}>{c.molecular_weight}</div>
                  </div>
                )}
                {c.logp !== null && c.logp !== undefined && (
                  <div style={{ textAlign: "center", padding: "6px", background: C.bg, borderRadius: 4 }}>
                    <div style={{ color: C.textDim, fontSize: 9, fontFamily: "monospace" }}>logP</div>
                    <div style={{ color: C.text, fontSize: 12, fontFamily: "monospace", fontWeight: 700 }}>{c.logp}</div>
                  </div>
                )}
                {c.drug_likeness_score !== null && c.drug_likeness_score !== undefined && (
                  <div style={{ textAlign: "center", padding: "6px", background: C.bg, borderRadius: 4 }}>
                    <div style={{ color: C.textDim, fontSize: 9, fontFamily: "monospace" }}>DL SCORE</div>
                    <div style={{ color: c.drug_likeness_score > 0.7 ? C.green : c.drug_likeness_score > 0.4 ? C.amber : C.red, fontSize: 12, fontFamily: "monospace", fontWeight: 700 }}>
                      {(c.drug_likeness_score * 100).toFixed(0)}%
                    </div>
                  </div>
                )}
              </div>
              {c.toxicity_flags?.length > 0 && (
                <div style={{ fontSize: 10, color: C.amber }}>{c.toxicity_flags[0]}</div>
              )}
            </Card>
          ))}
        </Section>
      )}
    </div>
  );
}

function Layer3Panel({ data }) {
  if (!data?.translational_readiness) return null;
  const tr = data.translational_readiness;
  const cdmo = tr.cdmo_readiness_score || 0;
  const evid = tr.evidence_completeness_score || 0;

  return (
    <div>
      <Section title="TRANSLATIONAL READINESS" accent={C.amber}>
        <Card style={{ marginBottom: 12 }}>
          <div style={{ display: "grid", gap: 14 }}>
            <EvidenceBar score={cdmo} label="CDMO / GMP READINESS" />
            <EvidenceBar score={evid} label="IND EVIDENCE COMPLETENESS" />
          </div>
          <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap" }}>
            {tr.qidp_eligible && <Badge label="QIDP ELIGIBLE" color={C.green} />}
            {tr.fast_track_eligible && <Badge label="FAST TRACK" color={C.green} />}
            {tr.lpad_eligible && <Badge label="LPAD ELIGIBLE" color={C.amber} />}
          </div>
        </Card>

        <Card style={{ marginBottom: 12 }}>
          <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 6 }}>FDA PATHWAY</div>
          <div style={{ color: C.text, fontSize: 11, lineHeight: 1.6 }}>{tr.fda_pathway}</div>
        </Card>

        {tr.cro_partner_type && (
          <Card style={{ marginBottom: 12 }}>
            <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", marginBottom: 6 }}>RECOMMENDED CRO TYPE</div>
            <div style={{ color: C.blue, fontSize: 11 }}>{tr.cro_partner_type}</div>
          </Card>
        )}
      </Section>

      <Section title="FUNDING STRATEGY" accent={C.green}>
        {data.funding_targets?.map((f, i) => (
          <Card key={i} style={{ marginBottom: 8, borderColor: i === 0 ? C.greenDim : C.border }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
              <div>
                <div style={{ color: i === 0 ? C.green : C.textBright, fontSize: 12, fontWeight: 600, marginBottom: 2 }}>
                  {i === 0 && "★ "}{f.program_name}
                </div>
                <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace" }}>{f.agency}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ color: C.green, fontSize: 13, fontFamily: "monospace", fontWeight: 700 }}>
                  {(f.fit_score * 100).toFixed(0)}%
                </div>
                <div style={{ color: C.textDim, fontSize: 9 }}>FIT</div>
              </div>
            </div>
            {f.award_size && (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Badge label={f.award_size} color={C.amber} bg="#1A1000" />
                {f.stage_match && <Badge label="STAGE MATCH" color={C.green} bg="#001A10" />}
              </div>
            )}
            {f.eligibility_gaps?.length > 0 && (
              <div style={{ marginTop: 8, fontSize: 10, color: C.textDim }}>
                {f.eligibility_gaps[0]}
              </div>
            )}
          </Card>
        ))}
      </Section>

      <Section title="SCALE-UP BLOCKERS" accent={C.red}>
        <Card>
          {tr.scale_up_blockers?.slice(0, 4).map((b, i) => (
            <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start", marginBottom: 8 }}>
              <span style={{ color: C.red, fontSize: 14, marginTop: -1 }}>✕</span>
              <span style={{ color: C.text, fontSize: 11, lineHeight: 1.5 }}>{b}</span>
            </div>
          ))}
        </Card>
      </Section>

      <Section title="MISSING IND STUDIES" accent={C.textDim}>
        <Card>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {tr.missing_ind_studies?.map((s, i) => (
              <Badge key={i} label={s} color={C.textDim} bg={C.bg} />
            ))}
          </div>
        </Card>
      </Section>
    </div>
  );
}

// ─── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [files, setFiles] = useState({ assay: null, variant: null, pdf: null, screen: null });
  const [freeText, setFreeText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeLayer, setActiveLayer] = useState(1);
  const [progress, setProgress] = useState("");

  const runDemo = useCallback(async () => {
    setLoading(true);
    setError(null);
    setProgress("Running demo: KPC-producing Klebsiella pneumoniae...");
    await new Promise(r => setTimeout(r, 800));
    setProgress("Layer 1: Parsing assay CSV + variant file...");
    await new Promise(r => setTimeout(r, 700));
    setProgress("Layer 2: Querying CARD, PubChem, protocols.io...");
    await new Promise(r => setTimeout(r, 900));
    setProgress("Layer 3: Computing FDA pathway + CDMO readiness...");
    await new Promise(r => setTimeout(r, 600));
    setResult(DEMO_RESULT);
    setActiveLayer(1);
    setLoading(false);
    setProgress("");
  }, []);

  const runAnalysis = useCallback(async () => {
    if (!files.assay && !files.variant && !files.pdf && !freeText.trim()) {
      setError("Please upload at least one file or enter text.");
      return;
    }
    setLoading(true);
    setError(null);
    setProgress("Layer 1: Ingesting + parsing inputs...");

    try {
      const form = new FormData();
      if (files.assay) form.append("assay_csv", files.assay);
      if (files.variant) form.append("variant_file", files.variant);
      if (files.pdf) form.append("paper_pdf", files.pdf);
      if (files.screen) form.append("compound_screen", files.screen);
      if (freeText) form.append("free_text", freeText);

      setProgress("Layer 2: Running experiment design engine...");
      const res = await fetch(`${API_BASE}/analyze`, { method: "POST", body: form });
      const data = await res.json();

      setProgress("Layer 3: Computing drug-to-market readiness...");
      await new Promise(r => setTimeout(r, 400));

      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      setResult(data);
      setActiveLayer(1);
    } catch (e) {
      setError(e.message + " (Is backend running at localhost:8000?)");
    } finally {
      setLoading(false);
      setProgress("");
    }
  }, [files, freeText]);

  const LAYERS = [
    { id: 1, label: "01 / INGESTION", desc: "State Builder" },
    { id: 2, label: "02 / EXPERIMENT", desc: "Design Engine" },
    { id: 3, label: "03 / TRANSLATION", desc: "Market Readiness" },
  ];

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: "system-ui, -apple-system, sans-serif", color: C.text }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; } 
        ::-webkit-scrollbar-track { background: ${C.bg}; }
        ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 2px; }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes fadein { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
      `}</style>

      {/* ── Header ── */}
      <div style={{
        background: C.surface, borderBottom: `1px solid ${C.border}`,
        padding: "0 24px", display: "flex", alignItems: "center",
        justifyContent: "space-between", height: 52
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            fontFamily: "'Space Mono', monospace", fontWeight: 700, fontSize: 16,
            color: C.green, letterSpacing: 2
          }}>AIDEN·AMP</div>
          <div style={{ width: 1, height: 20, background: C.border }} />
          <div style={{ color: C.textDim, fontSize: 11, fontFamily: "monospace" }}>
            AI PI for Antibiotic Resistance Drug Discovery
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <PulsingDot color={C.green} />
          <span style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace" }}>SYSTEM ONLINE</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", height: "calc(100vh - 52px)" }}>

        {/* ── Left sidebar: input ── */}
        <div style={{
          background: C.surface, borderRight: `1px solid ${C.border}`,
          overflowY: "auto", padding: 20
        }}>
          <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", letterSpacing: 2, marginBottom: 16 }}>
            INPUT DATA
          </div>

          <div style={{ display: "grid", gap: 8, marginBottom: 20 }}>
            <UploadZone label="Resistance Assay CSV" accept=".csv" file={files.assay}
              onFile={f => setFiles(p => ({...p, assay: f}))} />
            <UploadZone label="Variant / Genomics File" accept=".vcf,.tsv,.txt,.csv" file={files.variant}
              onFile={f => setFiles(p => ({...p, variant: f}))} />
            <UploadZone label="Paper PDF" accept=".pdf" file={files.pdf}
              onFile={f => setFiles(p => ({...p, pdf: f}))} />
            <UploadZone label="Compound Screen CSV" accept=".csv" file={files.screen}
              onFile={f => setFiles(p => ({...p, screen: f}))} />
          </div>

          <textarea
            placeholder="Free text: target rationale, organism notes, project context..."
            value={freeText}
            onChange={e => setFreeText(e.target.value)}
            style={{
              width: "100%", height: 100, background: C.bg, border: `1px solid ${C.border}`,
              borderRadius: 6, color: C.text, fontSize: 11, padding: 10, resize: "vertical",
              outline: "none", fontFamily: "monospace", marginBottom: 16
            }}
          />

          <button onClick={runAnalysis} disabled={loading} style={{
            width: "100%", padding: "11px", background: loading ? C.greenDim : C.green,
            color: C.bg, border: "none", borderRadius: 6, fontSize: 12, fontFamily: "monospace",
            fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", letterSpacing: 1, marginBottom: 8
          }}>
            {loading ? "ANALYZING..." : "▶  RUN ANALYSIS"}
          </button>

          <button onClick={runDemo} disabled={loading} style={{
            width: "100%", padding: "10px", background: "transparent",
            color: C.amber, border: `1px solid ${C.amberDim}`, borderRadius: 6,
            fontSize: 11, fontFamily: "monospace", cursor: loading ? "not-allowed" : "pointer",
            letterSpacing: 1
          }}>
            ⚡  DEMO: KPC Klebsiella
          </button>

          {error && (
            <div style={{ marginTop: 12, padding: 10, background: "#1A0000", border: `1px solid ${C.red}`, borderRadius: 6, color: C.red, fontSize: 10, fontFamily: "monospace", lineHeight: 1.5 }}>
              {error}
            </div>
          )}

          {loading && progress && (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ width: 12, height: 12, border: `2px solid ${C.green}`, borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                <span style={{ color: C.green, fontSize: 10, fontFamily: "monospace" }}>{progress}</span>
              </div>
            </div>
          )}

          {/* Workflow diagram */}
          <div style={{ marginTop: 24, borderTop: `1px solid ${C.border}`, paddingTop: 16 }}>
            <div style={{ color: C.textDim, fontSize: 10, fontFamily: "monospace", letterSpacing: 2, marginBottom: 12 }}>
              PIPELINE
            </div>
            {[
              { label: "INGEST", desc: "CSV · VCF · PDF · Text", color: C.blue },
              { label: "PARSE", desc: "Entities + stage detection", color: C.blue },
              { label: "QUERY", desc: "CARD · PubChem · protocols.io", color: C.green },
              { label: "DESIGN", desc: "Ranked experiments + protocols", color: C.green },
              { label: "ROUTE", desc: "Grants + CRO + CDMO", color: C.amber },
              { label: "COMPLY", desc: "FDA pathway + IND checklist", color: C.amber },
            ].map((step, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <div style={{ width: 2, height: 16, background: step.color, flexShrink: 0 }} />
                <span style={{ color: step.color, fontSize: 10, fontFamily: "monospace", fontWeight: 700, width: 50, flexShrink: 0 }}>{step.label}</span>
                <span style={{ color: C.textDim, fontSize: 10 }}>{step.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Right panel: results ── */}
        <div style={{ overflowY: "auto", padding: 24 }}>
          {!result && !loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16 }}>
              <div style={{ color: C.border, fontSize: 64 }}>⌬</div>
              <div style={{ color: C.textDim, fontSize: 13, fontFamily: "monospace", textAlign: "center" }}>
                Upload data or run the demo to begin analysis
              </div>
              <div style={{ color: C.textDim, fontSize: 11, textAlign: "center", maxWidth: 400 }}>
                AIDEN-AMP maps biological evidence → experiment design → drug-to-market readiness<br />in one deterministic pipeline.
              </div>
            </div>
          )}

          {result && (
            <div style={{ animation: "fadein 0.4s ease" }}>
              {/* Layer tabs */}
              <div style={{ display: "flex", gap: 2, marginBottom: 24, background: C.surface, borderRadius: 8, padding: 4, border: `1px solid ${C.border}` }}>
                {LAYERS.map(l => (
                  <button key={l.id} onClick={() => setActiveLayer(l.id)} style={{
                    flex: 1, padding: "8px 12px", border: "none", borderRadius: 6,
                    background: activeLayer === l.id ? C.bg : "transparent",
                    color: activeLayer === l.id ? C.textBright : C.textDim,
                    cursor: "pointer", transition: "all 0.2s"
                  }}>
                    <div style={{ fontFamily: "monospace", fontSize: 11, fontWeight: 700 }}>{l.label}</div>
                    <div style={{ fontSize: 10, color: C.textDim }}>{l.desc}</div>
                  </button>
                ))}
              </div>

              {activeLayer === 1 && <Layer1Panel data={result} />}
              {activeLayer === 2 && <Layer2Panel data={result} />}
              {activeLayer === 3 && <Layer3Panel data={result} />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
