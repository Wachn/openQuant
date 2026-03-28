from __future__ import annotations

from typing import Dict, Optional

from app.services.provider_gateway import ProviderGateway


class ConnectorRoutingService:
    def __init__(self, provider_gateway: ProviderGateway) -> None:
        self.provider_gateway = provider_gateway

    def select_connector(
        self,
        preferred_connection_id: str | None,
        route_class: str,
    ) -> Dict[str, object]:
        connections = self.provider_gateway.list_connections()
        if preferred_connection_id:
            selected = next((item for item in connections if item.get("connection_id") == preferred_connection_id), None)
            if selected is not None:
                return selected

        enabled_connections = [
            item
            for item in connections
            if bool(item.get("enabled", False)) and route_class == str(item.get("route_class", route_class))
        ]
        if enabled_connections:
            return enabled_connections[0]

        any_enabled = [item for item in connections if bool(item.get("enabled", False))]
        if any_enabled:
            return any_enabled[0]

        return {}

    def connector_health(self) -> Dict[str, object]:
        return self.provider_gateway.status()
