from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from app.storage.sqlite_store import SQLiteStore


OPENAI_OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
OPENAI_OAUTH_AUTHORIZE_URL = "https://auth.openai.com/oauth/authorize"
OPENAI_OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"

OAUTH_LOOPBACK_SHUTDOWN_AFTER_S = 10 * 60
OAUTH_REFRESH_EARLY_S = 5 * 60


PROVIDER_CATALOG: list[dict[str, object]] = [
    {
        "id": "openai",
        "name": "OpenAI",
        "category": "Popular",
        "auth_methods": [
            {
                "id": "chatgpt-browser",
                "type": "oauth-browser",
                "label": "ChatGPT (Pro/Plus - browser)",
                "description": "Use ChatGPT browser sign-in flow",
                "connect_url": None,
                "api_key_env": None,
            },
            {
                "id": "chatgpt-headless",
                "type": "oauth-headless",
                "label": "ChatGPT (Pro/Plus - headless)",
                "description": "Use headless OAuth-style flow",
                "connect_url": None,
                "api_key_env": None,
            },
            {
                "id": "api-key",
                "type": "api",
                "label": "Manually Enter API key",
                "description": "Use OpenAI API key",
                "connect_url": None,
                "api_key_env": "OPENAI_API_KEY",
            },
        ],
        "models": [
            {"id": "openai/gpt-5.4", "name": "GPT-5.4"},
            {"id": "openai/gpt-5.3-codex", "name": "GPT-5.3 Codex"},
            {"id": "openai/gpt-5", "name": "GPT-5"},
            {"id": "openai/gpt-5-mini", "name": "GPT-5 Mini"},
            {"id": "openai/gpt-5-mini-2025-08-07", "name": "GPT-5 Mini (2025-08-07)"},
            {"id": "openai/gpt-5-nano", "name": "GPT-5 Nano"},
            {"id": "openai/o3", "name": "o3"},
            {"id": "openai/o3-mini", "name": "o3 Mini"},
            {"id": "openai/o4-mini", "name": "o4 Mini"},
            {"id": "openai/gpt-4.1", "name": "GPT-4.1"},
            {"id": "openai/gpt-4.1-mini", "name": "GPT-4.1 Mini"},
            {"id": "openai/gpt-4.1-nano", "name": "GPT-4.1 Nano"},
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "openai/codex-mini-latest", "name": "Codex Mini"},
        ],
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "category": "Popular",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "Claude API key",
                "description": "Use Anthropic API key",
                "connect_url": None,
                "api_key_env": "ANTHROPIC_API_KEY",
            }
        ],
        "models": [
            {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4"},
            {"id": "anthropic/claude-3-7-sonnet", "name": "Claude 3.7 Sonnet"},
            {"id": "anthropic/claude-3-5-haiku", "name": "Claude 3.5 Haiku"},
        ],
    },
    {
        "id": "google",
        "name": "Google",
        "category": "Popular",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "Gemini API key",
                "description": "Use Google AI API key",
                "connect_url": None,
                "api_key_env": "GOOGLE_API_KEY",
            }
        ],
        "models": [
            {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
            {"id": "google/gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
        ],
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "category": "Popular",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "DeepSeek API key",
                "description": "Use DeepSeek API key",
                "connect_url": None,
                "api_key_env": "DEEPSEEK_API_KEY",
            }
        ],
        "models": [
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat"},
            {"id": "deepseek/deepseek-reasoner", "name": "DeepSeek Reasoner"},
            {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1"},
        ],
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "category": "Other",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "OpenRouter API key",
                "description": "Use OpenRouter API key",
                "connect_url": None,
                "api_key_env": "OPENROUTER_API_KEY",
            }
        ],
        "models": [
            {"id": "openrouter/openai/gpt-4o-mini", "name": "OpenAI GPT-4o Mini"},
            {"id": "openrouter/anthropic/claude-3.7-sonnet", "name": "Claude 3.7 Sonnet"},
        ],
    },
    {
        "id": "xai",
        "name": "xAI",
        "category": "Other",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "xAI API key",
                "description": "Use xAI API key",
                "connect_url": None,
                "api_key_env": "XAI_API_KEY",
            }
        ],
        "models": [
            {"id": "xai/grok-4", "name": "Grok 4"},
            {"id": "xai/grok-3-mini", "name": "Grok 3 Mini"},
        ],
    },
    {
        "id": "groq",
        "name": "Groq",
        "category": "Other",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "Groq API key",
                "description": "Use Groq API key",
                "connect_url": None,
                "api_key_env": "GROQ_API_KEY",
            }
        ],
        "models": [
            {"id": "groq/llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile"},
            {"id": "groq/deepseek-r1-distill-llama-70b", "name": "DeepSeek R1 Distill Llama 70B"},
        ],
    },
    {
        "id": "mistral",
        "name": "Mistral",
        "category": "Other",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "Mistral API key",
                "description": "Use Mistral API key",
                "connect_url": None,
                "api_key_env": "MISTRAL_API_KEY",
            }
        ],
        "models": [
            {"id": "mistral/magistral-medium", "name": "Magistral Medium"},
            {"id": "mistral/codestral-latest", "name": "Codestral Latest"},
        ],
    },
    {
        "id": "together",
        "name": "Together",
        "category": "Other",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "Together API key",
                "description": "Use Together API key",
                "connect_url": None,
                "api_key_env": "TOGETHER_API_KEY",
            }
        ],
        "models": [
            {"id": "together/deepseek-ai/DeepSeek-R1", "name": "DeepSeek R1"},
            {"id": "together/meta-llama/Llama-3.3-70B-Instruct-Turbo", "name": "Llama 3.3 70B Instruct"},
        ],
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "category": "Other",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "Cohere API key",
                "description": "Use Cohere API key",
                "connect_url": None,
                "api_key_env": "COHERE_API_KEY",
            }
        ],
        "models": [
            {"id": "cohere/command-a", "name": "Command A"},
            {"id": "cohere/command-r-plus", "name": "Command R+"},
        ],
    },
    {
        "id": "perplexity",
        "name": "Perplexity",
        "category": "Other",
        "auth_methods": [
            {
                "id": "api-key",
                "type": "api",
                "label": "Perplexity API key",
                "description": "Use Perplexity API key",
                "connect_url": None,
                "api_key_env": "PERPLEXITY_API_KEY",
            }
        ],
        "models": [
            {"id": "perplexity/sonar-pro", "name": "Sonar Pro"},
            {"id": "perplexity/sonar-reasoning-pro", "name": "Sonar Reasoning Pro"},
        ],
    },
    {
        "id": "local",
        "name": "Local",
        "category": "Other",
        "auth_methods": [
            {
                "id": "local-runtime",
                "type": "local",
                "label": "Local runtime",
                "description": "Use local model runtime",
                "connect_url": None,
                "api_key_env": None,
            }
        ],
        "models": [
            {"id": "ollama/llama3.1", "name": "Llama 3.1"},
            {"id": "ollama/qwen2.5-coder", "name": "Qwen 2.5 Coder"},
        ],
    },
]


