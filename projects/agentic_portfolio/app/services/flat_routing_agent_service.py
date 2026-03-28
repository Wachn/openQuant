from __future__ import annotations

import json
from datetime import datetime, timezone

from app.services.channel_gateway_service import ChannelGatewayService
from app.services.provider_gateway import ProviderGateway
from app.services.runtime_agent_registry import RuntimeAgentRegistry
from app.storage.sqlite_store import SQLiteStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FlatRoutingAgentService:
    SETTINGS_KEY = "flat_router.settings"

    def __init__(
        self,
        store: SQLiteStore,
        runtime_agent_registry: RuntimeAgentRegistry,
        provider_gateway: ProviderGateway,
        channel_gateway_service: ChannelGatewayService,
    ) -> None:
        self.store = store
        self.runtime_agent_registry = runtime_agent_registry
        self.provider_gateway = provider_gateway
        self.channel_gateway_service = channel_gateway_service

    def _default_settings(self) -> dict[str, object]:
        return {
            "engine": "openclaw_flat_router_v1",
            "routing_mode": "flat",
            "default_agent": "suzybae",
            "skills_profile": "openclaw_skeleton",
            "enabled_gateways": ["ibkr_cpapi", "telegram", "whatsapp"],
            "updated_at": _utc_now_iso(),
        }

    def get_settings(self) -> dict[str, object]:
        raw = self.store.get_settings().get(self.SETTINGS_KEY)
        if not raw:
            defaults = self._default_settings()
            self.store.set_setting(self.SETTINGS_KEY, json.dumps(defaults))
            return defaults
        try:
            parsed = json.loads(raw)
        except Exception:
            defaults = self._default_settings()
            self.store.set_setting(self.SETTINGS_KEY, json.dumps(defaults))
            return defaults
        if not isinstance(parsed, dict):
            defaults = self._default_settings()
            self.store.set_setting(self.SETTINGS_KEY, json.dumps(defaults))
            return defaults
        merged = {**self._default_settings(), **parsed}
        return merged

    def update_settings(self, updates: dict[str, object]) -> dict[str, object]:
        current = self.get_settings()
        allowed = {"engine", "routing_mode", "default_agent", "skills_profile", "enabled_gateways"}
        for key, value in updates.items():
            if key in allowed:
                current[key] = value
        current["updated_at"] = _utc_now_iso()
        self.store.set_setting(self.SETTINGS_KEY, json.dumps(current))
        return current

    def _agent_catalog(self) -> list[dict[str, object]]:
        specs = self.runtime_agent_registry.list_specs()
        rows: list[dict[str, object]] = []
        for spec in specs:
            if not spec.valid:
                continue
            rows.append(
                {
                    "agent_id": spec.agent_id,
                    "name": spec.name,
                    "lane_access": spec.lane_access,
                    "purpose": spec.purpose,
                }
            )
        return rows

    def _skills_catalog(self) -> list[dict[str, object]]:
        return [
            {
                "skill_id": "portfolio_management",
                "name": "Portfolio Management",
                "description": "Portfolio state, risk, and rebalance guidance.",
            },
            {
                "skill_id": "world_news_monitor",
                "name": "World News Monitor",
                "description": "Global headlines and macro risk context.",
            },
            {
                "skill_id": "open_data_query",
                "name": "Open Data Query",
                "description": "Open-data lookup and time-series retrieval.",
            },
            {
                "skill_id": "stock_reference",
                "name": "Stock Reference",
                "description": "Stock symbol discovery and quote details.",
            },
            {
                "skill_id": "gateway_operations",
                "name": "Gateway Operations",
                "description": "IBKR and channel gateway connection operations.",
            },
        ]

    def status(self) -> dict[str, object]:
        return {
            "settings": self.get_settings(),
            "agents": self._agent_catalog(),
            "skills": self._skills_catalog(),
            "providers": self.provider_gateway.status(),
            "channels": self.channel_gateway_service.channels_status(),
            "updated_at": _utc_now_iso(),
        }

    def route(self, message: str, preferred_agent: str | None = None) -> dict[str, object]:
        text = message.lower().strip()
        settings = self.get_settings()
        agents = self._agent_catalog()
        agent_ids = {str(item.get("agent_id")) for item in agents}

        selected_agent = preferred_agent if isinstance(preferred_agent, str) and preferred_agent in agent_ids else str(settings.get("default_agent", "suzybae"))

        route = "portfolio_management"
        reason = "Default flat route for portfolio management actions."
        required_data = ["portfolio_dashboard", "portfolio_positions"]
        skills = ["portfolio_management"]

        if any(token in text for token in ["world", "global", "geopolitical", "macro", "breaking news"]):
            route = "world_monitor"
            reason = "Detected world-news or macro monitoring intent."
            required_data = ["world_monitor_feed", "news_cache", "portfolio_dashboard"]
            skills = ["world_news_monitor", "portfolio_management"]
        elif any(token in text for token in ["open data", "dataset", "time series", "openbb", "macro data"]):
            route = "open_data"
            reason = "Detected open-data exploration intent."
            required_data = ["opendata_series", "opendata_overview", "portfolio_dashboard"]
            skills = ["open_data_query", "portfolio_management"]
        elif any(token in text for token in ["stock", "ticker", "symbol", "openstock", "company profile"]):
            route = "stock_reference"
            reason = "Detected stock discovery/reference intent."
            required_data = ["openstock_search", "openstock_snapshot", "watchlist"]
            skills = ["stock_reference", "portfolio_management"]
        elif any(token in text for token in ["gateway", "ibkr", "telegram", "whatsapp", "connect"]):
            route = "gateway_ops"
            reason = "Detected gateway connectivity intent."
            required_data = ["ibkr_session", "gateway_channels", "provider_status"]
            skills = ["gateway_operations"]

        return {
            "engine": settings.get("engine"),
            "routing_mode": settings.get("routing_mode"),
            "message": message,
            "selected_agent": selected_agent,
            "route": route,
            "reason": reason,
            "required_data": required_data,
            "skills": skills,
            "updated_at": _utc_now_iso(),
        }
