from __future__ import annotations

from pydantic import BaseModel


class Level1SignalBundle(BaseModel):
    snapshot_refs: list[str]
    notes: list[str]


class DebateRecord(BaseModel):
    bull: list[str]
    bear: list[str]


class TradeProposal(BaseModel):
    symbol: str
    side: str
    quantity: float


class RiskDecisionSet(BaseModel):
    approved: bool
    reasons: list[str]


class ManagerDecision(BaseModel):
    action: str
    rationale: str


class OrderTicket(BaseModel):
    symbol: str
    side: str
    quantity: float
