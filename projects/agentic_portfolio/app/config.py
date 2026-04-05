from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTIC_PORTFOLIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Agentic Portfolio Backend"
    app_env: str = Field(default="dev")
    app_version: str = "0.2.0"
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = Path("workspace")
    rag_workspace_dir: Path = Path("workspace/quant_rag")
    enable_quant_rag: bool = True
    plugins_dir: Path = Path("plugins")
    runtime_agents_dir: Path = Path("../../runtime_agents")
    enable_openclaw_plugins: bool = True
    openclaw_timeout_seconds: float = 3.0
    local_model_enabled: bool = True
    local_model_name: str = "local/default"
    external_model_enabled: bool = True
    external_model_name: str = "openai/gpt-4o-mini"
    suzy_activation_phrase: str = "/activateSuzy"
    suzy_edit_root: Path = Path("..")
    enable_mt5_connector: bool = False
    mt5_terminal_path: str | None = None
    mt5_login: int | None = None
    mt5_password: str | None = None
    mt5_server: str | None = None
    mt5_timeout_ms: int = 60000
    enable_scheduler: bool = True
    enable_runtime_v23_scaffold: bool = True
    oauth_loopback_port: int = 1455
    broker_paper_only: bool = True
    public_base_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_webhook_secret: str | None = None
    whatsapp_verify_token: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_app_secret: str | None = None
    whatsapp_test_recipient: str | None = None
    finnhub_api_key: str | None = None
    finnhub_base_url: str = "https://finnhub.io/api/v1"
    finnhub_webhook_secret: str | None = None
    finnhub_webhook_path: str = "/finnhub/webhook"
    finnhub_public_webhook_base_url: str | None = None
    finnhub_ngrok_url: str | None = None
    ibkr_cpapi_enabled: bool = True
    ibkr_cpapi_base_url: str = "https://localhost:5000/v1/api"
    ibkr_cpapi_websocket_url: str = "wss://localhost:5000/v1/api/ws"
    ibkr_cpapi_verify_tls: bool = False
    ibkr_cpapi_timeout_seconds: float = 8.0

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "agentic_portfolio.db"

    @property
    def duckdb_path(self) -> Path:
        return self.data_dir / "agentic_portfolio.duckdb"


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig()
