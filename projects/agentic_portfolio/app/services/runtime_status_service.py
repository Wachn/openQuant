from __future__ import annotations


class RuntimeStatusService:
    def status(self, session_binding: dict[str, object], auth_status: dict[str, object]) -> dict[str, object]:
        return {
            "connection": {
                "provider": session_binding.get("provider_id"),
                "model": session_binding.get("model_id"),
                "session": session_binding.get("session_id"),
                "bind_state": session_binding.get("status", "idle"),
            },
            "auth": auth_status,
            "degraded": False,
        }
