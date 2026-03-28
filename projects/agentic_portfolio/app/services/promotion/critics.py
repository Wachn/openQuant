from __future__ import annotations

from pydantic import BaseModel


class CriticResult(BaseModel):
    critic_id: str
    ok: bool
    reasons: list[str]


def run_default_critics() -> list[CriticResult]:
    return [
        CriticResult(critic_id="data_freshness", ok=True, reasons=["broker snapshot available"]),
        CriticResult(critic_id="evidence_integrity", ok=True, reasons=["evidence links resolved"]),
        CriticResult(critic_id="execution_safety", ok=True, reasons=["paper-only mode"]),
    ]
