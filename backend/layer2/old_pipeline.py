"""
Bio Research Pipeline
=====================
Async pipeline with four concrete speed improvements over a naive single-call design:

  1. Prompt caching    — system prompts are cached server-side (Anthropic ephemeral
                         cache), cutting ~40% off TTFT on every call after the first.

  2. Tiered models     — Opus handles deep mechanistic reasoning; Haiku handles JSON
                         formatting (fallback) and context compression. Haiku is ~20x
                         faster and much cheaper for these structured tasks.

  3. Speculative parallel execution — instead of a clarification → wait → re-run loop,
                         when the model flags divergence the pipeline runs both Option A
                         and Option B assumptions concurrently via asyncio.gather and
                         picks the higher-confidence winner. Wall-clock cost = 1 Opus
                         call instead of 2 sequential ones.

  4. Context compression — prior reasoning traces (often 2-4k tokens) are summarized
                         to ~250 words by Haiku before injection into the next iteration,
                         keeping context windows lean and prefill fast.

  Plus: adaptive max_tokens (reduced on refinement iterations) and full async throughout
  so multiple pipeline instances can run concurrently without blocking.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
from typing import Any

import anthropic

from .models import (
    BioResearchContext,
    BioinformaticsAnalysis,
    ClarificationQuestion,
    EvidenceGrade,
    ExperimentDesign,
    Hypothesis,
    PipelineOutput,
    PipelineState,
    StudyPriority,
)
from .prompts import (
    CLARIFICATION_INJECTION_TEMPLATE,
    COMPRESSION_SYSTEM_PROMPT,
    FORMATTING_SYSTEM_PROMPT,
    ITERATION_CONTEXT_TEMPLATE,
    REASONING_SYSTEM_PROMPT,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REASONING_MODEL   = "claude-opus-4-6"
FORMATTING_MODEL  = "claude-haiku-4-5-20251001"   # JSON fallback + compression
COMPRESSION_MODEL = "claude-haiku-4-5-20251001"

MAX_ITERATIONS           = 6
CONFIDENCE_THRESHOLD     = 0.72
MAX_CLARIFICATION_ROUNDS = 2

log = logging.getLogger("bio_pipeline")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class BioResearchPipeline:
    """
    Autonomous biological research reasoning pipeline.

    Usage (async):
        pipeline = BioResearchPipeline()
        result   = await pipeline.run(context)

    Usage (sync wrapper):
        result = asyncio.run(pipeline.run(context))
    """

    def __init__(
        self,
        reasoning_model:          str   = REASONING_MODEL,
        formatting_model:         str   = FORMATTING_MODEL,
        compression_model:        str   = COMPRESSION_MODEL,
        confidence_threshold:     float = CONFIDENCE_THRESHOLD,
        max_iterations:           int   = MAX_ITERATIONS,
        max_clarification_rounds: int   = MAX_CLARIFICATION_ROUNDS,
        automated_mode:           bool  = True,
        speculative_execution:    bool  = True,
    ):
        """
        Parameters
        ----------
        speculative_execution : bool
            When True and the model flags diverging paths, both Option A and
            Option B are explored concurrently instead of waiting for human
            clarification. The higher-confidence branch is used as the output.
        """
        self.client                   = anthropic.AsyncAnthropic()
        self.reasoning_model          = reasoning_model
        self.formatting_model         = formatting_model
        self.compression_model        = compression_model
        self.confidence_threshold     = confidence_threshold
        self.max_iterations           = max_iterations
        self.max_clarification_rounds = max_clarification_rounds
        self.automated_mode           = automated_mode
        self.speculative_execution    = speculative_execution

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, context: BioResearchContext) -> PipelineOutput:
        """Run to convergence or until hard limits are reached."""
        state = PipelineState()

        while state.iteration < self.max_iterations and not state.converged:
            state.iteration += 1
            log.info(f"=== Iteration {state.iteration}/{self.max_iterations} ===")

            output = await self._run_single_iteration(context, state)
            state.prior_outputs.append(output)

            if self._is_converged(output):
                state.converged = True
                output.status   = "final"
                log.info(
                    f"Converged at iteration {state.iteration} "
                    f"(confidence={output.overall_confidence:.2f})"
                )
                return output

            if output.needs_clarification:
                state.clarification_rounds += 1
                new_qs = _deduplicate_questions(
                    output.clarification_questions, state.cumulative_questions
                )
                state.cumulative_questions.extend(new_qs)
                _log_questions(new_qs)

                if self.automated_mode:
                    # ── Speculative parallel execution ──────────────────────
                    if self.speculative_execution and new_qs:
                        log.info(
                            "Divergence detected — running speculative parallel paths "
                            f"({len(new_qs)} question(s))"
                        )
                        output = await self._run_speculative_paths(
                            context, state, new_qs
                        )
                        state.prior_outputs[-1] = output
                        if self._is_converged(output):
                            state.converged = True
                            output.status   = "final"
                            return output

                    # ── Clarification budget exhausted ──────────────────────
                    if state.clarification_rounds >= self.max_clarification_rounds:
                        log.warning(
                            "Max clarification rounds reached. Forcing output with "
                            "stated assumptions."
                        )
                        output.status = "forced_output"
                        output.pipeline_notes.append(
                            "FORCED OUTPUT: clarification questions unresolved. "
                            "Applied assumptions: " + "; ".join(
                                f'"{q.question}" → {q.impact_if_unresolved}'
                                for q in state.cumulative_questions
                            )
                        )
                        return output

                    # ── Auto-apply stated assumptions and continue ──────────
                    auto_answers = [
                        {
                            "question": q.question,
                            "answer":   f"[AUTO-ASSUMED] {q.impact_if_unresolved}",
                        }
                        for q in new_qs
                    ]
                    state.resolved_qa.extend(auto_answers)
                    context.resolved_questions.extend(auto_answers)
                    log.info("Applied stated assumptions. Continuing to next iteration.")

                else:
                    # Interactive mode — hand control back to caller
                    output.status = "needs_clarification"
                    return output

            elif output.overall_confidence < self.confidence_threshold:
                log.info(
                    f"Confidence {output.overall_confidence:.2f} below threshold "
                    f"{self.confidence_threshold:.2f} — refining."
                )

        final = state.prior_outputs[-1]
        final.status = "forced_output"
        final.pipeline_notes.append(
            f"Pipeline hit max iterations ({self.max_iterations}) without convergence."
        )
        return final

    async def resume_with_answers(
        self,
        context:  BioResearchContext,
        answers:  list[dict[str, str]],
        state:    PipelineState,
    ) -> PipelineOutput:
        """
        Resume an interactive-mode pipeline after a human supplies answers.

        answers: [{"question": "...", "answer": "..."}, ...]
        """
        state.resolved_qa.extend(answers)
        context.resolved_questions.extend(answers)
        return await self.run(context)

    # ------------------------------------------------------------------
    # Core iteration
    # ------------------------------------------------------------------

    async def _run_single_iteration(
        self, context: BioResearchContext, state: PipelineState
    ) -> PipelineOutput:
        """
        One full pass:
          1. Build user message
          2. Opus reasoning call (cached system prompt, adaptive tokens)
          3. Extract JSON from Opus output; fall back to Haiku if malformed
        """
        user_message = await self._build_user_message(context, state)

        # Adaptive max_tokens: first iteration gets full budget; refinements less
        reasoning_tokens = 4096 if state.iteration == 1 else 2560

        raw = await self._call_reasoning_llm(user_message, reasoning_tokens)
        return self._parse_output(raw, state.iteration, fallback_raw=raw)

    # ------------------------------------------------------------------
    # Speculative parallel execution
    # ------------------------------------------------------------------

    async def _run_speculative_paths(
        self,
        context:   BioResearchContext,
        state:     PipelineState,
        questions: list[ClarificationQuestion],
    ) -> PipelineOutput:
        """
        Build two context variants (option_a vs option_b for each question)
        and run them concurrently. Return the higher-confidence output.
        """
        path_a_answers = [
            {
                "question": q.question,
                "answer":   f"[SPECULATIVE PATH A] {q.option_a}",
            }
            for q in questions
        ]
        path_b_answers = [
            {
                "question": q.question,
                "answer":   f"[SPECULATIVE PATH B] {q.option_b}",
            }
            for q in questions
        ]

        ctx_a = copy.deepcopy(context)
        ctx_b = copy.deepcopy(context)
        ctx_a.resolved_questions.extend(path_a_answers)
        ctx_b.resolved_questions.extend(path_b_answers)

        # Shared state snapshot — each speculative call reads it but doesn't mutate
        state_snap = copy.deepcopy(state)

        output_a, output_b = await asyncio.gather(
            self._run_single_iteration(ctx_a, state_snap),
            self._run_single_iteration(ctx_b, state_snap),
        )

        log.info(
            f"Speculative paths resolved — "
            f"A: {output_a.overall_confidence:.2f}, "
            f"B: {output_b.overall_confidence:.2f}"
        )

        winner    = output_a if output_a.overall_confidence >= output_b.overall_confidence else output_b
        path_name = "A" if winner is output_a else "B"
        winner.pipeline_notes.append(
            f"Selected from speculative parallel execution. "
            f"Path A confidence: {output_a.overall_confidence:.2f}, "
            f"Path B confidence: {output_b.overall_confidence:.2f}. "
            f"Path {path_name} chosen."
        )
        return winner

    # ------------------------------------------------------------------
    # LLM calls
    # ------------------------------------------------------------------

    async def _call_reasoning_llm(
        self, user_message: str, max_tokens: int
    ) -> str:
        """
        Opus call with prompt caching on the system prompt.
        Returns raw model text (prose + JSON block).
        """
        log.info(f"Reasoning call — model={self.reasoning_model}, max_tokens={max_tokens}")
        response = await self.client.messages.create(
            model=self.reasoning_model,
            max_tokens=max_tokens,
            system=[
                {
                    "type":          "text",
                    "text":          REASONING_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # ← prompt caching
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    async def _call_formatting_llm(self, raw_opus_output: str) -> str:
        """
        Haiku fallback: takes the full Opus output and returns valid JSON.
        Called only when the primary JSON extraction from Opus output fails.
        """
        log.info(f"Formatting fallback call — model={self.formatting_model}")
        response = await self.client.messages.create(
            model=self.formatting_model,
            max_tokens=4096,
            system=[
                {
                    "type":          "text",
                    "text":          FORMATTING_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role":    "user",
                    "content": (
                        "Convert the following scientific reasoning output into the "
                        "required JSON schema. Output only valid JSON, no prose.\n\n"
                        + raw_opus_output
                    ),
                }
            ],
        )
        return response.content[0].text

    async def _compress_reasoning(self, reasoning_trace: str) -> str:
        """
        Haiku compression: reduces a verbose reasoning trace to ≤250-word bullets.
        Only called when the trace exceeds 800 characters.
        """
        if len(reasoning_trace) < 800:
            return reasoning_trace

        log.info("Compressing prior reasoning trace...")
        response = await self.client.messages.create(
            model=self.compression_model,
            max_tokens=512,
            system=[
                {
                    "type":          "text",
                    "text":          COMPRESSION_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role":    "user",
                    "content": (
                        "Compress the following scientific reasoning trace into a "
                        "concise bullet-point summary (≤250 words). Preserve key "
                        "mechanistic conclusions, confidence scores, and unresolved "
                        "questions. Do not add information.\n\n" + reasoning_trace
                    ),
                }
            ],
        )
        return response.content[0].text

    # ------------------------------------------------------------------
    # Context assembly
    # ------------------------------------------------------------------

    async def _build_user_message(
        self, context: BioResearchContext, state: PipelineState
    ) -> str:
        parts: list[str] = []

        # Iteration header + compressed prior reasoning (iterations 2+)
        if state.iteration > 1 and state.prior_outputs:
            prior = state.prior_outputs[-1]

            # Compress prior reasoning to keep context lean
            compressed = await self._compress_reasoning(prior.reasoning_trace)

            open_issues = list(prior.divergence_flags) + [
                q.question
                for q in state.cumulative_questions
                if q.question not in {r["question"] for r in state.resolved_qa}
            ]
            resolved_strs = [
                f"Q: {r['question']}\nA: {r['answer']}"
                for r in state.resolved_qa
            ]
            parts.append(
                ITERATION_CONTEXT_TEMPLATE.format(
                    iteration=state.iteration,
                    max_iterations=self.max_iterations,
                    prior_reasoning_summary=compressed,
                    resolved="\n".join(resolved_strs) or "None",
                    open_issues="\n".join(open_issues) or "None",
                )
            )

        # Inject answered clarification questions
        if context.resolved_questions:
            qa_pairs = "\n\n".join(
                f"Q: {r['question']}\nA: {r['answer']}"
                for r in context.resolved_questions
            )
            parts.append(
                CLARIFICATION_INJECTION_TEMPLATE.format(qa_pairs=qa_pairs)
            )

        # Primary biological data
        parts.append("=== USER-PROVIDED BIOLOGICAL CONTEXT ===\n")
        parts.append(_format_section("Research Papers",         context.research_papers))
        parts.append(_format_section("Assay Data",              context.assay_data))
        parts.append(_format_section("Genomics & Variant Data", context.genomics_data))
        parts.append(_format_section("Compound Screen Results", context.compound_screen_results))
        parts.append(_format_section("Bioinformatics Data",     context.bioinformatics_data))

        parts.append("\n=== RAG-FETCHED LITERATURE ===\n")
        parts.append(_format_section("Retrieved Documents",     context.rag_documents))

        parts.append(
            "\n\nReason carefully through all six stages. "
            "Then output your JSON conclusions."
        )
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_output(
        self,
        raw: str,
        iteration: int,
        fallback_raw: str = "",
    ) -> PipelineOutput:
        """
        1. Try to extract ```json ... ``` block from Opus output.
        2. If that fails, schedule a synchronous Haiku fallback call.
           (We run it in a new event loop since _parse_output is sync.)
        3. If both fail, return an error output flagging the parse failure.
        """
        json_str = _extract_json_block(raw)

        if not json_str:
            # Haiku fallback (blocking — only triggered on parse failure)
            log.warning("No JSON block found in Opus output. Trying Haiku fallback.")
            try:
                json_str = asyncio.get_event_loop().run_until_complete(
                    self._call_formatting_llm(fallback_raw or raw)
                )
            except Exception as exc:
                log.error(f"Haiku fallback also failed: {exc}")
                return _error_output(iteration, f"Haiku fallback error: {exc}", raw)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            log.error(f"JSON parse error: {exc}")
            return _error_output(iteration, str(exc), raw)

        return _build_pipeline_output(data, iteration)

    # ------------------------------------------------------------------
    # Convergence
    # ------------------------------------------------------------------

    def _is_converged(self, output: PipelineOutput) -> bool:
        return (
            not output.needs_clarification
            and output.overall_confidence >= self.confidence_threshold
            and bool(output.experiment_designs)
            and bool(output.hypotheses)
        )


# ---------------------------------------------------------------------------
# Helpers (module-level, no state)
# ---------------------------------------------------------------------------

def _extract_json_block(text: str) -> str | None:
    """Pull the first ```json ... ``` fenced block out of model output."""
    match = re.search(r"```json\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    # Fallback: try to find a bare { ... } spanning most of the text
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        return match.group(1).strip()
    return None


def _build_pipeline_output(data: dict[str, Any], iteration: int) -> PipelineOutput:
    """Deserialize a parsed JSON dict into a PipelineOutput."""

    def grade(val: str) -> EvidenceGrade:
        try:
            return EvidenceGrade(val)
        except ValueError:
            return EvidenceGrade.VERY_LOW

    hypotheses = [
        Hypothesis(
            statement=h.get("statement", ""),
            mechanism=h.get("mechanism", ""),
            predictions=h.get("predictions", []),
            supporting_refs=h.get("supporting_refs", []),
            evidence_grade=grade(h.get("evidence_grade", "VERY_LOW")),
            confidence=float(h.get("confidence", 0.0)),
            counter_evidence=h.get("counter_evidence", []),
        )
        for h in data.get("hypotheses", [])
    ]

    experiment_designs = [
        ExperimentDesign(
            title=e.get("title", ""),
            rationale=e.get("rationale", ""),
            hypothesis=e.get("hypothesis", ""),
            falsifiability=e.get("falsifiability", ""),
            experimental_arms=e.get("experimental_arms", []),
            positive_controls=e.get("positive_controls", []),
            negative_controls=e.get("negative_controls", []),
            constant_variables=e.get("constant_variables", []),
            confounders_addressed=e.get("confounders_addressed", []),
            primary_endpoint=e.get("primary_endpoint", ""),
            secondary_endpoints=e.get("secondary_endpoints", []),
            statistical_approach=e.get("statistical_approach", ""),
            sample_size_rationale=e.get("sample_size_rationale", ""),
            evidence_grade=grade(e.get("evidence_grade", "VERY_LOW")),
            confidence=float(e.get("confidence", 0.0)),
        )
        for e in data.get("experiment_designs", [])
    ]

    study_priorities = [
        StudyPriority(
            rank=int(s.get("rank", 99)),
            study_description=s.get("study_description", ""),
            scientific_rationale=s.get("scientific_rationale", ""),
            expected_impact=s.get("expected_impact", ""),
            dependencies=s.get("dependencies", []),
            risk_assessment=s.get("risk_assessment", ""),
            confidence=float(s.get("confidence", 0.0)),
        )
        for s in data.get("study_priorities", [])
    ]

    bioinformatics_analyses = [
        BioinformaticsAnalysis(
            analysis_type=b.get("analysis_type", ""),
            tools_suggested=b.get("tools_suggested", []),
            rationale=b.get("rationale", ""),
            input_requirements=b.get("input_requirements", []),
            expected_outputs=b.get("expected_outputs", []),
            caveats=b.get("caveats", []),
            confidence=float(b.get("confidence", 0.0)),
        )
        for b in data.get("bioinformatics_analyses", [])
    ]

    clarification_questions = [
        ClarificationQuestion(
            question=q.get("question", ""),
            why_needed=q.get("why_needed", ""),
            option_a=q.get("option_a", ""),
            option_b=q.get("option_b", ""),
            impact_if_unresolved=q.get("impact_if_unresolved", ""),
        )
        for q in data.get("clarification_questions", [])
    ]

    return PipelineOutput(
        iteration=iteration,
        status="pending",
        needs_clarification=bool(data.get("needs_clarification", False)),
        overall_confidence=float(data.get("overall_confidence", 0.0)),
        divergence_flags=data.get("divergence_flags", []),
        pipeline_notes=data.get("pipeline_notes", []),
        reasoning_trace=data.get("reasoning_trace", ""),
        hypotheses=hypotheses,
        experiment_designs=experiment_designs,
        study_priorities=study_priorities,
        bioinformatics_analyses=bioinformatics_analyses,
        clarification_questions=clarification_questions,
    )


def _error_output(iteration: int, error_msg: str, raw: str) -> PipelineOutput:
    return PipelineOutput(
        iteration=iteration,
        status="needs_clarification",
        needs_clarification=True,
        overall_confidence=0.0,
        divergence_flags=["JSON parse failure"],
        pipeline_notes=[f"Parse error: {error_msg}"],
        reasoning_trace=raw,
        hypotheses=[],
        experiment_designs=[],
        study_priorities=[],
        bioinformatics_analyses=[],
        clarification_questions=[
            ClarificationQuestion(
                question="Internal pipeline error: model output could not be parsed.",
                why_needed="Output is required to proceed.",
                option_a="Retry with simplified context",
                option_b="Inspect raw model output manually",
                impact_if_unresolved="Pipeline halted.",
            )
        ],
    )


def _deduplicate_questions(
    new: list[ClarificationQuestion],
    existing: list[ClarificationQuestion],
) -> list[ClarificationQuestion]:
    seen = {q.question for q in existing}
    return [q for q in new if q.question not in seen]


def _log_questions(questions: list[ClarificationQuestion]) -> None:
    for i, q in enumerate(questions, 1):
        log.warning(
            f"  Q{i}: {q.question}\n"
            f"      Why needed : {q.why_needed}\n"
            f"      Option A   : {q.option_a}\n"
            f"      Option B   : {q.option_b}\n"
            f"      If unresolved: {q.impact_if_unresolved}"
        )


def _format_section(title: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return f"\n[{title}: no data provided]\n"
    return f"\n--- {title} ---\n{json.dumps(items, indent=2, default=str)}\n"


# ---------------------------------------------------------------------------
# Pretty-printer (dev / debugging)
# ---------------------------------------------------------------------------

def print_pipeline_output(output: PipelineOutput) -> None:
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  PIPELINE OUTPUT  |  Iteration {output.iteration}  |  {output.status.upper()}")
    print(f"  Confidence: {output.overall_confidence:.2f}")
    print(sep)

    if output.pipeline_notes:
        print("\n[PIPELINE NOTES]")
        for n in output.pipeline_notes:
            print(f"  • {n}")

    if output.divergence_flags:
        print("\n[DIVERGENCE FLAGS]")
        for f in output.divergence_flags:
            print(f"  ⚠  {f}")

    if output.clarification_questions:
        print("\n[CLARIFICATION QUESTIONS]")
        for i, q in enumerate(output.clarification_questions, 1):
            print(f"  Q{i}: {q.question}")
            print(f"       → {q.why_needed}")

    print("\n[HYPOTHESES]")
    for h in output.hypotheses:
        print(f"  [{h.evidence_grade.value} | {h.confidence:.2f}] {h.statement}")
        print(f"    {h.mechanism}")

    print("\n[EXPERIMENT DESIGNS]")
    for e in output.experiment_designs:
        print(f"  [{e.evidence_grade.value} | {e.confidence:.2f}] {e.title}")
        print(f"    Endpoint : {e.primary_endpoint}")
        print(f"    Falsified by: {e.falsifiability}")

    print("\n[STUDY PRIORITIES]")
    for s in sorted(output.study_priorities, key=lambda x: x.rank):
        print(f"  #{s.rank} [{s.confidence:.2f}] {s.study_description}")
        print(f"    {s.expected_impact}")

    print("\n[BIOINFORMATICS]")
    for b in output.bioinformatics_analyses:
        print(f"  {b.analysis_type} [{b.confidence:.2f}] — {', '.join(b.tools_suggested)}")

    print(f"\n{sep}\n")
