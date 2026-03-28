from __future__ import annotations

from app.domain.routing.models import (
    RouteDecision,
    RouteLane,
    RouteRequest,
    RouteSource,
    WorkflowType,
)
from app.domain.routing.registry import BuilderAgentRegistry


class DynamicAgentRouter:
    """Intent-driven routing inspired by OpenCode's agent-mode approach.

    The router selects workflow/lane with deterministic checks while keeping
    internal builder identities hidden by default.
    """

    EXECUTE_KEYWORDS = {
        "execute",
        "place order",
        "submit order",
        "buy now",
        "sell now",
        "confirm ticket",
    }
    TRADE_KEYWORDS = {
        "trade",
        "proposal",
        "rebalance",
        "hedge",
        "position size",
        "invalidation",
    }
    SETTINGS_KEYWORDS = {
        "settings",
        "configure",
        "api key",
        "provider",
        "risk profile",
    }
    STARTUP_KEYWORDS = {
        "startup",
        "morning report",
        "resume",
        "what changed",
    }

    def __init__(self, registry: BuilderAgentRegistry | None = None) -> None:
        self.registry = registry or BuilderAgentRegistry()

    def route(self, request: RouteRequest) -> RouteDecision:
        text = request.message.lower().strip()

        if request.source == RouteSource.STARTUP or self._contains_any(text, self.STARTUP_KEYWORDS):
            return self._startup_report_decision(request)

        if self._contains_any(text, self.SETTINGS_KEYWORDS):
            return RouteDecision(
                lane=RouteLane.RESEARCH,
                workflow=WorkflowType.SETTINGS_UPDATE,
                reason="Message indicates a configuration/settings intent.",
                requires_dag=False,
                requires_market_refresh=False,
                requires_user_confirmation=False,
                internal_builder_plan=self._plan_if_requested(request, ["trader_builder"]),
            )

        if self._contains_any(text, self.EXECUTE_KEYWORDS):
            return RouteDecision(
                lane=RouteLane.TRADE,
                workflow=WorkflowType.EXECUTE_TICKET,
                reason="Message indicates direct order execution intent.",
                requires_dag=True,
                requires_market_refresh=True,
                requires_user_confirmation=not request.automation_enabled,
                internal_builder_plan=self._plan_if_requested(
                    request,
                    [
                        "level1_signals_builder",
                        "level2_research_builder",
                        "level3_trader_builder",
                        "level4_risk_builder",
                        "level5_manager_builder",
                    ],
                ),
            )

        if self._contains_any(text, self.TRADE_KEYWORDS):
            return RouteDecision(
                lane=RouteLane.TRADE,
                workflow=WorkflowType.TRADE_CANDIDATE,
                reason="Message requests trade-level analysis or proposal review.",
                requires_dag=True,
                requires_market_refresh=True,
                requires_user_confirmation=True,
                internal_builder_plan=self._plan_if_requested(
                    request,
                    [
                        "level1_signals_builder",
                        "level2_research_builder",
                        "level3_trader_builder",
                        "level4_risk_builder",
                    ],
                ),
            )

        return RouteDecision(
            lane=RouteLane.RESEARCH,
            workflow=WorkflowType.RESEARCH_QUERY,
            reason="Default route for exploratory analysis and discussion.",
            requires_dag=False,
            requires_market_refresh=False,
            requires_user_confirmation=False,
            internal_builder_plan=self._plan_if_requested(
                request,
                ["level1_signals_builder", "level2_research_builder"],
            ),
        )

    def _startup_report_decision(self, request: RouteRequest) -> RouteDecision:
        return RouteDecision(
            lane=RouteLane.RESEARCH,
            workflow=WorkflowType.STARTUP_REPORT,
            reason="Startup source or startup-related intent detected.",
            requires_dag=False,
            requires_market_refresh=True,
            requires_user_confirmation=False,
            internal_builder_plan=self._plan_if_requested(
                request,
                ["level1_signals_builder", "trader_builder"],
            ),
        )

    @staticmethod
    def _contains_any(text: str, phrases: set[str]) -> bool:
        return any(phrase in text for phrase in phrases)

    def _plan_if_requested(self, request: RouteRequest, names: list[str]) -> list[str] | None:
        if not request.include_internal_plan:
            return None
        return [self.registry.get(name).name for name in names]
