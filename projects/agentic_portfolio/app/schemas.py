from __future__ import annotations

from typing import Dict, Literal

from pydantic import BaseModel, Field

from app.domain.core_models import BrokerType, RiskProfile, TradeTicket
from app.domain.routing.models import RouteLane, RouteSource, WorkflowType


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    app_env: str
    started_at: str


class SettingsUpdateRequest(BaseModel):
    value: str


class SettingsResponse(BaseModel):
    config: Dict[str, str]
    persisted: Dict[str, str]
    meta: Dict[str, str]


class RouteRequestModel(BaseModel):
    message: str
    source: RouteSource = RouteSource.CHAT
    automation_enabled: bool = False
    include_internal_plan: bool = False


class RouteDecisionResponse(BaseModel):
    lane: RouteLane
    workflow: WorkflowType
    reason: str
    requires_dag: bool
    requires_market_refresh: bool
    requires_user_confirmation: bool
    internal_builder_plan: list[str] | None = None


class PositionInput(BaseModel):
    symbol: str
    asset: str = "stock"
    quantity: float
    avg_cost: float
    last_price: float


class PortfolioUpsertRequest(BaseModel):
    positions: list[PositionInput]
    cash: float


class StartupReportRequest(BaseModel):
    tracked_symbols: list[str]


class PortfolioBreakdownRequest(BaseModel):
    period: str = "7d"
    frequency: str = "daily"


class ConsultantBriefRequest(BaseModel):
    period: str = "7d"
    frequency: str = "daily"


class DailyCycleRequest(BaseModel):
    tracked_symbols: list[str]
    period: str = "7d"
    frequency: str = "daily"


class MonitorEnableRequest(BaseModel):
    tracked_symbols: list[str]
    interval_seconds: int = 60


class ResearchQueryRequest(BaseModel):
    query: str


class TradeLaneRequest(BaseModel):
    symbol: str
    profile: RiskProfile = RiskProfile.NEUTRAL


class ExecuteTicketRequest(BaseModel):
    ticket: TradeTicket
    confirm: bool = False
    broker: BrokerType = BrokerType.IBKR_PAPER


class ExecutionReconcileRequest(BaseModel):
    broker: BrokerType | None = None


class PluginInvokeRequest(BaseModel):
    plugin_id: str
    capability: str
    payload: Dict[str, object] = Field(default_factory=dict)
    run_id: str | None = None


class RuntimeSessionCreateRequest(BaseModel):
    title: str | None = None


class RuntimeSessionRenameRequest(BaseModel):
    title: str


class RuntimeSessionMessageRequest(BaseModel):
    message: str
    source: RouteSource = RouteSource.CHAT
    automation_enabled: bool = False
    include_internal_plan: bool = False
    agent_id: str = "suzybae"
    connection_id: str | None = None
    variant: str = "default"


class RuntimeChangeActionRequest(BaseModel):
    action: str
    snooze_minutes: int | None = None


class RuntimeSuzyActivateRequest(BaseModel):
    command: str


class RuntimeSuzySelfEditRequest(BaseModel):
    file_path: str
    find_text: str
    replace_text: str


class RuntimeProviderOauthAuthorizeRequest(BaseModel):
    method_id: str
    connection_id: str


class RuntimeProviderApiValidateRequest(BaseModel):
    provider_id: str
    api_key: str


class ProviderConnectionRequest(BaseModel):
    connection_id: str
    provider: str
    model: str
    route_class: str = "fast_summary"
    enabled: bool = True
    base_url: str | None = None
    api_key_env: str | None = None
    api_key: str | None = None
    auth_method: str | None = None
    display_name: str | None = None


class AgentConnectionBindingRequest(BaseModel):
    connection_id: str


class ProviderProfileUpsertRequest(BaseModel):
    provider_profile_id: str
    provider_id: str
    display_name: str
    auth_type: str
    base_url: str | None = None
    options: Dict[str, object] = Field(default_factory=dict)
    status: str = "disconnected"
    last_health_at: str | None = None


