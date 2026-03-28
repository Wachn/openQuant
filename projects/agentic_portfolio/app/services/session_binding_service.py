from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionBindingService:
    def __init__(self) -> None:
        self._bindings: dict[str, dict[str, object]] = {}

    def bind(self, session_id: str, provider_id: str, auth_method: str, model_id: str, base_url: str | None = None) -> dict[str, object]:
        if not provider_id or not auth_method or not model_id:
            raise ValueError("provider/auth/model required before binding")
        self._bindings[session_id] = {
            "session_id": session_id,
            "provider_id": provider_id,
            "auth_method": auth_method,
            "model_id": model_id,
            "base_url": base_url,
            "status": "connected",
            "updated_at": utc_now_iso(),
        }
        return dict(self._bindings[session_id])

    def unbind(self, session_id: str) -> dict[str, object]:
        self._bindings.pop(session_id, None)
        return {"session_id": session_id, "status": "idle"}

    def reset(self, session_id: str) -> dict[str, object]:
        self._bindings.pop(session_id, None)
        return {"session_id": session_id, "status": "idle", "reset": True}

    def status(self, session_id: str) -> dict[str, object]:
        return dict(self._bindings.get(session_id, {"session_id": session_id, "status": "idle"}))
