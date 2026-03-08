"""
routers/execution_planning.py

Layer 3 — Execution / Translational Planning API

Endpoints:
  POST /api/execution-planning/run
    — Accept ExecutionPlanningInput, return full execution roadmap.

The input schema (ExecutionPlanningInput) is produced by the ingestion layer
and documented in docs/execution-planning-layer-handoff.md.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..models.ingestion import ExecutionPlanningInput
from ..layer3.drug_to_market import run_layer3

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/execution-planning", tags=["execution-planning"])


@router.post("/run")
async def run_execution_planning(epi: ExecutionPlanningInput) -> dict:
    """
    Run the Layer 3 Drug-to-Market execution engine.

    Accepts the ExecutionPlanningInput handoff from the ingestion layer and returns:
      - partner_recommendations    (CRO/CDMO routing)
      - funding_opportunities       (12 grant programs, scored + ranked)
      - missing_evidence_package_elements  (IND checklist gaps)
      - translational_blockers      (scale-up blockers)
      - readiness_assessment        (GMP + evidence completeness)
      - fda_pathway                 (QIDP, Fast Track, LPAD, PRV signals)
      - international_regulatory    (EMA PRIME, MHRA ILAP)
      - competitive_landscape       (approved + pipeline drugs by organism)
      - market_intelligence         (TAM, US cases, unmet need)
      - ip_landscape                (FTO signals by resistance gene family)
      - stage_timeline              (months to IND / Phase 1, cost estimate)
      - probability_of_success      (PoS to Phase 1 and approval by stage)
      - grant_stacking              (stackable grant pair recommendations)
      - live_trials                 (ClinicalTrials.gov active trials)
      - fda_intelligence            (openFDA approved drugs + QIDP list)
      - execution_brief             (markdown summary)
    """
    try:
        result = await run_layer3(epi)
        return result
    except Exception as exc:
        logger.exception("Layer 3 execution planning failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Execution planning failed: {exc}")
