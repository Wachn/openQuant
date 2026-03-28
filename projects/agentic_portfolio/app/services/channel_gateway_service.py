from __future__ import annotations

import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from app.config import AppConfig
from app.storage.sqlite_store import SQLiteStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChannelGatewayService:
    def __init__(self, store: SQLiteStore, config: AppConfig) -> None:
        self.store = store
        self.config = config

    def _setting(self, key: str, fallback: str | None = None) -> str | None:
        value = self.store.get_settings().get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(fallback, str) and fallback.strip():
            return fallback.strip()
        return None

    def _telegram_token(self) -> str | None:
        return self._setting("gateway.telegram.bot_token", self.config.telegram_bot_token)

    def _telegram_chat_id(self) -> str | None:
        return self._setting("gateway.telegram.chat_id", self.config.telegram_chat_id)

    def _telegram_webhook_secret(self) -> str | None:
        return self._setting("gateway.telegram.webhook_secret", self.config.telegram_webhook_secret)

    def _whatsapp_verify_token(self) -> str | None:
        return self._setting("gateway.whatsapp.verify_token", self.config.whatsapp_verify_token)

    def _whatsapp_access_token(self) -> str | None:
        return self._setting("gateway.whatsapp.access_token", self.config.whatsapp_access_token)

    def _whatsapp_phone_number_id(self) -> str | None:
        return self._setting("gateway.whatsapp.phone_number_id", self.config.whatsapp_phone_number_id)

    def _whatsapp_app_secret(self) -> str | None:
        return self._setting("gateway.whatsapp.app_secret", self.config.whatsapp_app_secret)

    def _whatsapp_test_recipient(self) -> str | None:
        return self._setting("gateway.whatsapp.test_recipient", self.config.whatsapp_test_recipient)

    def _public_base_url(self) -> str | None:
        return self._setting("gateway.public_base_url", self.config.public_base_url)

    def _telegram_api_request(self, method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, Any]:
        token = self._telegram_token()
        if not token:
            raise ValueError("Telegram bot token is not configured")
        url = f"https://api.telegram.org/bot{token}/{path.lstrip('/')}"
        body = None
        headers = {"User-Agent": "agentic-portfolio/0.1"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=body, method=method.upper(), headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
        if not raw.strip():
            return {}
        decoded = json.loads(raw)
        if isinstance(decoded, dict):
            return decoded
        return {"data": decoded}

    def _whatsapp_api_request(self, method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, Any]:
        access_token = self._whatsapp_access_token()
        if not access_token:
            raise ValueError("WhatsApp access token is not configured")
        base_url = "https://graph.facebook.com/v23.0"
        url = f"{base_url}/{path.lstrip('/')}"
        body = None
        headers = {
            "User-Agent": "agentic-portfolio/0.1",
            "Authorization": f"Bearer {access_token}",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=body, method=method.upper(), headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
        if not raw.strip():
            return {}
        decoded = json.loads(raw)
        if isinstance(decoded, dict):
            return decoded
        return {"data": decoded}

    def channels_status(self) -> dict[str, object]:
        public_base_url = self._public_base_url()
        telegram_missing: list[str] = []
        if not self._telegram_token():
            telegram_missing.append("telegram_bot_token")
        if not self._telegram_chat_id():
            telegram_missing.append("telegram_chat_id")

        telegram_status = "ready"
        telegram_message = "Telegram gateway configured."
        telegram_meta: dict[str, object] = {}
        if telegram_missing:
            telegram_status = "missing_config"
            telegram_message = f"Missing: {', '.join(telegram_missing)}"
        else:
            try:
                response = self._telegram_api_request("GET", "getMe")
                telegram_meta["bot"] = response.get("result", {}) if isinstance(response, dict) else {}
            except Exception as exc:
                telegram_status = "degraded"
                telegram_message = f"{type(exc).__name__}:{exc}"

        whatsapp_missing: list[str] = []
        if not self._whatsapp_access_token():
            whatsapp_missing.append("whatsapp_access_token")
        if not self._whatsapp_phone_number_id():
            whatsapp_missing.append("whatsapp_phone_number_id")
        if not self._whatsapp_verify_token():
            whatsapp_missing.append("whatsapp_verify_token")
        if not self._whatsapp_app_secret():
            whatsapp_missing.append("whatsapp_app_secret")
        if not self._whatsapp_test_recipient():
            whatsapp_missing.append("whatsapp_test_recipient")
        if not public_base_url:
            whatsapp_missing.append("public_base_url")

        whatsapp_status = "ready" if not whatsapp_missing else "missing_config"
        whatsapp_message = "WhatsApp Cloud API gateway configured." if not whatsapp_missing else f"Missing: {', '.join(whatsapp_missing)}"

        channels = [
            {
                "channel": "telegram",
                "label": "Telegram Bot API",
                "status": telegram_status,
                "message": telegram_message,
                "mode": "bot_api",
                "webhook_url": f"{public_base_url.rstrip('/')}/gateway/telegram/webhook" if public_base_url else None,
                "next_action": "set_gateway_credentials" if telegram_missing else "send_test_message",
                "hint": "Create a Telegram bot with @BotFather, then configure bot token and chat id."
                if telegram_missing
                else "Telegram gateway is ready for webhook and outbound test messages.",
                "meta": telegram_meta,
            },
            {
                "channel": "whatsapp",
                "label": "WhatsApp Cloud API",
                "status": whatsapp_status,
                "message": whatsapp_message,
                "mode": "cloud_api",
                "webhook_url": f"{public_base_url.rstrip('/')}/gateway/whatsapp/webhook" if public_base_url else None,
                "next_action": "set_gateway_credentials" if whatsapp_missing else "verify_webhook_and_send_test",
                "hint": "WhatsApp requires Meta app credentials, verify token, app secret, phone number id, recipient, and a public HTTPS webhook."
                if whatsapp_missing
                else "WhatsApp gateway is ready for webhook verification and outbound test messages.",
                "meta": {},
            },
        ]
        return {
            "channels": channels,
            "updated_at": _utc_now_iso(),
        }

    def send_telegram_test(self, text: str) -> dict[str, object]:
        chat_id = self._telegram_chat_id()
        if not chat_id:
            raise ValueError("Telegram chat id is not configured")
        payload = self._telegram_api_request(
            "POST",
            "sendMessage",
            payload={"chat_id": chat_id, "text": text},
        )
        return {
            "channel": "telegram",
            "status": "sent",
            "response": payload,
            "updated_at": _utc_now_iso(),
        }

    def send_whatsapp_test(self, text: str) -> dict[str, object]:
        phone_number_id = self._whatsapp_phone_number_id()
        recipient = self._whatsapp_test_recipient()
        if not phone_number_id:
            raise ValueError("WhatsApp phone number id is not configured")
        if not recipient:
            raise ValueError("WhatsApp test recipient is not configured")
        payload = self._whatsapp_api_request(
            "POST",
            f"{phone_number_id}/messages",
            payload={
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            },
        )
        return {
            "channel": "whatsapp",
            "status": "sent",
            "response": payload,
            "updated_at": _utc_now_iso(),
        }

    def verify_whatsapp_webhook(self, mode: str | None, challenge: str | None, verify_token: str | None) -> str:
        expected = self._whatsapp_verify_token()
        if mode == "subscribe" and challenge and expected and verify_token == expected:
            return challenge
        raise ValueError("invalid webhook verification request")

    def accept_telegram_webhook(self, payload: dict[str, object], secret_token: str | None) -> dict[str, object]:
        expected = self._telegram_webhook_secret()
        if expected and secret_token != expected:
            raise ValueError("invalid telegram webhook secret")
        return {
            "channel": "telegram",
            "accepted": True,
            "has_message": isinstance(payload.get("message"), dict),
            "updated_at": _utc_now_iso(),
        }

    def accept_whatsapp_webhook(self, raw_body: bytes, signature_header: str | None, payload: dict[str, object]) -> dict[str, object]:
        app_secret = self._whatsapp_app_secret()
        if app_secret:
            digest = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
            expected = f"sha256={digest}"
            if signature_header != expected:
                raise ValueError("invalid whatsapp webhook signature")
        return {
            "channel": "whatsapp",
            "accepted": True,
            "entry_count": len(payload.get("entry", [])) if isinstance(payload.get("entry"), list) else 0,
            "updated_at": _utc_now_iso(),
        }
