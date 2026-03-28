from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class RouteSource(str, Enum):
    CHAT = "chat"
    STARTUP = "startup"
    WEBHOOK = "webhook"
    SYSTEM = "system"


class RouteLane(str, Enum):
    RESEARCH = "research"
    TRADE = "trade"


class WorkflowType(str, Enum):
    STARTUP_REPORT = "startup_report"
    PORTFOLIO_REVIEW = "portfolio_review"
    RESEARCH_QUERY = "research_query"
    TRADE_CANDIDATE = "trade_candidate"
    EXECUTE_TICKET = "execute_ticket"
    SETTINGS_UPDATE = "settings_update"


@dataclass(frozen=True)
class RouteRequest:
    message: str
    source: RouteSource
    automation_enabled: bool = False
    include_internal_plan: bool = False


@dataclass(frozen=True)
class RouteDecision:
    lane: RouteLane
    workflow: WorkflowType
    reason: str
    requires_dag: bool
    requires_market_refresh: bool
    requires_user_confirmation: bool
    internal_builder_plan: Optional[List[str]] = None