class ProviderGateway:
    def __init__(
        self,
        store: SQLiteStore,
        local_model_enabled: bool,
        local_model_name: str,
        external_model_enabled: bool,
        external_model_name: str,
    ) -> None:
        self.store = store
        self._oauth_pending: dict[str, dict[str, object]] = {}
        self._oauth_loopback_lock = threading.Lock()
        self._oauth_loopback_server: http.server.HTTPServer | None = None
        self._oauth_loopback_thread: threading.Thread | None = None
        self._oauth_loopback_timer: threading.Timer | None = None
        self._oauth_loopback_bind: tuple[str, int, str] | None = None
        self._oauth_refresh_lock = threading.Lock()
        self._seed_defaults(
            local_model_enabled=local_model_enabled,
            local_model_name=local_model_name,
            external_model_enabled=external_model_enabled,
            external_model_name=external_model_name,
        )

    def _parse_loopback_redirect(self, redirect_uri: str) -> tuple[str, int, str]:
        parsed = urllib.parse.urlparse(redirect_uri)
        host = parsed.hostname or "127.0.0.1"
        if host == "localhost":
            host = "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        return host, port, path

    def _ensure_oauth_loopback_server(self, provider_id: str, redirect_uri: str) -> bool:
        if provider_id != "openai":
            return True

        host, port, path = self._parse_loopback_redirect(redirect_uri)
        bind_key = (host, port, path)

        with self._oauth_loopback_lock:
            if self._oauth_loopback_thread and self._oauth_loopback_thread.is_alive() and self._oauth_loopback_bind == bind_key:
                return True

            if self._oauth_loopback_server is not None:
                try:
                    self._oauth_loopback_server.shutdown()
                except Exception:
                    pass
                self._oauth_loopback_server = None

            if self._oauth_loopback_timer is not None:
                try:
                    self._oauth_loopback_timer.cancel()
                except Exception:
                    pass
                self._oauth_loopback_timer = None

            gateway = self

            class LoopbackHandler(http.server.BaseHTTPRequestHandler):
                def log_message(self, format: str, *args: object) -> None:
                    return

                def do_GET(self) -> None:  # noqa: N802
                    try:
                        url = urllib.parse.urlparse(self.path)
                        if url.path != path:
                            self.send_response(404)
                            self.send_header("Content-Type", "text/plain; charset=utf-8")
                            self.end_headers()
                            self.wfile.write(b"Not found")
                            return
                        query = urllib.parse.parse_qs(url.query)
                        state = (query.get("state") or [None])[0]
                        code = (query.get("code") or [None])[0]
                        error = (query.get("error") or [None])[0]
                        error_description = (query.get("error_description") or [None])[0]
                        status_code, html = gateway.oauth_callback(
                            provider_id=provider_id,
                            state=state,
                            code=code,
                            error=error,
                            error_description=error_description,
                        )
                        self.send_response(status_code)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(html.encode("utf-8"))
                    finally:
                        srv = gateway._oauth_loopback_server
                        if srv is not None:
                            threading.Thread(target=srv.shutdown, daemon=True).start()

            class ReusableHTTPServer(http.server.HTTPServer):
                allow_reuse_address = True

            try:
                self._oauth_loopback_server = ReusableHTTPServer((host, port), LoopbackHandler)
            except OSError as exc:
                # Common Windows errno for address-in-use is 10048.
                if getattr(exc, "errno", None) in {getattr(socket, "EADDRINUSE", 10048), 10048}:
                    return False
                return False

            self._oauth_loopback_bind = bind_key

            def serve() -> None:
                try:
                    assert self._oauth_loopback_server is not None
                    self._oauth_loopback_server.serve_forever(poll_interval=0.2)
                finally:
                    with self._oauth_loopback_lock:
                        if self._oauth_loopback_server is not None:
                            try:
                                self._oauth_loopback_server.server_close()
                            except Exception:
                                pass
                        self._oauth_loopback_server = None
                        self._oauth_loopback_thread = None
                        self._oauth_loopback_timer = None
                        self._oauth_loopback_bind = None

            self._oauth_loopback_thread = threading.Thread(target=serve, name="oauth-loopback", daemon=True)
            self._oauth_loopback_thread.start()
            self._oauth_loopback_timer = threading.Timer(OAUTH_LOOPBACK_SHUTDOWN_AFTER_S, self._oauth_loopback_server.shutdown)
            self._oauth_loopback_timer.daemon = True
            self._oauth_loopback_timer.start()
            return True

    def _oauth_should_refresh(self, oauth: dict[str, object]) -> bool:
        access = oauth.get("access")
        refresh = oauth.get("refresh")
        if not isinstance(access, str) or not access.strip():
            return False
        if not isinstance(refresh, str) or not refresh.strip():
            return False
        expires_at = oauth.get("expires_at")
        if isinstance(expires_at, (int, float)):
            return time.time() >= float(expires_at) - OAUTH_REFRESH_EARLY_S
        return False

    def _oauth_refresh(self, connection_id: str, connection: dict[str, object], oauth: dict[str, object]) -> dict[str, object] | None:
        refresh_token = oauth.get("refresh")
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            return None

        payload = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": OPENAI_OAUTH_CLIENT_ID,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            OPENAI_OAUTH_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                body = response.read().decode("utf-8")
                token_payload = json.loads(body) if body else {}
        except Exception:
            return None

        access = token_payload.get("access_token")
        if not isinstance(access, str) or not access.strip():
            return None
        new_refresh = token_payload.get("refresh_token")
        expires_in_raw = token_payload.get("expires_in")
        now = time.time()
        try:
            expires_in = float(expires_in_raw)
        except (TypeError, ValueError):
            expires_in = None
        expires_at = (now + expires_in) if isinstance(expires_in, (int, float)) else None

        updated_oauth: dict[str, object] = {
            "type": "oauth",
            "access": access,
            "refresh": (new_refresh if isinstance(new_refresh, str) and new_refresh.strip() else refresh_token),
            "expires_in": expires_in if expires_in is not None else expires_in_raw,
            "obtained_at": now,
        }
        if expires_at is not None:
            updated_oauth["expires_at"] = expires_at

        metadata = connection.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["oauth"] = updated_oauth
        refreshed_account_id = self._extract_account_id_from_token_payload(token_payload)
        if isinstance(refreshed_account_id, str) and refreshed_account_id.strip():
            metadata["chatgpt_account_id"] = refreshed_account_id.strip()
        self.store.upsert_provider_connection(
            connection_id=connection_id,
            provider=connection["provider"],
            model=connection["model"],
            base_url=connection.get("base_url"),
            api_key_env=connection.get("api_key_env"),
            enabled=connection.get("enabled", True),
            metadata=metadata,
        )
        refreshed = self.store.get_provider_connection(connection_id)
        if refreshed is None:
            return None
        refreshed_meta = refreshed.get("metadata", {})
        if isinstance(refreshed_meta, dict) and isinstance(refreshed_meta.get("oauth"), dict):
            return refreshed_meta["oauth"]
        return None

    def _connection_bearer_token(self, connection_id: str, connection: dict[str, object]) -> str | None:
        provider = str(connection.get("provider", ""))
        metadata = connection.get("metadata", {})
        oauth_auth_methods = {"chatgpt-browser", "chatgpt-headless"}
        if isinstance(metadata, dict):
            auth_method = metadata.get("auth_method")
            oauth_only = isinstance(auth_method, str) and auth_method in oauth_auth_methods

            oauth = metadata.get("oauth")
            if isinstance(oauth, dict):
                access = oauth.get("access")
                if isinstance(access, str) and access.strip():
                    if provider == "openai" and self._oauth_should_refresh(oauth):
                        with self._oauth_refresh_lock:
                            reloaded = self.store.get_provider_connection(connection_id)
                            if reloaded is not None:
                                re_meta = reloaded.get("metadata", {})
                                re_oauth = re_meta.get("oauth") if isinstance(re_meta, dict) else None
                                if isinstance(re_oauth, dict) and self._oauth_should_refresh(re_oauth):
                                    refreshed = self._oauth_refresh(connection_id=connection_id, connection=reloaded, oauth=re_oauth)
                                    if isinstance(refreshed, dict):
                                        refreshed_access = refreshed.get("access")
                                        if isinstance(refreshed_access, str) and refreshed_access.strip():
                                            return refreshed_access.strip()
                    return access.strip()

            if oauth_only:
                return None

            direct = metadata.get("api_key")
            if isinstance(direct, str) and direct.strip():
                return direct.strip()

        env_name = connection.get("api_key_env")
        if isinstance(env_name, str) and env_name.strip():
            value = os.getenv(env_name.strip())
            if value and value.strip():
                return value.strip()
        return None

    def _oauth_pending_key(self, state: str) -> str:
        return f"oauth_pending_{state}"

    def _save_oauth_pending(self, state: str, payload: dict[str, object]) -> None:
        self._oauth_pending[state] = payload
        self.store.set_setting(self._oauth_pending_key(state), json.dumps(payload))

    def _load_oauth_pending(self, state: str) -> dict[str, object] | None:
        pending = self._oauth_pending.get(state)
        if pending is not None:
            return pending
        raw = self.store.get_settings().get(self._oauth_pending_key(state))
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                self._oauth_pending[state] = parsed
                return parsed
        except Exception:
            return None
        return None

    def _clear_oauth_pending(self, state: str) -> None:
        self._oauth_pending.pop(state, None)
        self.store.set_setting(self._oauth_pending_key(state), "")

    def _provider_model_name(self, provider: str, model: str) -> str:
        prefix = f"{provider}/"
        normalized = model
        while normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
        if provider == "openrouter" and normalized.startswith("openrouter/"):
            return normalized[len("openrouter/"):]
        if provider == "together" and normalized.startswith("together/"):
            return normalized[len("together/"):]
        return normalized

    def _is_chatgpt_auth_connection(self, connection: dict[str, object]) -> bool:
        metadata = connection.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        auth_method = metadata.get("auth_method")
        return isinstance(auth_method, str) and auth_method in {"chatgpt-browser", "chatgpt-headless"}

    def _extract_chatgpt_account_id(self, token: str) -> str | None:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload = parts[1]
        padded = payload + ("=" * (-len(payload) % 4))
        try:
            decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
            parsed = json.loads(decoded.decode("utf-8"))
        except Exception:
            return None
        if not isinstance(parsed, dict):
            return None
        auth_claim = parsed.get("https://api.openai.com/auth")
        if not isinstance(auth_claim, dict):
            return None
        account_id = auth_claim.get("chatgpt_account_id")
        if isinstance(account_id, str) and account_id.strip():
            return account_id.strip()
        return None

    def _extract_account_id_from_token_payload(self, token_payload: dict[str, object]) -> str | None:
        direct_account_id = token_payload.get("account_id")
        if isinstance(direct_account_id, str) and direct_account_id.strip():
            return direct_account_id.strip()
        id_token = token_payload.get("id_token")
        if isinstance(id_token, str) and id_token.strip():
            return self._extract_chatgpt_account_id(id_token)
        return None

    def _decode_openai_response_body(self, body: str) -> dict[str, object]:
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        output_fragments: list[str] = []
        final_output_text: str | None = None

        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line.startswith("data:"):
                continue
            payload_str = line[5:].strip()
            if not payload_str or payload_str == "[DONE]":
                continue
            try:
                event_payload = json.loads(payload_str)
            except json.JSONDecodeError:
                continue
            if not isinstance(event_payload, dict):
                continue

            event_type = event_payload.get("type")
            if not isinstance(event_type, str):
                event_type = ""

            delta = event_payload.get("delta")
            if event_type == "response.output_text.delta" and isinstance(delta, str) and delta:
                output_fragments.append(delta)

            item = event_payload.get("item")
            if event_type in {"response.output_item.added", "response.output_item.done"} and isinstance(item, dict):
                if str(item.get("type", "")) != "message":
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for entry in content:
                        if isinstance(entry, dict):
                            text = entry.get("text")
                            if isinstance(text, str) and text:
                                output_fragments.append(text)

            response_obj = event_payload.get("response")
            if event_type in {"response.completed", "response.done"} and isinstance(response_obj, dict):
                response_output_text = response_obj.get("output_text")
                if isinstance(response_output_text, str) and response_output_text.strip():
                    final_output_text = response_output_text.strip()

        assembled = final_output_text or "".join(output_fragments).strip()
        if assembled:
            return {"output_text": assembled}

        raise ValueError("openai streamed response parse failed")

    def _connection_api_key(self, connection: dict[str, object]) -> str | None:
        metadata = connection.get("metadata", {})
        if isinstance(metadata, dict):
            direct = metadata.get("api_key")
            if isinstance(direct, str) and direct.strip():
                return direct.strip()
            oauth = metadata.get("oauth")
            if isinstance(oauth, dict):
                access = oauth.get("access")
                if isinstance(access, str) and access.strip():
                    return access.strip()
        env_name = connection.get("api_key_env")
        if isinstance(env_name, str) and env_name.strip():
            value = os.getenv(env_name.strip())
            if value and value.strip():
                return value.strip()
        return None

    def _connection_oauth_connected(self, connection: dict[str, object]) -> bool:
        metadata = connection.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        oauth = metadata.get("oauth")
        if not isinstance(oauth, dict):
            return False
        access = oauth.get("access")
        if not isinstance(access, str) or access.strip() == "":
            return False
        expires_at = oauth.get("expires_at")
        if isinstance(expires_at, (int, float)) and time.time() >= float(expires_at):
            return False
        return True

    def _connection_ready(self, connection: dict[str, object]) -> bool:
        if not connection.get("enabled", False):
            return False
        metadata = connection.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        auth_method = metadata.get("auth_method")
        if isinstance(auth_method, str) and auth_method in {"chatgpt-browser", "chatgpt-headless"}:
            return self._connection_oauth_connected(connection)
        return True

    def _seed_defaults(
        self,
        local_model_enabled: bool,
        local_model_name: str,
        external_model_enabled: bool,
        external_model_name: str,
    ) -> None:
        existing = self.store.list_provider_connections()
        if existing:
            return
        self.store.upsert_provider_connection(
            connection_id="local-default",
            provider="local",
            model=local_model_name,
            base_url=None,
            api_key_env=None,
            enabled=local_model_enabled,
            metadata={"route_class": "fast_summary"},
        )
        self.store.upsert_provider_connection(
            connection_id="external-default",
            provider="external_api",
            model=external_model_name,
            base_url=None,
            api_key_env="OPENAI_API_KEY",
            enabled=external_model_enabled,
            metadata={"route_class": "deep_reasoning"},
        )

    def list_connections(self) -> list[dict[str, object]]:
        return [
            {
                "connection_id": item["connection_id"],
                "provider": item["provider"],
                "model": item["model"],
                "base_url": item["base_url"],
                "api_key_env": item["api_key_env"],
                "enabled": item["enabled"],
                "route_class": item["metadata"].get("route_class", "fast_summary"),
                "auth_method": item["metadata"].get("auth_method"),
                "display_name": item["metadata"].get("display_name"),
                "oauth_connected": self._connection_oauth_connected(item),
            }
            for item in self.store.list_provider_connections()
        ]

    def catalog(self) -> dict[str, object]:
        records = self.store.list_provider_connections()
        connected = sorted({item["provider"] for item in records if item["enabled"]})
        default_map: dict[str, str] = {}
        for provider in PROVIDER_CATALOG:
            models = provider.get("models", [])
            if models:
                default_map[str(provider["id"])] = str(models[0]["id"])
        return {
            "all": PROVIDER_CATALOG,
            "default": default_map,
            "connected": connected,
        }

    def auth_methods(self) -> dict[str, list[dict[str, object]]]:
        methods: dict[str, list[dict[str, object]]] = {}
        for provider in PROVIDER_CATALOG:
            provider_id = str(provider["id"])
            methods[provider_id] = []
            for method in provider.get("auth_methods", []):
                methods[provider_id].append(
                    {
                        "id": method["id"],
                        "type": method["type"],
                        "label": method["label"],
                        "description": method.get("description"),
                    }
                )
        return methods

    def oauth_authorize(self, provider_id: str, method_id: str, connection_id: str, redirect_uri: str) -> dict[str, object]:
        if provider_id != "openai":
            raise ValueError("OAuth authorize is only available for openai provider")
        if method_id not in {"chatgpt-browser", "chatgpt-headless"}:
            raise ValueError("unsupported oauth method")
        if self.store.get_provider_connection(connection_id) is None:
            raise ValueError("connection not found")

        loopback_ready = self._ensure_oauth_loopback_server(provider_id=provider_id, redirect_uri=redirect_uri)
        if not loopback_ready:
            raise ValueError("OAuth loopback callback server could not start. Check port availability and retry.")

        pkce_verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(pkce_verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")
        state = secrets.token_urlsafe(32)
        payload = {
            "provider_id": provider_id,
            "method_id": method_id,
            "connection_id": connection_id,
            "code_verifier": pkce_verifier,
            "redirect_uri": redirect_uri,
            "created_at": time.time(),
        }
        self._save_oauth_pending(state, payload)
        params = {
            "response_type": "code",
            "client_id": OPENAI_OAUTH_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email offline_access",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "id_token_add_organizations": "true",
            "codex_cli_simplified_flow": "true",
            "state": state,
            "originator": "opencode",
        }
        if method_id == "chatgpt-headless":
            params["prompt"] = "none"
        query = urllib.parse.urlencode(params)
        return {
            "url": f"{OPENAI_OAUTH_AUTHORIZE_URL}?{query}",
            "method": "code",
            "instructions": "Open the URL, authorize, then return to the app. The loopback callback will finalize the connection.",
        }

    def oauth_callback(
        self,
        provider_id: str,
        state: str | None,
        code: str | None,
        error: str | None,
        error_description: str | None,
    ) -> tuple[int, str]:
        if error:
            detail = error_description or error
            return 400, (
                "<html><body><h1>Authorization Failed</h1>"
                f"<p>{detail}</p></body></html>"
            )
        if not state:
            return 400, "<html><body><h1>Authorization Failed</h1><p>Missing state.</p></body></html>"
        pending = self._load_oauth_pending(state)
        if pending is None:
            return 400, "<html><body><h1>Authorization Failed</h1><p>Invalid state - potential CSRF attack.</p></body></html>"
        if str(pending["provider_id"]) != provider_id:
            self._clear_oauth_pending(state)
            return 400, "<html><body><h1>Authorization Failed</h1><p>Provider mismatch for state.</p></body></html>"
        if not code:
            self._clear_oauth_pending(state)
            return 400, "<html><body><h1>Authorization Failed</h1><p>Missing authorization code.</p></body></html>"

        token_url = OPENAI_OAUTH_TOKEN_URL
        payload = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": str(pending["redirect_uri"]),
                "client_id": OPENAI_OAUTH_CLIENT_ID,
                "code_verifier": str(pending["code_verifier"]),
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                body = response.read().decode("utf-8")
                token_payload = json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8")[:300]
            self._clear_oauth_pending(state)
            return 400, (
                "<html><body><h1>Authorization Failed</h1>"
                f"<p>Token exchange failed: HTTP {exc.code} {detail}</p></body></html>"
            )
        except Exception as exc:
            self._clear_oauth_pending(state)
            return 400, (
                "<html><body><h1>Authorization Failed</h1>"
                f"<p>Token exchange failed: {exc}</p></body></html>"
            )

        access_token = token_payload.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            self._clear_oauth_pending(state)
            return 400, (
                "<html><body><h1>Authorization Failed</h1>"
                "<p>Token exchange failed: access token missing from response.</p></body></html>"
            )
        refresh_token = token_payload.get("refresh_token")
        normalized_refresh = refresh_token.strip() if isinstance(refresh_token, str) and refresh_token.strip() else None

        connection_id = str(pending["connection_id"])
        connection = self.store.get_provider_connection(connection_id)
        if connection is None:
            self._clear_oauth_pending(state)
            return 400, "<html><body><h1>Authorization Failed</h1><p>Connection not found.</p></body></html>"
        metadata = connection.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        now = time.time()
        expires_in_raw = token_payload.get("expires_in")
        try:
            expires_in = float(expires_in_raw)
        except (TypeError, ValueError):
            expires_in = None
        expires_at = (now + expires_in) if isinstance(expires_in, (int, float)) else None
        metadata["oauth"] = {
            "type": "oauth",
            "access": access_token.strip(),
            "refresh": normalized_refresh,
            "expires_in": expires_in if expires_in is not None else expires_in_raw,
            "obtained_at": now,
            "expires_at": expires_at,
        }
        chatgpt_account_id = self._extract_account_id_from_token_payload(token_payload)
        if chatgpt_account_id is not None:
            metadata["chatgpt_account_id"] = chatgpt_account_id
        self.store.upsert_provider_connection(
            connection_id=connection_id,
            provider=connection["provider"],
            model=connection["model"],
            base_url=connection.get("base_url"),
            api_key_env=connection.get("api_key_env"),
            enabled=True,
            metadata=metadata,
        )
        self._clear_oauth_pending(state)
        return 200, (
            "<html><body><h1>Authorization Successful</h1>"
            "<p>You can close this window and return to SuzyBae runtime.</p></body></html>"
        )

    def validate_api_key(self, provider_id: str, api_key: str) -> dict[str, object]:
        provider_endpoints: dict[str, str] = {
            "openai": "https://api.openai.com/v1/models",
            "anthropic": "https://api.anthropic.com/v1/models",
            "cohere": "https://api.cohere.com/v2/models",
            "deepseek": "https://api.deepseek.com/models",
            "openrouter": "https://openrouter.ai/api/v1/models",
            "xai": "https://api.x.ai/v1/models",
            "groq": "https://api.groq.com/openai/v1/models",
            "mistral": "https://api.mistral.ai/v1/models",
            "together": "https://api.together.xyz/v1/models",
            "perplexity": "https://api.perplexity.ai/models",
        }
        if provider_id == "google":
            return {
                "ok": True,
                "provider": provider_id,
                "message": "Google key accepted (online validation skipped).",
            }
        url = provider_endpoints.get(provider_id)
        if not url:
            return {
                "ok": False,
                "provider": provider_id,
                "message": "Provider API key validation is not supported yet.",
            }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if provider_id == "anthropic":
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        request = urllib.request.Request(
            url,
            headers=headers,
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
                payload = json.loads(body) if body else {}
                count = 0
                if isinstance(payload, dict) and isinstance(payload.get("data"), list):
                    count = len(payload["data"])
                return {
                    "ok": True,
                    "provider": provider_id,
                    "message": f"API key validated ({count} models visible).",
                }
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8")[:200]
            return {
                "ok": False,
                "provider": provider_id,
                "message": f"Validation failed: HTTP {exc.code} {detail}",
            }
        except Exception as exc:
            return {
                "ok": False,
                "provider": provider_id,
                "message": f"Validation failed: {exc}",
            }

    def upsert_connection(
        self,
        connection_id: str,
        provider: str,
        model: str,
        enabled: bool,
        route_class: str,
        base_url: str | None,
        api_key_env: str | None,
        api_key: str | None,
        auth_method: str | None,
        display_name: str | None,
    ) -> dict[str, object]:
        existing = self.store.get_provider_connection(connection_id)
        existing_metadata = existing.get("metadata", {}) if isinstance(existing, dict) else {}
        if not isinstance(existing_metadata, dict):
            existing_metadata = {}

        metadata: dict[str, object] = {
            "route_class": route_class,
            "auth_method": auth_method,
            "display_name": display_name,
        }
        if api_key:
            metadata["api_key"] = api_key
        elif auth_method in {"chatgpt-browser", "chatgpt-headless"}:
            pass
        elif isinstance(existing_metadata.get("api_key"), str) and str(existing_metadata.get("api_key", "")).strip():
            metadata["api_key"] = str(existing_metadata["api_key"])

        existing_oauth = existing_metadata.get("oauth")
        if isinstance(existing_oauth, dict):
            metadata["oauth"] = existing_oauth

        self.store.upsert_provider_connection(
            connection_id=connection_id,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
            enabled=enabled,
            metadata=metadata,
        )
        connection = self.store.get_provider_connection(connection_id)
        if connection is None:
            raise ValueError("connection not found")
        return connection

    def bind_agent_connection(self, agent_id: str, connection_id: str) -> dict[str, object]:
        if self.store.get_provider_connection(connection_id) is None:
            raise ValueError("connection not found")
        self.store.bind_agent_provider_connection(agent_id, connection_id)
        binding = self.store.get_agent_provider_binding(agent_id)
        if binding is None:
            raise ValueError("binding not found")
        return binding

    def get_agent_binding(self, agent_id: str) -> dict[str, object] | None:
        return self.store.get_agent_provider_binding(agent_id)

    def status(self) -> dict[str, object]:
        connections = self.store.list_provider_connections()
        enabled = [item for item in connections if item["enabled"]]
        return {
            "providers": [
                {
                    "connection_id": item["connection_id"],
                    "provider": item["provider"],
                    "model": item["model"],
                    "route_class": item["metadata"].get("route_class", "fast_summary"),
                    "enabled": item["enabled"],
                }
                for item in connections
            ],
            "healthy": len(enabled) > 0,
            "enabled_count": len(enabled),
        }

    def models(self) -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        connected = {item["provider"] for item in self.store.list_provider_connections() if item["enabled"]}
        for provider in PROVIDER_CATALOG:
            provider_id = str(provider["id"])
            provider_name = str(provider["name"])
            for model in provider.get("models", []):
                entries.append(
                    {
                        "provider": provider_id,
                        "provider_name": provider_name,
                        "model": model["id"],
                        "model_name": model["name"],
                        "connected": provider_id in connected,
                    }
                )
        return entries

    def generate_chat_response(self, message: str, selected_model: dict[str, object], session_id: str | None = None) -> dict[str, object]:
        message = message.strip()
        if len(message) > 4000:
            message = message[:4000]
        connection_id = selected_model.get("connection_id")
        if not isinstance(connection_id, str) or not connection_id:
            raise ValueError("no active provider connection")
        connection = self.store.get_provider_connection(connection_id)
        if connection is None:
            raise ValueError("connection not found")
        if not connection.get("enabled", False):
            raise ValueError("connection is disabled")

        provider = str(connection.get("provider", ""))
        model = self._provider_model_name(provider, str(connection.get("model", "")))
        route_class = str(selected_model.get("route_class", "fast_summary"))
        api_key = self._connection_bearer_token(connection_id=connection_id, connection=connection)

        if provider == "local":
            raise ValueError("local provider chat runtime is not configured")
        if provider not in {"google", "local"} and (api_key is None or not api_key):
            raise ValueError("missing API key for provider connection")

        if provider == "google":
            if not api_key:
                raise ValueError("missing API key for provider connection")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}"
            payload = {
                "contents": [
                    {
                        "parts": [{"text": message}],
                    }
                ]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
            candidates = raw.get("candidates", []) if isinstance(raw, dict) else []
            text = ""
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                if parts and isinstance(parts[0], dict):
                    text = str(parts[0].get("text", ""))
            if not text.strip():
                raise ValueError("provider returned empty response")
            return {"answer": text.strip(), "backend": provider, "provider": provider, "model": model}

        if provider == "anthropic":
            payload = {
                "model": model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": message}],
            }
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "x-api-key": api_key or "",
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
            parts = raw.get("content", []) if isinstance(raw, dict) else []
            text = ""
            if parts and isinstance(parts[0], dict):
                text = str(parts[0].get("text", ""))
            if not text.strip():
                raise ValueError("provider returned empty response")
            return {"answer": text.strip(), "backend": provider, "provider": provider, "model": model}

        if provider == "cohere":
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
            }
            req = urllib.request.Request(
                "https://api.cohere.com/v2/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = json.loads(response.read().decode("utf-8"))
            message_obj = raw.get("message", {}) if isinstance(raw, dict) else {}
            content_list = message_obj.get("content", []) if isinstance(message_obj, dict) else []
            text = ""
            if content_list and isinstance(content_list[0], dict):
                text = str(content_list[0].get("text", ""))
            if not text.strip():
                raise ValueError("provider returned empty response")
            return {"answer": text.strip(), "backend": provider, "provider": provider, "model": model}

        if provider == "openai":
            max_output_tokens = 1200 if route_class == "deep_reasoning" else 500
            runtime_instructions = (
                "Provide a concise but thorough answer with clear actions and rationale."
                if route_class == "deep_reasoning"
                else "Answer briefly and directly."
            )
            use_chatgpt_backend = self._is_chatgpt_auth_connection(connection)
            if use_chatgpt_backend:
                chatgpt_supported_models = {"gpt-5.3-codex", "codex-mini-latest"}
                if route_class == "fast_summary":
                    model = "codex-mini-latest"
                elif model not in chatgpt_supported_models:
                    model = "gpt-5.3-codex"
            payload = {
                "model": model,
                "stream": False,
                "instructions": runtime_instructions,
                "input": [
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": message,
                            }
                        ],
                    }
                ],
            }
            openai_responses_url = "https://chatgpt.com/backend-api/codex/responses" if use_chatgpt_backend else "https://api.openai.com/v1/responses"
            if use_chatgpt_backend:
                payload["stream"] = True
                payload["store"] = False
            else:
                payload["max_output_tokens"] = max_output_tokens

            def _send_openai_request(token: str) -> dict[str, object]:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                if use_chatgpt_backend:
                    headers["originator"] = "opencode"
                    headers["OpenAI-Beta"] = "responses=experimental"
                    chatgpt_account_id = self._extract_chatgpt_account_id(token)
                    if chatgpt_account_id is None:
                        metadata = connection.get("metadata", {})
                        if isinstance(metadata, dict):
                            stored_account_id = metadata.get("chatgpt_account_id")
                            if isinstance(stored_account_id, str) and stored_account_id.strip():
                                chatgpt_account_id = stored_account_id.strip()
                    if chatgpt_account_id is not None:
                        headers["ChatGPT-Account-Id"] = chatgpt_account_id
                    if isinstance(session_id, str) and session_id.strip():
                        headers["session_id"] = session_id.strip()
                req = urllib.request.Request(
                    openai_responses_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    body = response.read().decode("utf-8")
                    return self._decode_openai_response_body(body) if body else {}

            try:
                raw = _send_openai_request(api_key)
            except urllib.error.HTTPError as exc:
                if exc.code == 401:
                    refreshed_token: str | None = None
                    metadata = connection.get("metadata", {})
                    oauth = metadata.get("oauth") if isinstance(metadata, dict) else None
                    if isinstance(oauth, dict):
                        with self._oauth_refresh_lock:
                            reloaded = self.store.get_provider_connection(connection_id)
                            if reloaded is not None:
                                re_meta = reloaded.get("metadata", {})
                                re_oauth = re_meta.get("oauth") if isinstance(re_meta, dict) else None
                                if isinstance(re_oauth, dict):
                                    refreshed = self._oauth_refresh(connection_id=connection_id, connection=reloaded, oauth=re_oauth)
                                    if isinstance(refreshed, dict):
                                        access = refreshed.get("access")
                                        if isinstance(access, str) and access.strip():
                                            refreshed_token = access.strip()
                    if refreshed_token:
                        raw = _send_openai_request(refreshed_token)
                    else:
                        detail = exc.read().decode("utf-8")[:240]
                        raise ValueError(f"openai unauthorized: {detail}") from exc
                else:
                    detail = exc.read().decode("utf-8")[:300]
                    raise ValueError(f"openai request failed: HTTP {exc.code} {detail}") from exc
            text = str(raw.get("output_text", "")) if isinstance(raw, dict) else ""
            if not text.strip():
                output = raw.get("output", []) if isinstance(raw, dict) else []
                if output and isinstance(output[0], dict):
                    content = output[0].get("content", [])
                    if isinstance(content, list) and content and isinstance(content[0], dict):
                        text = str(content[0].get("text", ""))
            if not text.strip():
                raise ValueError("provider returned empty response")
            return {"answer": text.strip(), "backend": provider, "provider": provider, "model": model}

        openai_compatible_endpoints: dict[str, str] = {
            "deepseek": "https://api.deepseek.com/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "xai": "https://api.x.ai/v1/chat/completions",
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "mistral": "https://api.mistral.ai/v1/chat/completions",
            "together": "https://api.together.xyz/v1/chat/completions",
            "perplexity": "https://api.perplexity.ai/chat/completions",
        }
        url = str(connection.get("base_url") or openai_compatible_endpoints.get(provider, ""))
        if not url:
            raise ValueError("provider chat runtime is not supported")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://localhost"
            headers["X-Title"] = "SuzyBae Runtime"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 1000 if route_class == "deep_reasoning" else 220,
        }
        if provider == "deepseek":
            if str(selected_model.get("route_class", "")) == "deep_reasoning" and model != "deepseek-reasoner":
                payload["thinking"] = {"type": "enabled"}
        else:
            payload["temperature"] = 0.2
        request_timeout = 90 if provider == "deepseek" else 30
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=request_timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
        choices = raw.get("choices", []) if isinstance(raw, dict) else []
        text = ""
        reasoning = ""
        if choices and isinstance(choices[0], dict):
            msg = choices[0].get("message", {})
            if isinstance(msg, dict):
                text = str(msg.get("content", ""))
                reasoning = str(msg.get("reasoning_content", ""))
        if not text.strip():
            raise ValueError("provider returned empty response")
        result = {"answer": text.strip(), "backend": provider, "provider": provider, "model": model}
        if reasoning.strip():
            result["reasoning"] = reasoning.strip()
        return result

    def route_model(self, route_class: str, agent_id: str = "suzybae", connection_id: str | None = None) -> dict[str, object]:
        records = self.store.list_provider_connections()
        selected_id = connection_id
        if selected_id is not None:
            selected = self.store.get_provider_connection(selected_id)
            if selected is None or not self._connection_ready(selected):
                return {
                    "provider": "none",
                    "model": "unavailable",
                    "route_class": route_class,
                }
            return {
                "connection_id": selected["connection_id"],
                "provider": selected["provider"],
                "model": selected["model"],
                "route_class": selected["metadata"].get("route_class", route_class),
            }

        if selected_id is None:
            binding = self.get_agent_binding(agent_id)
            if binding is not None:
                selected_id = binding["connection_id"]

        if selected_id is not None:
            selected = self.store.get_provider_connection(selected_id)
            if selected is not None and self._connection_ready(selected):
                return {
                    "connection_id": selected["connection_id"],
                    "provider": selected["provider"],
                    "model": selected["model"],
                    "route_class": selected["metadata"].get("route_class", route_class),
                }

        exact = next(
            (item for item in records if self._connection_ready(item) and item["metadata"].get("route_class", "fast_summary") == route_class),
            None,
        )
        if exact is not None:
            return {
                "connection_id": exact["connection_id"],
                "provider": exact["provider"],
                "model": exact["model"],
                "route_class": exact["metadata"].get("route_class", route_class),
            }
        fallback = next((item for item in records if self._connection_ready(item)), None)
        if fallback is None:
            return {
                "provider": "none",
                "model": "unavailable",
                "route_class": route_class,
            }
        return {
            "connection_id": fallback["connection_id"],
            "provider": fallback["provider"],
            "model": fallback["model"],
            "route_class": fallback["metadata"].get("route_class", "fast_summary"),
        }