class ModelProfileUpsertRequest(BaseModel):
    model_profile_id: str
    provider_profile_id: str
    model_id: str
    display_name: str
    capabilities: Dict[str, object] = Field(default_factory=dict)
    default_temperature: float | None = None
    max_output_tokens: int | None = None
    enabled: bool = True


class AuthStartRequest(BaseModel):
    provider_id: str
    auth_method: str
    session_id: str


class AuthCompleteRequest(BaseModel):
    provider_id: str
    auth_method: str
    session_id: str
    state: str | None = None
    code: str | None = None
    api_key: str | None = None
    token: str | None = None
    base_url: str | None = None


class AuthLogoutRequest(BaseModel):
    provider_id: str
    session_id: str


class SessionBindRequest(BaseModel):
    session_id: str
    provider_id: str
    auth_method: str
    model_id: str
    base_url: str | None = None


class SessionUnbindRequest(BaseModel):
    session_id: str


class SessionResetRequest(BaseModel):
    session_id: str


class EngineHealthRequest(BaseModel):
    provider_id: str
    base_url: str | None = None


class JobUpsertRequest(BaseModel):
    job_id: str
    job_type: str
    name: str
    schedule_cron: str | None = None
    enabled: bool = True
    config: Dict[str, object] = Field(default_factory=dict)


class NewsFeedRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    sources: list[str] | None = None
    categories: list[str] | None = None
    classes: list[str] | None = None
    limit: int = 20
    focus_mode: Literal["general", "focused"] = "general"


class NewsCachePurgeRequest(BaseModel):
    pass


class WorldMonitorFeedRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    limit: int = 20
    focus_mode: Literal["general", "focused"] = "general"


class FlatRouterUpdateSettingsRequest(BaseModel):
    engine: str | None = None
    routing_mode: str | None = None
    default_agent: str | None = None
    skills_profile: str | None = None
    enabled_gateways: list[str] | None = None


class FlatRouterRouteRequest(BaseModel):
    message: str
    preferred_agent: str | None = None


class OpenDataDatasetsRequest(BaseModel):
    query: str | None = None
    limit: int = 20


class OpenDataOverviewRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    limit: int = 20


class OpenDataSeriesRequest(BaseModel):
    symbol: str
    dataset_id: str = "equity_price_history"
    interval: str = "1d"
    limit: int = 120


class OpenStockSearchRequest(BaseModel):
    query: str
    limit: int = 10


class OpenStockSnapshotRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    limit: int = 20


class OpenStockCatalogRequest(BaseModel):
    query: str | None = None
    exchange: str | None = None
    stock_type: str | None = None
    limit: int = 50
    offset: int = 0


class OpenStockReferenceRequest(BaseModel):
    symbol: str


class FinnhubLookupRequest(BaseModel):
    query: str
    exchange: str | None = None


class FinnhubStockSymbolsRequest(BaseModel):
    exchange: str = "US"
    mic: str | None = None
    security_type: str | None = None
    currency: str | None = None


class FinnhubSymbolRequest(BaseModel):
    symbol: str


class FinnhubCompanyNewsRequest(BaseModel):
    symbol: str
    from_date: str | None = None
    to_date: str | None = None


class FinnhubCandlesRequest(BaseModel):
    symbol: str
    resolution: str = "D"
    from_ts: int
    to_ts: int


class GatewayTestMessageRequest(BaseModel):
    text: str = "Agentic Portfolio gateway test"


class MarketQuotesRequest(BaseModel):
    instruments: list[str] = Field(default_factory=list)
    focus_mode: Literal["general", "focused"] = "general"


class MarketCandlesRequest(BaseModel):
    instrument_id: str
    interval: str = "5m"
    range: str = "1d"


class IbkrHistoryRequest(BaseModel):
    conid: str
    period: str = "1w"
    bar: str = "1d"


class RuntimeOrchestrateRequest(BaseModel):
    message: str
    route_hint: str = "research"
    preferred_connection_id: str | None = None
    limit: int = 20
