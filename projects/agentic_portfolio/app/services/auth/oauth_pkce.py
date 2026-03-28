from __future__ import annotations

import base64
import hashlib
import secrets
import time
import uuid


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


class OAuthPkceService:
    def __init__(self, loopback_port: int = 1455) -> None:
        self.loopback_port = loopback_port
        self._flows: dict[str, dict[str, object]] = {}

    def start_flow(self, provider_profile_id: str) -> dict[str, object]:
        state = secrets.token_urlsafe(24)
        code_verifier = _b64url(secrets.token_bytes(48))
        challenge = _b64url(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        created_at = int(time.time())
        expires_at = created_at + 600
        flow = {
            "flow_id": str(uuid.uuid4()),
            "state": state,
            "provider_profile_id": provider_profile_id,
            "code_verifier": code_verifier,
            "code_challenge": challenge,
            "created_at": created_at,
            "expires_at": expires_at,
            "consumed": False,
        }
        self._flows[state] = flow
        return {
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "callback_url": f"http://127.0.0.1:{self.loopback_port}/auth/callback",
            "authorize_url": (
                "https://auth.openai.com/oauth/authorize"
                f"?response_type=code&state={state}&code_challenge={challenge}&code_challenge_method=S256"
            ),
        }

    def finish_flow(self, state: str, code: str) -> dict[str, object]:
        flow = self._flows.get(state)
        if flow is None:
            raise ValueError("Invalid state - potential CSRF attack.")
        if flow.get("consumed"):
            raise ValueError("OAuth state already consumed.")
        if int(time.time()) > int(flow["expires_at"]):
            raise ValueError("OAuth state expired.")
        flow["consumed"] = True
        return {
            "provider_profile_id": flow["provider_profile_id"],
            "state": state,
            "code": code,
            "code_verifier": flow["code_verifier"],
            "status": "connected",
        }
