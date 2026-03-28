from __future__ import annotations


class CapabilityService:
    def get_capabilities(
        self,
        session_id: str,
        binding: dict[str, object],
        auth_status: dict[str, object],
        provider_connections: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        session_bound = binding.get("status") == "connected"
        auth_valid = auth_status.get("status") == "auth_valid"
        runtime_connection_ready = False
        for connection in provider_connections or []:
            if not connection.get("enabled"):
                continue
            auth_method = connection.get("auth_method")
            if auth_method in {"chatgpt-browser", "chatgpt-headless"} and not connection.get("oauth_connected"):
                continue
            runtime_connection_ready = True
            break

        can_bind = auth_valid or runtime_connection_ready
        return {
            "session_id": session_id,
            "connection": {
                "can_select_provider": True,
                "can_authenticate": True,
                "can_load_models": can_bind,
                "can_bind_session": can_bind,
                "bind_block_reason": None if can_bind else "auth_not_valid",
            },
            "chat": {
                "can_send": session_bound,
                "send_block_reason": None if session_bound else "session_not_bound",
            },
            "broker": {
                "can_sync": True,
                "can_submit_paper_order": True,
                "submit_block_reason": None,
            },
            "promotion": {
                "can_promote_change": True,
                "promote_block_reason": None,
            },
        }
