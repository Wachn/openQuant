from __future__ import annotations

import json
import ssl
import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IbkrCpapiMarketService:
    def __init__(
        self,
        base_url: str,
        websocket_url: str,
        verify_tls: bool = False,
        timeout_seconds: float = 8.0,
        enabled: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.websocket_url = websocket_url
        self.verify_tls = verify_tls
        self.timeout_seconds = timeout_seconds
        self.enabled = enabled
        self._conid_by_symbol: dict[str, str] = {}
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = self._build_opener()

    def _build_opener(self) -> urllib.request.OpenerDirector:
        handlers: list[urllib.request.BaseHandler] = [urllib.request.HTTPCookieProcessor(self._cookie_jar)]
        if self.verify_tls:
            handlers.append(urllib.request.HTTPSHandler())
        else:
            handlers.append(urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
        return urllib.request.build_opener(*handlers)

    def _ssl_context(self) -> ssl.SSLContext | None:
        if self.verify_tls:
            return None
        return ssl._create_unverified_context()

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        body = None
        headers = {"User-Agent": "agentic-portfolio/0.1"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, method=method.upper(), headers=headers)
        with self._opener.open(req, timeout=self.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
        if not raw.strip():
            return {}
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        return {"data": data}

    def gateway_session_status(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "authenticated": False,
                "connected": False,
                "status": "disabled",
                "message": "IBKR CPAPI disabled by config",
                "next_action": "enable_cpapi",
                "hint": "Enable AGENTIC_PORTFOLIO_IBKR_CPAPI_ENABLED and restart backend.",
                "login_url": self.login_url,
                "websocket_url": self.websocket_url,
                "updated_at": _utc_now_iso(),
            }

        try:
            payload = self._request("GET", "/iserver/auth/status")
            authenticated = bool(payload.get("authenticated", False))
            connected = bool(payload.get("connected", False))
            status = "ready" if authenticated and connected else "login_required"
            message = str(payload.get("message") or "")
            next_action = "none" if status == "ready" else "login_gateway"
            hint = (
                "Open gateway login page and complete IBKR authentication."
                if status != "ready"
                else "Gateway authenticated and connected."
            )
            return {
                "enabled": True,
                "authenticated": authenticated,
                "connected": connected,
                "competing": bool(payload.get("competing", False)),
                "status": status,
                "message": message,
                "next_action": next_action,
                "hint": hint,
                "login_url": self.login_url,
                "websocket_url": self.websocket_url,
                "updated_at": _utc_now_iso(),
            }
        except Exception as exc:
            return {
                "enabled": True,
                "authenticated": False,
                "connected": False,
                "status": "gateway_unreachable",
                "message": f"{type(exc).__name__}:{exc}",
                "next_action": "start_gateway",
                "hint": "Start IBKR Client Portal Gateway, log in via browser, then click Sync IBKR Login.",
                "login_url": self.login_url,
                "websocket_url": self.websocket_url,
                "updated_at": _utc_now_iso(),
            }

    def init_brokerage_session(self) -> dict[str, Any]:
        if not self.enabled:
            return self.gateway_session_status()
        try:
            _ = self._request("POST", "/iserver/auth/ssodh/init")
        except Exception:
            pass
        return self.gateway_session_status()

    def tickle(self) -> dict[str, Any]:
        if not self.enabled:
            return self.gateway_session_status()
        tickle_payload: dict[str, Any] = {}
        try:
            tickle_payload = self._request("GET", "/tickle")
        except Exception as exc:
            tickle_payload = {"status": "error", "message": f"{type(exc).__name__}:{exc}"}
        status = self.gateway_session_status()
        status["tickle"] = tickle_payload
        return status

    @property
    def login_url(self) -> str:
        if "/v1/api" in self.base_url:
            return self.base_url.split("/v1/api", maxsplit=1)[0]
        return self.base_url

    def resolve_conid(self, symbol: str) -> str | None:
        normalized = symbol.strip().upper()
        if not normalized:
            return None
        cached = self._conid_by_symbol.get(normalized)
        if cached:
            return cached
        if not self.enabled:
            return None
        try:
            payload = self._request("GET", "/iserver/secdef/search", params={"symbol": normalized})
        except Exception:
            return None
        entries = payload.get("data") if isinstance(payload.get("data"), list) else payload
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                conid = entry.get("conid")
                if isinstance(conid, (int, str)):
                    resolved = str(conid)
                    self._conid_by_symbol[normalized] = resolved
                    return resolved
        return None

    def market_snapshot(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        if not self.enabled:
            return {}
        conid_by_symbol: dict[str, str] = {}
        for symbol in symbols:
            conid = self.resolve_conid(symbol)
            if conid:
                conid_by_symbol[symbol.upper()] = conid
        if not conid_by_symbol:
            return {}
        conids = ",".join(conid_by_symbol.values())
        try:
            payload = self._request("GET", "/iserver/marketdata/snapshot", params={"conids": conids, "fields": "31,84,85"})
        except Exception:
            return {}
        rows = payload.get("data") if isinstance(payload.get("data"), list) else payload
        if not isinstance(rows, list):
            return {}
        conid_to_symbol = {value: key for key, value in conid_by_symbol.items()}
        by_symbol: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_conid = row.get("conid")
            if isinstance(row_conid, (int, str)):
                symbol = conid_to_symbol.get(str(row_conid))
                if symbol:
                    by_symbol[symbol] = row
        return by_symbol

    def history(self, conid: str, period: str = "1w", bar: str = "1d") -> dict[str, Any]:
        if not self.enabled:
            return {
                "status": "disabled",
                "conid": conid,
                "period": period,
                "bar": bar,
                "data": [],
            }
        params = {"conid": str(conid), "period": period, "bar": bar}
        try:
            return self._request("GET", "/hmds/history", params=params)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                try:
                    return self._request("GET", "/hmds/history", params=params)
                except Exception as retry_exc:
                    return {
                        "status": "error",
                        "conid": str(conid),
                        "period": period,
                        "bar": bar,
                        "message": f"{type(retry_exc).__name__}:{retry_exc}",
                    }
            return {
                "status": "error",
                "conid": str(conid),
                "period": period,
                "bar": bar,
                "message": f"HTTPError:{exc.code}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "conid": str(conid),
                "period": period,
                "bar": bar,
                "message": f"{type(exc).__name__}:{exc}",
            }
