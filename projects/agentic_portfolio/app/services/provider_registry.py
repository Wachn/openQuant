from __future__ import annotations


class ProviderRegistryService:
    def __init__(self, provider_gateway) -> None:
        self.provider_gateway = provider_gateway

    def list_providers(self) -> list[dict[str, object]]:
        catalog = self.provider_gateway.catalog()
        entries = catalog.get("all", []) if isinstance(catalog, dict) else []
        providers: list[dict[str, object]] = []
        for item in entries:
            if not isinstance(item, dict):
                continue
            provider_id = str(item.get("id", "")).strip()
            if not provider_id:
                continue
            methods = item.get("auth_methods", [])
            providers.append(
                {
                    "provider_id": provider_id,
                    "label": str(item.get("name") or provider_id),
                    "group": str(item.get("category") or "Providers"),
                    "auth_methods": [
                        str(method.get("id"))
                        for method in methods
                        if isinstance(method, dict) and str(method.get("id", "")).strip()
                    ],
                }
            )
        return providers
