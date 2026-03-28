from __future__ import annotations

import uuid

from app.services.promotion.contracts import (
    DebateRecord,
    Level1SignalBundle,
    ManagerDecision,
    OrderTicket,
    RiskDecisionSet,
    TradeProposal,
)
from app.services.promotion.critics import run_default_critics


class PromotionLane:
    def __init__(self, run_recorder) -> None:
        self.run_recorder = run_recorder

    async def run(self, input_artifacts: dict[str, object]) -> dict[str, object]:
        run_id = self.run_recorder.start_run("promotion", {"input_artifacts": sorted(input_artifacts.keys())})
        l1 = Level1SignalBundle(snapshot_refs=list(input_artifacts.keys()), notes=["signals normalized"])
        l2 = DebateRecord(bull=["trend supports entry"], bear=["volatility elevated"])
        l3 = TradeProposal(symbol="AAPL", side="buy", quantity=10)
        critics = run_default_critics()
        l4 = RiskDecisionSet(approved=all(item.ok for item in critics), reasons=[reason for item in critics for reason in item.reasons])
        action = "approve" if l4.approved else "reject"
        l5 = ManagerDecision(action=action, rationale="promotion lane deterministic decision")
        ticket = OrderTicket(symbol=l3.symbol, side=l3.side, quantity=l3.quantity) if l4.approved else None
        artifact_id = self.run_recorder.add_artifact(
            run_id=run_id,
            kind="promotion_lane",
            payload={
                "l1": l1.model_dump(mode="json"),
                "l2": l2.model_dump(mode="json"),
                "l3": l3.model_dump(mode="json"),
                "l4": l4.model_dump(mode="json"),
                "l5": l5.model_dump(mode="json"),
                "ticket": ticket.model_dump(mode="json") if ticket is not None else None,
            },
        )
        self.run_recorder.finish_run(run_id=run_id, status="succeeded")
        return {
            "run_id": run_id,
            "artifact_id": artifact_id,
            "decision": l5.model_dump(mode="json"),
            "ticket": ticket.model_dump(mode="json") if ticket is not None else None,
            "trace_id": str(uuid.uuid4()),
        }
