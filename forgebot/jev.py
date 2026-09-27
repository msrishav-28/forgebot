"""Optional Jev gatekeeper for pre-screening bot events."""

from __future__ import annotations

import os
from dataclasses import dataclass

API_KEY_ENV = "TYPESAFE_API_KEY"
THRESHOLD_ENV = "FORGEBOT_JEV_THRESHOLD"
DEFAULT_THRESHOLD = 0.5


@dataclass
class GateDecision:
    proceed: bool
    reason: str
    probability: float | None = None
    detail: str = ""


def gate_configured() -> bool:
    return bool(os.environ.get(API_KEY_ENV))


def _default_threshold() -> float:
    raw = os.environ.get(THRESHOLD_ENV)
    try:
        return float(raw) if raw is not None else DEFAULT_THRESHOLD
    except ValueError:
        return DEFAULT_THRESHOLD


def screen_event(question: str, event: str, threshold: float | None = None) -> GateDecision:
    """Ask Jev whether an event warrants a full agent run."""
    if not gate_configured():
        return GateDecision(True, "gate-off")
    try:
        from pydantic import BaseModel, Field
        from pydantic_ai import Agent
    except ImportError:
        return GateDecision(
            True,
            "gate-off",
            detail="TYPESAFE_API_KEY is set but 'forgebot[jev]' is not installed",
        )
    limit = threshold if threshold is not None else _default_threshold()

    class _Screen(BaseModel):
        probability: float = Field(
            ge=0.0,
            le=1.0,
            description="Probability that the event warrants a full agent run",
        )

    try:
        agent = Agent("typesafe:jev-latest", output_type=_Screen)
        result = agent.run_sync(f"{question}\n\n=== EVENT ===\n{event}")
        probability = float(result.output.probability)
    except Exception as exc:  # The optional cost-saving gate must never block a bot run.
        return GateDecision(True, "error", detail=f"{type(exc).__name__}: {exc}"[:300])
    if probability >= limit:
        return GateDecision(True, "pass", probability=probability)
    return GateDecision(False, "skip", probability=probability)
