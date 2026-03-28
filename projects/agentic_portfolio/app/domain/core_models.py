from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RiskProfile(str, Enum):
    AGGRESSIVE = "aggressive"
    NEUTRAL = "neutral"
    CONSERVATIVE = "conservative"


class AssetType(str, Enum):
    STOCK = "stock"
    COMMODITY = "commodity"
    CRYPTO = "crypto"
    ETF = "etf"
    FX = "fx"


class BrokerType(str, Enum):
    IBKR_PAPER = "ibkr_paper"
    MT5_PAPER = "mt5_paper"


class Position(BaseModel):
    symbol: str
    asset: AssetType
    quantity: float
    avg_cost: float
    last_price: float


class PortfolioSnapshot(BaseModel):
    as_of_ts: datetime
    equity: float
    cash: float
    daily_pnl: float
    drawdown: float
    risk_profile: RiskProfile
    positions: List[Position] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    as_of_ts: datetime
    symbol: str
    asset: AssetType
    price: float
    change_pct: float
    volatility: float
    source: str
    raw_hash: str


class Suggestion(BaseModel):
    suggestion_id: str
    title: str
    thesis: str
    confidence: float
    impact_score: float
    status: str = "new"
    evidence_refs: List[str] = Field(default_factory=list)


class RunState(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"


class RunRecord(BaseModel):
    run_id: str
    run_type: str
    state: RunState
    started_at: datetime
    finished_at: Optional[datetime] = None
    config_hash: str
    metadata: Dict[str, str] = Field(default_factory=dict)


class CriticResult(BaseModel):
    critic: str
    passed: bool
    reason: str


class TradeProposal(BaseModel):
    proposal_id: str
    symbol: str
    asset: AssetType
    side: str
    quantity: float
    entry_price: float
    invalidation: str
    time_horizon: str
    evidence_refs: List[str]


class RiskDecision(BaseModel):
    profile: RiskProfile
    decision: str
    max_position_size: float
    constraints: List[str] = Field(default_factory=list)


class ManagerDecision(BaseModel):
    action: str
    rationale: str
    approved_profile: Optional[RiskProfile] = None


class TradeTicket(BaseModel):
    ticket_id: str
    run_id: str
    symbol: str
    asset: AssetType
    side: str
    order_type: str
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_horizon: str
    invalidation: str
    evidence_refs: List[str]


class SimulationResult(BaseModel):
    expected_return_pct: float
    expected_drawdown_pct: float
    cost_estimate: float
    slippage_estimate: float


class ExecutionReceipt(BaseModel):
    order_id: str
    ticket_id: str
    run_id: str
    broker: BrokerType
    status: str
    idempotency_key: str
    submitted_at: datetime


class ExecutionOrderStatus(BaseModel):
    order_id: str
    broker: BrokerType
    status: str
    updated_at: datetime


class ExecutionFill(BaseModel):
    fill_id: str
    order_id: str
    broker: BrokerType
    quantity: float
    price: float
    filled_at: datetime


class PortfolioNavPoint(BaseModel):
    ts: datetime
    nav: float
    return_pct: float


class PortfolioAllocationItem(BaseModel):
    bucket: str
    value: float
    weight_pct: float


class PortfolioMoverItem(BaseModel):
    symbol: str
    contribution: float
    weight_pct: float


class PortfolioRiskSnapshot(BaseModel):
    drawdown_pct: float
    concentration_score: float
    largest_position_pct: float


class PortfolioBreakdownResponse(BaseModel):
    run_id: str
    as_of_ts: datetime
    period: str
    frequency: str
    holdings: List[Dict[str, object]]
    cash_breakdown: List[Dict[str, object]]
    allocation: Dict[str, List[PortfolioAllocationItem]]
    movers: Dict[str, List[PortfolioMoverItem]]
    risk: PortfolioRiskSnapshot
    nav_series: List[PortfolioNavPoint]
