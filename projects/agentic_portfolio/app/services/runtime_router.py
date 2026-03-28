from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RoutingDecision:
    route: str
    agents: list[str]
    required_snapshots: list[str]
    allow_tools: dict[str, bool]


class RuntimeRouter:
    def route_user_message(self, text: str, requested_agent: str | None = None) -> RoutingDecision:
        lowered = text.lower()
        if "promote" in lowered or "ticket" in lowered:
            return RoutingDecision(
                route="promotion",
                agents=[requested_agent or "session_concierge", "promotion_gate"],
                required_snapshots=["broker", "market"],
                allow_tools={"broker": False, "report": True},
            )
        if "refresh" in lowered or "monitor" in lowered:
            return RoutingDecision(
                route="monitoring",
                agents=[requested_agent or "session_concierge", "market_monitor_agent", "broker_sync_agent"],
                required_snapshots=["market", "broker"],
                allow_tools={"broker": True, "report": True},
            )
        return RoutingDecision(
            route="advisory",
            agents=[requested_agent or "session_concierge"],
            required_snapshots=["portfolio"],
            allow_tools={"broker": False, "report": True},
        )
