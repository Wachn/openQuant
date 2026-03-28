from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuthService:
    def __init__(self, oauth_pkce, secret_storage, provider_registry) -> None:
        self.oauth_pkce = oauth_pkce
        self.secret_storage = secret_storage
        self.provider_registry = provider_registry
        self._auth_state: dict[str, dict[str, object]] = {}

    def _normalize_method(self, method: str) -> str:
        alias = {
            "api-key": "api_key",
            "chatgpt-browser": "chatgpt_browser_oauth",
            "chatgpt-headless": "browserless_oauth",
        }
        return alias.get(method, method)

    def start(self, provider_id: str, method: str, session_id: str) -> dict[str, object]:
        method = self._normalize_method(method)
        if method in {"chatgpt_browser_oauth", "browserless_oauth"}:
            flow = self.oauth_pkce.start_flow(provider_profile_id=provider_id)
            self._auth_state[session_id] = {
                "provider_id": provider_id,
                "method": method,
                "status": "awaiting_auth",
                "state": flow["state"],
                "updated_at": utc_now_iso(),
            }
            return {
                "status": "awaiting_auth",
                "provider_id": provider_id,
                "auth_method": method,
                "authorize_url": flow["authorize_url"],
                "state": flow["state"],
            }
        self._auth_state[session_id] = {
            "provider_id": provider_id,
            "method": method,
            "status": "awaiting_auth",
            "updated_at": utc_now_iso(),
        }
        return {
            "status": "awaiting_auth",
            "provider_id": provider_id,
            "auth_method": method,
        }

    def complete(
        self,
        provider_id: str,
        method: str,
        session_id: str,
        state: str | None = None,
        code: str | None = None,
        api_key: str | None = None,
        token: str | None = None,
        base_url: str | None = None,
    ) -> dict[str, object]:
        method = self._normalize_method(method)
        if method in {"chatgpt_browser_oauth", "browserless_oauth"}:
            if not state or not code:
                raise ValueError("oauth callback state/code required")
            _result = self.oauth_pkce.finish_flow(state=state, code=code)
            self.secret_storage.store(provider_id, {"oauth_state": state, "oauth_code": code})
        elif method == "api_key":
            if not api_key:
                raise ValueError("api key required")
            self.secret_storage.store(provider_id, {"api_key": api_key})
        elif method == "token":
            if not token:
                raise ValueError("token required")
            self.secret_storage.store(provider_id, {"token": token})
        elif method == "base_url":
            if not base_url:
                raise ValueError("base URL required")
            self.secret_storage.store(provider_id, {"base_url": base_url})
        elif method == "base_url_api_key":
            if not base_url or not api_key:
                raise ValueError("base URL and API key required")
            self.secret_storage.store(provider_id, {"base_url": base_url, "api_key": api_key})
        else:
            raise ValueError("unsupported auth method")

        self._auth_state[session_id] = {
            "provider_id": provider_id,
            "method": method,
            "status": "auth_valid",
            "updated_at": utc_now_iso(),
        }
        return {
            "provider_id": provider_id,
            "auth_method": method,
            "status": "auth_valid",
            "redacted_credentials": self.secret_storage.redacted_view(provider_id),
        }

    def logout(self, provider_id: str, session_id: str) -> dict[str, object]:
        self.secret_storage.forget(provider_id)
        self._auth_state[session_id] = {
            "provider_id": provider_id,
            "method": None,
            "status": "idle",
            "updated_at": utc_now_iso(),
        }
        return {"status": "idle", "provider_id": provider_id}

    def status(self, session_id: str) -> dict[str, object]:
        return dict(self._auth_state.get(session_id, {"status": "idle"}))
