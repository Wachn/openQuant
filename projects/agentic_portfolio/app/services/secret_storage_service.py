from __future__ import annotations


class SecretStorageService:
    def __init__(self) -> None:
        self._secrets: dict[str, dict[str, str]] = {}

    def store(self, provider_id: str, values: dict[str, str]) -> None:
        filtered = {k: v for k, v in values.items() if v}
        self._secrets[provider_id] = filtered

    def forget(self, provider_id: str) -> None:
        self._secrets.pop(provider_id, None)

    def has(self, provider_id: str) -> bool:
        return provider_id in self._secrets and bool(self._secrets[provider_id])

    def redacted_view(self, provider_id: str) -> dict[str, str]:
        values = self._secrets.get(provider_id, {})
        return {k: "***" for k in values.keys()}
