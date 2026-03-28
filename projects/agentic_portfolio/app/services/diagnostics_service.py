from __future__ import annotations


def _redact(message: str) -> str:
    return message.replace("api_key", "***").replace("token", "***")


class DiagnosticsService:
    def collect(self, error: str | None = None) -> dict[str, object]:
        return {
            "status": "ok" if error is None else "degraded",
            "error": _redact(error) if error else None,
            "redaction": "enabled",
        }
