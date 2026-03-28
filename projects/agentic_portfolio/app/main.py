from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_config
from app.domain.routing.dynamic_router import DynamicAgentRouter
from app.services.mt5_connector import MT5Connector
from app.services.auth.oauth_pkce import OAuthPkceService
from app.services.engine_service import EngineService
from app.services.auth_service import AuthService
from app.services.capability_service import CapabilityService
from app.services.channel_gateway_service import ChannelGatewayService
from app.services.connector_routing_service import ConnectorRoutingService
from app.services.dashboard_service import DashboardService
from app.services.diagnostics_service import DiagnosticsService
from app.services.finding_query_service import FindingQueryService
from app.services.ibkr_cpapi_market_service import IbkrCpapiMarketService
from app.services.instrument_query_service import InstrumentQueryService
from app.services.jobs.scheduler import Scheduler
from app.services.model_service import ModelService
from app.services.market.market_data_service import MarketDataServiceV21
from app.services.open_data_service import OpenDataService
from app.services.openclaw_runtime import OpenClawRuntimeHost
from app.services.open_stock_service import OpenStockService
from app.services.order_query_service import OrderQueryService
from app.services.portfolio.portfolio_service import PortfolioServiceV21
from app.services.portfolio_query_service import PortfolioQueryService
from app.services.platform_service import PlatformService
from app.services.flat_routing_agent_service import FlatRoutingAgentService
from app.services.provider_gateway import ProviderGateway
from app.services.provider_registry import ProviderRegistryService
from app.services.route_trace_service import RouteTraceService
from app.services.report_query_service import ReportQueryService
from app.services.reports.report_service import ReportServiceV21
from app.services.runtime_orchestrator_service import RuntimeOrchestratorService
from app.services.runtime_status_service import RuntimeStatusService
from app.services.secret_storage_service import SecretStorageService
from app.services.session_binding_service import SessionBindingService
from app.services.memory_summary_service import MemorySummaryService
from app.services.watchlist_query_service import WatchlistQueryService
from app.services.runtime_agent_registry import RuntimeAgentRegistry
from app.services.runtime_workspace_service import RuntimeWorkspaceService
from app.services.world_monitor_service import WorldMonitorService
from app.storage.duckdb_store import DuckDbStore
from app.storage.sqlite_store import SQLiteStore
from app.storage.v21_store import V21Store


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = get_config()
    store = SQLiteStore(config.sqlite_path)
    store.initialize()
    v21_store = V21Store(config.sqlite_path)
    v21_store.initialize()
    duckdb_store = DuckDbStore(config.duckdb_path)
    duckdb_store.initialize()

    app.state.config = config
    app.state.store = store
    app.state.v21_store = v21_store
    app.state.duckdb_store = duckdb_store
    app.state.dynamic_router = DynamicAgentRouter()
    app.state.platform_service = PlatformService(
        store=store,
        rag_workspace=config.rag_workspace_dir,
        enable_quant_rag=config.enable_quant_rag,
        ibkr_cpapi_market=IbkrCpapiMarketService(
            base_url=config.ibkr_cpapi_base_url,
            websocket_url=config.ibkr_cpapi_websocket_url,
            verify_tls=config.ibkr_cpapi_verify_tls,
            timeout_seconds=config.ibkr_cpapi_timeout_seconds,
            enabled=config.ibkr_cpapi_enabled,
        ),
    )
    app.state.runtime_agent_registry = RuntimeAgentRegistry(config.runtime_agents_dir)
    app.state.world_monitor_service = WorldMonitorService()
    app.state.open_data_service = OpenDataService()
    app.state.open_stock_service = OpenStockService()
    app.state.provider_gateway = ProviderGateway(
        store=store,
        local_model_enabled=config.local_model_enabled,
        local_model_name=config.local_model_name,
        external_model_enabled=config.external_model_enabled,
        external_model_name=config.external_model_name,
    )
    app.state.provider_registry = ProviderRegistryService(provider_gateway=app.state.provider_gateway)
    app.state.channel_gateway_service = ChannelGatewayService(store=store, config=config)
    app.state.flat_routing_agent_service = FlatRoutingAgentService(
        store=store,
        runtime_agent_registry=app.state.runtime_agent_registry,
        provider_gateway=app.state.provider_gateway,
        channel_gateway_service=app.state.channel_gateway_service,
    )
    app.state.secret_storage_service = SecretStorageService()
    app.state.oauth_pkce = OAuthPkceService(loopback_port=config.oauth_loopback_port)
    app.state.model_service = ModelService(provider_gateway=app.state.provider_gateway)
    app.state.auth_service = AuthService(
        oauth_pkce=app.state.oauth_pkce,
        secret_storage=app.state.secret_storage_service,
        provider_registry=app.state.provider_registry,
    )
    app.state.session_binding_service = SessionBindingService()
    app.state.engine_service = EngineService()
    app.state.portfolio_service_v21 = PortfolioServiceV21(platform_service=app.state.platform_service)
    app.state.market_data_service_v21 = MarketDataServiceV21(platform_service=app.state.platform_service)
    app.state.report_service_v21 = ReportServiceV21(v21_store=v21_store, platform_service=app.state.platform_service)
    app.state.capability_service = CapabilityService()
    app.state.dashboard_service = DashboardService(platform_service=app.state.platform_service, v21_store=v21_store)
    app.state.portfolio_query_service = PortfolioQueryService(portfolio_service_v21=app.state.portfolio_service_v21)
    app.state.watchlist_query_service = WatchlistQueryService()
    app.state.instrument_query_service = InstrumentQueryService(
        market_data_service_v21=app.state.market_data_service_v21,
        portfolio_service_v21=app.state.portfolio_service_v21,
    )
    app.state.report_query_service = ReportQueryService(v21_store=v21_store, report_service_v21=app.state.report_service_v21)
    app.state.finding_query_service = FindingQueryService(v21_store=v21_store)
    app.state.order_query_service = OrderQueryService(platform_service=app.state.platform_service)
    app.state.diagnostics_service = DiagnosticsService()
    app.state.runtime_status_service = RuntimeStatusService()
    app.state.route_trace_service = RouteTraceService(store=store)
    app.state.memory_summary_service = MemorySummaryService(store=store)
    app.state.connector_routing_service = ConnectorRoutingService(provider_gateway=app.state.provider_gateway)
    app.state.runtime_orchestrator = RuntimeOrchestratorService(
        route_trace_service=app.state.route_trace_service,
        memory_summary_service=app.state.memory_summary_service,
        connector_routing_service=app.state.connector_routing_service,
        enabled=config.enable_runtime_v23_scaffold,
    )
    app.state.scheduler = Scheduler(enabled=config.enable_scheduler)
    app.state.runtime_workspace = RuntimeWorkspaceService(
        store=store,
        platform=app.state.platform_service,
        provider_gateway=app.state.provider_gateway,
        suzy_activation_phrase=config.suzy_activation_phrase,
        suzy_edit_root=config.suzy_edit_root,
    )
    app.state.openclaw_runtime = OpenClawRuntimeHost(
        plugins_dir=config.plugins_dir,
        enabled=config.enable_openclaw_plugins,
        timeout_seconds=config.openclaw_timeout_seconds,
    )
    app.state.openclaw_runtime.reload()
    app.state.mt5_connector = MT5Connector(
        enabled=config.enable_mt5_connector,
        terminal_path=config.mt5_terminal_path,
        login=config.mt5_login,
        password=config.mt5_password,
        server=config.mt5_server,
        timeout_ms=config.mt5_timeout_ms,
    )
    app.state.started_at = utc_now_iso()
    await app.state.scheduler.start_if_enabled()
    try:
        yield
    finally:
        app.state.platform_service.disable_monitor()
        await app.state.scheduler.stop()


app = FastAPI(title="Agentic Portfolio Backend", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Agentic Portfolio Backend Phase 1 is running",
        "docs": "/docs",
        "health": "/health",
    }
