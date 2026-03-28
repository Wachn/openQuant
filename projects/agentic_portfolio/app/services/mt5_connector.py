from __future__ import annotations

from typing import Dict


class MT5Connector:
    def __init__(
        self,
        enabled: bool,
        terminal_path: str | None,
        login: int | None,
        password: str | None,
        server: str | None,
        timeout_ms: int,
    ) -> None:
        self.enabled = enabled
        self.terminal_path = terminal_path
        self.login = login
        self.password = password
        self.server = server
        self.timeout_ms = timeout_ms

        self._mt5_module = None
        self._import_error: str | None = None
        if self.enabled:
            try:
                import MetaTrader5 as mt5  # type: ignore

                self._mt5_module = mt5
            except Exception as exc:
                self._import_error = str(exc)

    def health(self) -> Dict[str, object]:
        if not self.enabled:
            return {"enabled": False, "status": "disabled"}
        if self._mt5_module is None:
            return {
                "enabled": True,
                "status": "unavailable",
                "reason": "MetaTrader5 package unavailable",
                "error": self._import_error,
            }
        if self.login is None:
            return {
                "enabled": True,
                "status": "not_configured",
                "reason": "mt5_login not set",
            }

        mt5 = self._mt5_module
        kwargs: Dict[str, object] = {"timeout": self.timeout_ms}
        if self.terminal_path:
            kwargs["path"] = self.terminal_path

        initialized = False
        try:
            initialized = bool(mt5.initialize(**kwargs))
            if not initialized:
                return {
                    "enabled": True,
                    "status": "error",
                    "stage": "initialize",
                    "last_error": mt5.last_error(),
                }
            logged_in = mt5.login(self.login, password=self.password or "", server=self.server or "")
            if not logged_in:
                return {
                    "enabled": True,
                    "status": "error",
                    "stage": "login",
                    "last_error": mt5.last_error(),
                }
            account = mt5.account_info()
            terminal = mt5.terminal_info()
            return {
                "enabled": True,
                "status": "connected",
                "account_login": getattr(account, "login", None),
                "server": getattr(account, "server", None),
                "terminal_connected": getattr(terminal, "connected", None),
            }
        except Exception as exc:
            return {
                "enabled": True,
                "status": "error",
                "stage": "runtime",
                "error": str(exc),
            }
        finally:
            if initialized:
                try:
                    mt5.shutdown()
                except Exception:
                    pass
