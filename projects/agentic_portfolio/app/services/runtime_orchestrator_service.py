from __future__ import annotations

from typing import Dict

from app.services.connector_routing_service import ConnectorRoutingService
from app.services.memory_summary_service import MemorySummaryService
from app.services.route_trace_service import RouteTraceService


class RuntimeOrchestratorService:
    def __init__(
        self,
        route_trace_service: RouteTraceService,
        memory_summary_service: MemorySummaryService,
        connector_routing_service: ConnectorRoutingService,
        enabled: bool,
    ) -> None:
        self.route_trace_service = route_trace_service
        self.memory_summary_service = memory_summary_service
        self.connector_routing_service = connector_routing_service
        self.enabled = enabled

    def status(self) -> Dict[str, object]:
        return {
            "enabled": self.enabled,
            "services": {
                "route_trace": True,
                "memory_summary": True,
                "connector_routing": True,
            },
        }

    def orchestrate(
        self,
        session_id: str,
        message: str,
        route_hint: str,
        preferred_connection_id: str | None,
    ) -> Dict[str, object]:
        route_class = "deep_reasoning" if route_hint in {"trade_candidate", "execute_ticket", "deep"} else "fast_summary"
        connector = self.connector_routing_service.select_connector(
            preferred_connection_id=preferred_connection_id,
            route_class=route_class,
        )
        connector_id = str(connector.get("connection_id")) if connector else None
        trace = self.route_trace_service.record(
            session_id=session_id,
            route=route_hint,
            connector_id=connector_id,
            status="selected" if connector_id else "no_connector",
            metadata={
                "route_class": route_class,
                "message_preview": message[:200],
            },
        )
        summary = self.memory_summary_service.summarize_session(session_id=session_id)
        return {
            "session_id": session_id,
            "route": route_hint,
            "route_class": route_class,
            "selected_connector": connector,
            "trace": trace,
            "memory": summary,
        }
