import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AuthModal } from "./components/Connection/AuthModal";
import { ConnectionStatus } from "./components/Connection/ConnectionStatus";
import { ModelPicker, type ProviderModel } from "./components/Connection/ModelPicker";
import { ProviderPicker, type ProviderOption } from "./components/Connection/ProviderPicker";
import { ResetConnectionButton } from "./components/Connection/ResetConnectionButton";
import { TradingViewEmbed } from "./components/TradingViewEmbed";
import { useCapabilities } from "./hooks/useCapabilities";
import { useRuntimeStatus } from "./hooks/useRuntimeStatus";
import { type ConnectionState, idleConnectionSnapshot } from "./store/connectionStore";

type RiskProfile = "aggressive" | "neutral" | "conservative";
type BrokerType = "ibkr_paper" | "mt5_paper";
type PortfolioAccountScope = "overall" | "ibkr" | "mt5";

type JsonObject = Record<string, unknown>;

interface PositionInput {
  symbol: string;
  asset: string;
  quantity: number;
  avg_cost: number;
  last_price: number;
}

interface PortfolioSnapshot {
  equity: number;
  cash: number;
  daily_pnl: number;
  drawdown: number;
  risk_profile: RiskProfile;
  positions: PositionInput[];
}

interface StartupSuggestion {
  suggestion_id: string;
  title: string;
  impact_score: number;
  confidence: number;
  status: string;
}

interface MarketChange {
  symbol: string;
  change_pct: number;
}

interface StartupReport {
  as_of_ts: string;
  portfolio_snapshot: PortfolioSnapshot;
  suggestions: StartupSuggestion[];
  market_changes: MarketChange[];
}

interface TradeRun {
  run_id: string;
  proposal: JsonObject;
  ticket: JsonObject;
  critics: JsonObject[];
  simulation: JsonObject;
}

interface ResearchResult {
  query: string;
  answer: string;
  evidence: JsonObject[];
  backend: string;
}

interface BrokerCapability {
  broker: BrokerType;
  mode: string;
  connection_status: string;
  supports: string[];
}

interface ExecuteReceipt {
  order_id: string;
  broker: BrokerType;
  status: string;
  submitted_at: string;
}

interface SuggestionRecord {
  suggestion_id: string;
  status: string;
  updated_at: string;
  payload: JsonObject;
}

interface ArtifactsResponse {
  run_id: string;
  artifacts: JsonObject[];
}

interface OrderStatus {
  order_id: string;
  broker: BrokerType;
  status: string;
  updated_at: string;
}

interface OrderFill {
  fill_id: string;
  order_id: string;
  broker: BrokerType;
  quantity: number;
  price: number;
  filled_at: string;
}

interface OrderEvent {
  event_id: string;
  event_type: string;
  created_at: string;
}

interface BreakdownAllocationItem {
  bucket: string;
  value: number;
  weight_pct: number;
}

interface BreakdownMoverItem {
  symbol: string;
  contribution: number;
  weight_pct: number;
}

interface BreakdownRisk {
  drawdown_pct: number;
  concentration_score: number;
  largest_position_pct: number;
}

interface BreakdownNavPoint {
  ts: string;
  nav: number;
  return_pct: number;
}

interface PortfolioBreakdown {
  run_id: string;
  period: string;
  frequency: string;
  holdings: JsonObject[];
  cash_breakdown: JsonObject[];
  allocation: {
    asset_class: BreakdownAllocationItem[];
    symbol: BreakdownAllocationItem[];
  };
  movers: {
    top: BreakdownMoverItem[];
    bottom: BreakdownMoverItem[];
  };
  risk: BreakdownRisk;
  nav_series: BreakdownNavPoint[];
}

interface ConsultantBrief {
  run_id: string;
  ic_brief: JsonObject;
  risk_memo: JsonObject;
  scenario_table: JsonObject[];
  allocation_recommendation: JsonObject;
}

interface DailyCycleResult {
  run_id: string;
  tracked_symbols: string[];
  period: string;
  frequency: string;
  linked_runs: {
    startup: string;
    breakdown_run_id: string;
    consultant_run_id: string;
  };
}

interface RuntimeSessionInfo {
  session_id: string;
  title: string;
  state: string;
}

interface RuntimeChatMessage {
  message_id: string;
  role: string;
  content: string;
  route: string | null;
  artifact?: JsonObject | null;
  created_at: string;
}

interface RuntimeMessageResult {
  assistant: string;
  agent: string;
  variant: string;
  decision: JsonObject;
  report: JsonObject;
  result: JsonObject;
}

interface RuntimeRunStatus {
  run_id: string;
  prompt: string;
  agent: string;
  model: string;
  started_at: number;
  status: "running" | "completed" | "aborted" | "failed";
  error?: string;
}

interface RuntimeChangeRequest {
  change_id: string;
  status: string;
  summary: string;
  snooze_until: string | null;
}

interface ProviderConnection {
  connection_id: string;
  provider: string;
  model: string;
  route_class: string;
  enabled: boolean;
  base_url?: string | null;
  api_key_env?: string | null;
  auth_method?: string | null;
  display_name?: string | null;
  oauth_connected?: boolean;
}

interface RuntimeAgentSpec {
  agent_id: string;
  name: string;
  valid: boolean;
}

interface ProviderRegistryEntry {
  provider_id: string;
  label: string;
  group: string;
  auth_methods: string[];
}

interface ProviderRuntimeModelEntry {
  model_id: string;
  label: string;
  provider_qualified: string;
}

interface MarketConnectorStatus {
  source: string;
  label: string;
  status: string;
  mode: string;
}

interface NewsFeedItem {
  news_id: string;
  symbol: string;
  source: string;
  title: string;
  summary: string;
  news_category?: string;
  news_class?: string;
  world_source?: string;
  url: string;
  thumbnail_url?: string;
  published_at: string;
}

interface NewsFeedResponse {
  sources: string[];
  symbols: string[];
  categories?: string[];
  classes?: string[];
  focus_mode?: "general" | "focused";
  items: NewsFeedItem[];
  filter_relaxed?: boolean;
  cached_count?: number;
  from_cache?: boolean;
  updated_at: string;
}

interface MarketQuoteItem {
  instrument_id: string;
  name: string;
  symbol: string;
  value: number;
  change_pct: number;
  change_value: number;
  currency: string;
  source: string;
  source_label: string;
  quote_url: string;
  status: string;
  as_of_ts: string;
  cross_check?: {
    source: string;
    status: string;
    value?: number;
    change_pct?: number;
    change_value?: number;
    delta_value?: number;
    delta_pct?: number;
  };
}

interface MarketQuotesResponse {
  source: string;
  source_label: string;
  items: MarketQuoteItem[];
  updated_at: string;
}

interface MarketCandle {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface MarketCandlesResponse {
  instrument_id: string;
  name: string;
  symbol: string;
  interval: string;
  range: string;
  source: string;
  status: string;
  candles: MarketCandle[];
  updated_at: string;
}

interface IbkrSessionStatus {
  enabled: boolean;
  authenticated: boolean;
  connected: boolean;
  status: string;
  message?: string;
  next_action?: string;
  hint?: string;
  login_url?: string;
  websocket_url?: string;
  tickle?: JsonObject;
  updated_at?: string;
}

interface GatewayChannelStatus {
  channel: string;
  label: string;
  status: string;
  message: string;
  mode: string;
  webhook_url?: string | null;
  next_action?: string;
  hint?: string;
}

interface GatewayChannelsResponse {
  channels: GatewayChannelStatus[];
  updated_at: string;
}

interface FlatRouteDecision {
  engine: string;
  routing_mode: string;
  message: string;
  selected_agent: string;
  route: string;
  reason: string;
  required_data: string[];
  skills: string[];
  updated_at: string;
}

interface FlatRouterStatus {
  settings: JsonObject;
  agents: JsonObject[];
  skills: JsonObject[];
  providers: JsonObject;
  channels: JsonObject;
  updated_at: string;
}

interface FlatRouterSettingsResponse {
  settings: JsonObject;
}

interface OpenClawHeartbeatResponse {
  scheduler: JsonObject;
  monitor: JsonObject;
  channels: JsonObject[];
}

interface OpenClawCronResponse {
  scheduler: JsonObject;
  jobs: JsonObject[];
  job_runs: JsonObject[];
  count: number;
}

interface OpenClawSettingsResponse {
  app_version: string;
  router: JsonObject;
  monitor: JsonObject;
  scheduler: JsonObject;
  channels: JsonObject[];
}

interface WorldMonitorSourceItem {
  source: string;
  url: string;
}

interface WorldMonitorSourcesResponse {
  items: WorldMonitorSourceItem[];
}

interface OpenDataDatasetItem {
  dataset_id: string;
  label: string;
  description: string;
  provider: string;
}

interface OpenDataDatasetsResponse {
  items: OpenDataDatasetItem[];
  openbb_available: boolean;
  updated_at: string;
}

interface OpenDataOverviewItem {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number;
  currency: string;
}

interface OpenDataOverviewResponse {
  symbols: string[];
  items: OpenDataOverviewItem[];
  backend: string;
  openbb_available: boolean;
  updated_at: string;
}

interface OpenDataSeriesPoint {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface OpenDataSeriesResponse {
  symbol: string;
  dataset_id: string;
  interval: string;
  points: OpenDataSeriesPoint[];
  backend: string;
  openbb_available: boolean;
  updated_at: string;
}

interface OpenStockSearchItem {
  symbol: string;
  name: string;
  exchange: string;
  type: string;
  score?: number;
}

interface OpenStockSearchResponse {
  query: string;
  items: OpenStockSearchItem[];
  backend: string;
  updated_at: string;
}

interface OpenStockCatalogResponse {
  items: OpenStockSearchItem[];
  total: number;
  offset: number;
  limit: number;
  backend: string;
  updated_at: string;
}

interface FinnhubStatusResponse {
  configured: boolean;
  base_url: string;
  webhook_secret_configured: boolean;
  webhook_url: string | null;
  updated_at: string;
}

interface FinnhubLookupItem {
  description: string;
  displaySymbol: string;
  symbol: string;
  type: string;
}

interface FinnhubLookupResponse {
  query: string;
  exchange?: string | null;
  items: FinnhubLookupItem[];
  backend: string;
  updated_at: string;
}

interface FinnhubMarketStatusResponse {
  exchange: string;
  holiday?: string | null;
  isOpen?: boolean;
  session?: string | null;
  timezone?: string;
  t?: number;
}

interface FinnhubCompanyNewsItem {
  category: string;
  datetime: number;
  headline: string;
  id: number;
  image?: string;
  related?: string;
  source: string;
  summary: string;
  url: string;
}

interface FinnhubCompanyNewsResponse {
  symbol: string;
  from: string;
  to: string;
  items: FinnhubCompanyNewsItem[];
  backend: string;
  updated_at: string;
}

interface FinnhubWidgetConfig {
  script_url: string;
  config: Record<string, unknown>;
}

interface FinnhubTradingViewWidgetsResponse {
  advanced_chart: FinnhubWidgetConfig;
  market_quotes: FinnhubWidgetConfig;
  timeline: FinnhubWidgetConfig;
  heatmap: FinnhubWidgetConfig;
}

interface OpenStockSnapshotItem {
  symbol: string;
  name: string;
  exchange: string;
  type: string;
  currency: string;
  price: number;
  change_pct: number;
  market_cap: number;
  volume: number;
}

interface OpenStockSnapshotResponse {
  symbols: string[];
  items: OpenStockSnapshotItem[];
  backend: string;
  updated_at: string;
}

interface OpenStockReferenceItem extends OpenStockSnapshotItem {
  day_high: number;
  day_low: number;
  year_high: number;
  year_low: number;
  website: string;
}

interface OpenStockReferenceResponse {
  item: OpenStockReferenceItem;
  peers: OpenStockSearchItem[];
  backend: string;
  updated_at: string;
}

const RUNTIME_PUBLIC_COMMANDS = ["/new", "/sessions", "/models", "/connect", "/agent"];
const HIDDEN_SUZY_COMMAND = "/activatesuzy";
const RUNTIME_VARIANTS = ["default", "fast", "deep"];
const MAX_PARALLEL_RUNTIME_RUNS = 3;
const MAX_DEEPSEEK_PROMPT_CHARS = 2000;
const TOP_INDEX_INSTRUMENTS = [
  "sp500",
  "nasdaq_comp",
  "russell_2000",
  "xau_usd",
  "bitcoin",
  "dbs_sg",
  "mara",
  "riot",
];
const DEFAULT_WATCHLISTS: Record<string, string[]> = {
  core: ["^GSPC", "^IXIC", "^RUT", "XAUUSD=X", "D05.SI"],
  crypto: ["BTC-USD", "MARA", "RIOT"],
  sg: ["D05.SI", "^GSPC", "^IXIC"],
};
const OAUTH_METHOD_IDS = new Set(["chatgpt-browser", "chatgpt-headless", "chatgpt_browser_oauth", "browserless_oauth"]);
const API_KEY_METHOD_IDS = new Set(["api-key", "api_key", "base_url_api_key"]);

const API_BASE = "http://127.0.0.1:8000";

async function callApi<T>(path: string, method: string, payload?: JsonObject, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: payload ? JSON.stringify(payload) : undefined,
    signal,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed: ${response.status} ${text}`);
  }
  return (await response.json()) as T;
}

function toFixedPercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function asNumber(value: unknown, fallback: number = 0): number {
  if (typeof value === "number") {
    return value;
  }
  return fallback;
}

function asString(value: unknown, fallback: string = "-"): string {
  if (typeof value === "string") {
    return value;
  }
  return fallback;
}

function usd(value: number): string {
  return `$${value.toFixed(2)}`;
}

function formatQuoteValue(value: number, currency: string): string {
  return `${value.toFixed(2)} ${currency}`;
}

function formatQuoteChange(value: number): string {
  const pct = `${Math.abs(value * 100).toFixed(2)}%`;
  return value >= 0 ? `+${pct}` : `-${pct}`;
}

function formatCompactNumber(value: number): string {
  if (!Number.isFinite(value)) {
    return "0";
  }
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000_000) {
    return `${(value / 1_000_000_000_000).toFixed(2)}T`;
  }
  if (abs >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`;
  }
  if (abs >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`;
  }
  if (abs >= 1_000) {
    return `${(value / 1_000).toFixed(2)}K`;
  }
  return value.toFixed(0);
}

function parseSymbolCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim().toUpperCase())
    .filter((item) => item.length > 0);
}

function computeCandleChartMetrics(points: OpenDataSeriesPoint[]): {
  min: number;
  max: number;
  range: number;
} {
  if (!points.length) {
    return { min: 0, max: 1, range: 1 };
  }
  const lows = points.map((point) => point.low);
  const highs = points.map((point) => point.high);
  const min = Math.min(...lows);
  const max = Math.max(...highs);
  const range = Math.max(max - min, 1);
  return { min, max, range };
}

function mapSymbolToAccountScope(symbol: string): Exclude<PortfolioAccountScope, "overall"> {
  let sum = 0;
  for (const char of symbol.toUpperCase()) {
    sum += char.charCodeAt(0);
  }
  return sum % 2 === 0 ? "ibkr" : "mt5";
}

function quoteMoveBarWidth(changePct: number): number {
  return Math.min(100, Math.max(8, Math.abs(changePct) * 1800));
}

function normalizeOAuthMethod(method: string): string {
  return method.replace("chatgpt_browser_oauth", "chatgpt-browser").replace("browserless_oauth", "chatgpt-headless");
}

function runtimeProcessLabel(artifact: JsonObject | null | undefined): string {
  if (!artifact) {
    return "-";
  }
  const report = artifact.report as JsonObject | undefined;
  const agent = typeof report?.agent === "string" ? report.agent : "suzybae";
  const selected = report?.selected_model as JsonObject | undefined;
  const provider = typeof selected?.provider === "string" ? selected.provider : "auto";
  const rawModel = typeof selected?.model === "string" ? selected.model : "auto";
  const providerPrefix = `${provider}/`;
  let model = rawModel;
  while (model.startsWith(providerPrefix)) {
    model = model.slice(providerPrefix.length);
  }
  return `agent ${agent} | provider ${provider} | model ${model}`;
}

export function App(): JSX.Element {
  const [symbols, setSymbols] = useState("AAPL,MSFT,NVDA");
  const [riskProfile, setRiskProfile] = useState<RiskProfile>("neutral");
  const [selectedBroker, setSelectedBroker] = useState<BrokerType>("ibkr_paper");
  const [researchQuery, setResearchQuery] = useState("What is the biggest portfolio risk right now?");
  const [runIdInput, setRunIdInput] = useState("");

  const [portfolio, setPortfolio] = useState<PortfolioSnapshot | null>(null);
  const [tradeRun, setTradeRun] = useState<TradeRun | null>(null);
  const [research, setResearch] = useState<ResearchResult | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionRecord[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactsResponse | null>(null);
  const [brokers, setBrokers] = useState<BrokerCapability[]>([]);
  const [receipt, setReceipt] = useState<ExecuteReceipt | null>(null);
  const [orderStatus, setOrderStatus] = useState<OrderStatus | null>(null);
  const [orderFills, setOrderFills] = useState<OrderFill[]>([]);
  const [orderEvents, setOrderEvents] = useState<OrderEvent[]>([]);
  const [breakdown, setBreakdown] = useState<PortfolioBreakdown | null>(null);
  const [breakdownPeriod, setBreakdownPeriod] = useState("7d");
  const [breakdownFrequency, setBreakdownFrequency] = useState("daily");
  const [consultantBrief, setConsultantBrief] = useState<ConsultantBrief | null>(null);
  const [dailyCycle, setDailyCycle] = useState<DailyCycleResult | null>(null);
  const [runtimeSession, setRuntimeSession] = useState<RuntimeSessionInfo | null>(null);
  const [runtimeSessions, setRuntimeSessions] = useState<RuntimeSessionInfo[]>([]);
  const [activeSessionId, setActiveSessionId] = useState("");
  const [runtimePrompt, setRuntimePrompt] = useState("Summarize what changed and what action is needed.");
  const [runtimeMessages, setRuntimeMessages] = useState<RuntimeChatMessage[]>([]);
  const [highlightMessageId, setHighlightMessageId] = useState("");
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showSessionsModal, setShowSessionsModal] = useState(false);
  const [sessionSearch, setSessionSearch] = useState("");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [sessionCursor, setSessionCursor] = useState(0);
  const [newSessionTitle, setNewSessionTitle] = useState("SuzyBae Session");
  const [renameSessionTitle, setRenameSessionTitle] = useState("");
  const [suzyActive, setSuzyActive] = useState(false);
  const [selfEditPath, setSelfEditPath] = useState("");
  const [selfEditFind, setSelfEditFind] = useState("");
  const [selfEditReplace, setSelfEditReplace] = useState("");
  const [runtimeReply, setRuntimeReply] = useState<RuntimeMessageResult | null>(null);
  const [runtimeRuns, setRuntimeRuns] = useState<RuntimeRunStatus[]>([]);
  const [runtimePulse, setRuntimePulse] = useState(0);
  const [runtimeChangeRequests, setRuntimeChangeRequests] = useState<RuntimeChangeRequest[]>([]);
  const [runtimeProvidersHealthy, setRuntimeProvidersHealthy] = useState<boolean | null>(null);
  const [runtimeAgentValidation, setRuntimeAgentValidation] = useState<JsonObject | null>(null);
  const [runtimeConnections, setRuntimeConnections] = useState<ProviderConnection[]>([]);
  const [runtimeAgents, setRuntimeAgents] = useState<RuntimeAgentSpec[]>([]);
  const [runtimeAgentId, setRuntimeAgentId] = useState("suzybae");
  const [runtimeVariant, setRuntimeVariant] = useState("default");
  const [runtimeConnectionId, setRuntimeConnectionId] = useState("");
  const [showProviderFlowModal, setShowProviderFlowModal] = useState(false);
  const [connectionLifecycleState, setConnectionLifecycleState] = useState<ConnectionState>("idle");
  const [connectionBlockReason, setConnectionBlockReason] = useState<string | null>(null);
  const [connectionProviders, setConnectionProviders] = useState<ProviderOption[]>([]);
  const [providerAuthMethods, setProviderAuthMethods] = useState<Record<string, string[]>>({});
  const [connectionModels, setConnectionModels] = useState<ProviderModel[]>([]);
  const [modelCacheByProvider, setModelCacheByProvider] = useState<Record<string, ProviderModel[]>>({});
  const [selectedProviderId, setSelectedProviderId] = useState(idleConnectionSnapshot.providerId);
  const [selectedAuthMethod, setSelectedAuthMethod] = useState(idleConnectionSnapshot.authMethod);
  const [selectedModelId, setSelectedModelId] = useState(idleConnectionSnapshot.modelId);
  const [authTokenInput, setAuthTokenInput] = useState("");
  const [authBaseUrlInput, setAuthBaseUrlInput] = useState("");
  const [sendDebounceUntil, setSendDebounceUntil] = useState(0);
  const [sendingSessionId, setSendingSessionId] = useState("");
  const [chatDocked, setChatDocked] = useState(false);
  const [chatMinimized, setChatMinimized] = useState(false);
  const [monitorStatus, setMonitorStatus] = useState<JsonObject | null>(null);
  const [monitorInterval, setMonitorInterval] = useState(60);
  const [marketConnectors, setMarketConnectors] = useState<MarketConnectorStatus[]>([]);
  const [ibkrSessionStatus, setIbkrSessionStatus] = useState<IbkrSessionStatus | null>(null);
  const [newsFeed, setNewsFeed] = useState<NewsFeedItem[]>([]);
  const [newsFeedMeta, setNewsFeedMeta] = useState({ filterRelaxed: false, cachedCount: 0, focusMode: "general" as "general" | "focused" });
  const [marketQuotes, setMarketQuotes] = useState<MarketQuoteItem[]>([]);
  const [selectedMarketInstrumentId, setSelectedMarketInstrumentId] = useState("");
  const [marketCandles, setMarketCandles] = useState<MarketCandle[]>([]);
  const [marketCandleSource, setMarketCandleSource] = useState("-");
  const [marketCandleStatus, setMarketCandleStatus] = useState("unavailable");
  const [marketCandleSymbol, setMarketCandleSymbol] = useState("-");
  const [newsSourceFilter, setNewsSourceFilter] = useState("all");
  const [newsCategoryFilter, setNewsCategoryFilter] = useState("all");
  const [newsClassFilter, setNewsClassFilter] = useState("all");
  const [feedFocusMode, setFeedFocusMode] = useState<"general" | "focused">("general");
  const [activeNavTab, setActiveNavTab] = useState("Overview");
  const [activeAccountTab, setActiveAccountTab] = useState("Positions");
  const [chartMode, setChartMode] = useState<"value" | "performance">("value");
  const [chartRange, setChartRange] = useState("1Y");
  const [watchlists, setWatchlists] = useState<Record<string, string[]>>(DEFAULT_WATCHLISTS);
  const [activeWatchlistId, setActiveWatchlistId] = useState("core");
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [watchlistTickerInput, setWatchlistTickerInput] = useState("");
  const [portfolioAccountScope, setPortfolioAccountScope] = useState<PortfolioAccountScope>("overall");
  const [showRuntimeSettingsPanel, setShowRuntimeSettingsPanel] = useState(false);
  const [showRuntimeConnectionInfo, setShowRuntimeConnectionInfo] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [lastUnifiedRefreshAt, setLastUnifiedRefreshAt] = useState("");
  const [gatewayChannels, setGatewayChannels] = useState<GatewayChannelStatus[]>([]);
  const [flatRouterStatus, setFlatRouterStatus] = useState<FlatRouterStatus | null>(null);
  const [flatRouteInput, setFlatRouteInput] = useState("Monitor world macro risk for my holdings");
  const [flatRouteDecision, setFlatRouteDecision] = useState<FlatRouteDecision | null>(null);
  const [flatRouterEngineInput, setFlatRouterEngineInput] = useState("openclaw_flat_router_v1");
  const [flatRouterModeInput, setFlatRouterModeInput] = useState("flat");
  const [flatRouterDefaultAgentInput, setFlatRouterDefaultAgentInput] = useState("suzybae");
  const [flatRouterSkillsProfileInput, setFlatRouterSkillsProfileInput] = useState("openclaw_skeleton");
  const [flatRouterGatewaysInput, setFlatRouterGatewaysInput] = useState("ibkr_cpapi,telegram,whatsapp");
  const [openClawHeartbeat, setOpenClawHeartbeat] = useState<OpenClawHeartbeatResponse | null>(null);
  const [openClawCron, setOpenClawCron] = useState<OpenClawCronResponse | null>(null);
  const [openClawSettings, setOpenClawSettings] = useState<OpenClawSettingsResponse | null>(null);
  const [finnhubStatus, setFinnhubStatus] = useState<FinnhubStatusResponse | null>(null);
  const [finnhubLookupItems, setFinnhubLookupItems] = useState<FinnhubLookupItem[]>([]);
  const [finnhubLookupQuery, setFinnhubLookupQuery] = useState("AAPL");
  const [finnhubMarketStatus, setFinnhubMarketStatus] = useState<FinnhubMarketStatusResponse | null>(null);
  const [finnhubCompanyNews, setFinnhubCompanyNews] = useState<FinnhubCompanyNewsItem[]>([]);
  const [finnhubWidgetConfigs, setFinnhubWidgetConfigs] = useState<FinnhubTradingViewWidgetsResponse | null>(null);
  const [worldMonitorFeed, setWorldMonitorFeed] = useState<NewsFeedItem[]>([]);
  const [worldMonitorSources, setWorldMonitorSources] = useState<WorldMonitorSourceItem[]>([]);
  const [worldMonitorSymbols, setWorldMonitorSymbols] = useState("AAPL,MSFT,NVDA");
  const [worldMonitorLimit, setWorldMonitorLimit] = useState(18);
  const [worldMonitorFocusMode, setWorldMonitorFocusMode] = useState<"general" | "focused">("general");
  const [openDataQuery, setOpenDataQuery] = useState("equity");
  const [openDataDatasets, setOpenDataDatasets] = useState<OpenDataDatasetItem[]>([]);
  const [openDataOverviewSymbols, setOpenDataOverviewSymbols] = useState("AAPL,MSFT,NVDA");
  const [openDataOverview, setOpenDataOverview] = useState<OpenDataOverviewItem[]>([]);
  const [openDataSeriesSymbol, setOpenDataSeriesSymbol] = useState("AAPL");
  const [openDataSeriesInterval, setOpenDataSeriesInterval] = useState("1d");
  const [openDataSeriesLimit, setOpenDataSeriesLimit] = useState(120);
  const [openDataSeries, setOpenDataSeries] = useState<OpenDataSeriesPoint[]>([]);
  const [openDataSeriesBackend, setOpenDataSeriesBackend] = useState("openbb_bridge");
  const [openDataOpenbbAvailable, setOpenDataOpenbbAvailable] = useState(false);
  const [openStockQuery, setOpenStockQuery] = useState("NVIDIA");
  const [openStockActiveSymbol, setOpenStockActiveSymbol] = useState("AAPL");
  const [openStockReference, setOpenStockReference] = useState<OpenStockReferenceItem | null>(null);
  const [openStockSearchItems, setOpenStockSearchItems] = useState<OpenStockSearchItem[]>([]);
  const [openStockCatalogItems, setOpenStockCatalogItems] = useState<OpenStockSearchItem[]>([]);
  const [openStockCatalogQuery, setOpenStockCatalogQuery] = useState("");
  const [openStockCatalogExchange, setOpenStockCatalogExchange] = useState("ALL");
  const [openStockCatalogType, setOpenStockCatalogType] = useState("ALL");
  const [openStockCatalogOffset, setOpenStockCatalogOffset] = useState(0);
  const [openStockCatalogLimit, setOpenStockCatalogLimit] = useState(12);
  const [openStockCatalogTotal, setOpenStockCatalogTotal] = useState(0);
  const [openStockSnapshotSymbols, setOpenStockSnapshotSymbols] = useState("AAPL,MSFT,NVDA");
  const [openStockSnapshotItems, setOpenStockSnapshotItems] = useState<OpenStockSnapshotItem[]>([]);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runtimeAbortControllers = useRef<Map<string, AbortController>>(new Map());

  const trackedSymbols = useMemo(
    () => symbols.split(",").map((s) => s.trim().toUpperCase()).filter((s) => s.length > 0),
    [symbols]
  );
  const activeWatchlistSymbolsMemo = useMemo(() => watchlists[activeWatchlistId] ?? [], [activeWatchlistId, watchlists]);
  const activeWatchlistSymbolsCsv = useMemo(() => activeWatchlistSymbolsMemo.join(","), [activeWatchlistSymbolsMemo]);

  const primarySymbol = trackedSymbols[0] ?? "AAPL";
  const artifactRunId = runIdInput || tradeRun?.run_id || "";
  const activeOrderId = receipt?.order_id ?? orderStatus?.order_id ?? "";
  const selectedConnection = runtimeConnections.find((item) => item.connection_id === runtimeConnectionId) ?? null;
  const filteredSessions = runtimeSessions.filter((item) => {
    const q = sessionSearch.trim().toLowerCase();
    if (!q) {
      return true;
    }
    return item.session_id.toLowerCase().includes(q) || item.title.toLowerCase().includes(q);
  });
  const runningRuntimeRuns = runtimeRuns.filter((item) => item.status === "running");
  const latestRunningRun = runningRuntimeRuns[0] ?? null;
  const runtimeDotCount = (runtimePulse % 3) + 1;
  const selectedSessionFromModal = filteredSessions.length ? filteredSessions[Math.min(sessionCursor, filteredSessions.length - 1)] : null;
  const activeRuntimeSessionId = activeSessionId || runtimeSession?.session_id || "";
  const runtimeCapabilities = useCapabilities(activeRuntimeSessionId);
  const runtimeStatus = useRuntimeStatus(activeRuntimeSessionId);
  const selectedProviderLabel = connectionProviders.find((item) => item.provider_id === selectedProviderId)?.label ?? selectedProviderId;
  const availableAuthMethods = providerAuthMethods[selectedProviderId] ?? [];
  const runtimeCanSendMessage = runtimeCapabilities.canSend || (runtimeConnectionId.trim().length > 0 && connectionLifecycleState === "connected");
  const runtimeIsProcessing = Boolean((activeRuntimeSessionId && sendingSessionId === activeRuntimeSessionId) || latestRunningRun);

  const cycleRuntimeAgent = (): void => {
    const ids = runtimeAgents.length ? runtimeAgents.map((item) => item.agent_id) : ["suzybae"];
    const currentIndex = ids.indexOf(runtimeAgentId);
    const next = currentIndex >= 0 ? ids[(currentIndex + 1) % ids.length] : ids[0];
    setRuntimeAgentId(next);
  };

  const cycleRuntimeVariant = (): void => {
    const currentIndex = RUNTIME_VARIANTS.indexOf(runtimeVariant);
    const next = currentIndex >= 0 ? RUNTIME_VARIANTS[(currentIndex + 1) % RUNTIME_VARIANTS.length] : RUNTIME_VARIANTS[0];
    setRuntimeVariant(next);
  };

  const commandPaletteSections = [
    {
      title: "Providers",
      items: [
        { id: "connect", label: "Connect Providers", action: "/connect", description: "Connect OAuth or API providers" },
      ],
    },
    {
      title: "Agent",
      items: [
        { id: "agent", label: "Agent Selection", action: "/agent", description: "Cycle to next runtime agent" },
      ],
    },
    {
      title: "Models",
      items: [
        { id: "models", label: "Model Selection", action: "/models", description: "Choose model for current connection" },
      ],
    },
    {
      title: "Sessions",
      items: [
        { id: "sessions", label: "Session Manager", action: "/sessions", description: "Switch, rename, or delete sessions" },
        { id: "new", label: "New Session", action: "/new", description: "Create a new SuzyBae session" },
      ],
    },
  ];

  useEffect(() => {
    const loadBootstrap = async (): Promise<void> => {
      try {
        const brokersResp = await callApi<{ brokers: BrokerCapability[] }>("/execution/brokers", "GET");
        setBrokers(brokersResp.brokers);
        if (brokersResp.brokers.length > 0) {
          setSelectedBroker(brokersResp.brokers[0].broker);
        }
        const sessionsResp = await callApi<{ sessions: RuntimeSessionInfo[] }>("/runtime/chat/sessions", "GET");
        setRuntimeSessions(sessionsResp.sessions);
        if (sessionsResp.sessions.length > 0) {
          const firstId = sessionsResp.sessions[0].session_id;
          const selected = await callApi<{ session: RuntimeSessionInfo; messages: RuntimeChatMessage[] }>(`/runtime/chat/sessions/${firstId}`, "GET");
          setRuntimeSession(selected.session);
          setRuntimeMessages(selected.messages);
          setActiveSessionId(firstId);
        }
        const connResp = await callApi<{ connections: ProviderConnection[] }>("/runtime/providers/connections", "GET");
        setRuntimeConnections(connResp.connections);
        if (connResp.connections.length > 0) {
          setRuntimeConnectionId(connResp.connections[0].connection_id);
        }
        const agentsResp = await callApi<{ agents: RuntimeAgentSpec[] }>("/runtime/agents", "GET");
        const validAgents = agentsResp.agents.filter((item) => item.valid);
        setRuntimeAgents(validAgents);
        if (validAgents.length > 0 && !validAgents.some((item) => item.agent_id === runtimeAgentId)) {
          setRuntimeAgentId(validAgents[0].agent_id);
        }
        const suzyResp = await callApi<{ active: boolean }>("/runtime/suzy/status", "GET");
        setSuzyActive(suzyResp.active);
        const runtimeProviderResp = await callApi<{ healthy: boolean }>("/runtime/providers/status", "GET");
        setRuntimeProvidersHealthy(runtimeProviderResp.healthy);
        const runtimeValidationResp = await callApi<JsonObject>("/runtime/agents/validation", "GET");
        setRuntimeAgentValidation(runtimeValidationResp);
        const changeRequestsResp = await callApi<{ change_requests: RuntimeChangeRequest[] }>("/runtime/change-requests", "GET");
        setRuntimeChangeRequests(changeRequestsResp.change_requests);
        const connectorsResp = await callApi<{ connectors: MarketConnectorStatus[] }>("/market/connectors/status", "GET");
        setMarketConnectors(connectorsResp.connectors);
        const ibkrResp = await callApi<IbkrSessionStatus>("/market/ibkr/session", "GET");
        setIbkrSessionStatus(ibkrResp);
        const gatewayResp = await callApi<GatewayChannelsResponse>("/gateway/channels", "GET");
        setGatewayChannels(gatewayResp.channels);
        const quotesResp = await callApi<MarketQuotesResponse>("/market/quotes", "POST", {
          instruments: TOP_INDEX_INSTRUMENTS,
          focus_mode: "general",
        });
        setMarketQuotes(quotesResp.items);
        const newsResp = await callApi<NewsFeedResponse>("/news/feed", "POST", {
          symbols: ["AAPL", "MSFT", "NVDA"],
          limit: 24,
          focus_mode: "general",
          categories: [],
          classes: [],
        });
        setNewsFeed(newsResp.items);
        setNewsFeedMeta({
          filterRelaxed: Boolean(newsResp.filter_relaxed),
          cachedCount: Number(newsResp.cached_count ?? 0),
          focusMode: newsResp.focus_mode === "focused" ? "focused" : "general",
        });
        const worldResp = await callApi<{ items: NewsFeedItem[] }>("/world-monitor/feed", "POST", {
          symbols: parseSymbolCsv(worldMonitorSymbols),
          limit: Math.max(1, Math.min(worldMonitorLimit, 50)),
          focus_mode: worldMonitorFocusMode,
        });
        setWorldMonitorFeed(worldResp.items);
        const worldSourcesResp = await callApi<WorldMonitorSourcesResponse>("/world-monitor/sources", "GET");
        setWorldMonitorSources(worldSourcesResp.items);
        const flatStatus = await callApi<FlatRouterStatus>("/agent-router/status", "GET");
        setFlatRouterStatus(flatStatus);
        setFlatRouterEngineInput(asString(flatStatus.settings.engine, "openclaw_flat_router_v1"));
        setFlatRouterModeInput(asString(flatStatus.settings.routing_mode, "flat"));
        setFlatRouterDefaultAgentInput(asString(flatStatus.settings.default_agent, "suzybae"));
        setFlatRouterSkillsProfileInput(asString(flatStatus.settings.skills_profile, "openclaw_skeleton"));
        const flatGateways = Array.isArray(flatStatus.settings.enabled_gateways) ? flatStatus.settings.enabled_gateways.join(",") : "ibkr_cpapi,telegram,whatsapp";
        setFlatRouterGatewaysInput(flatGateways);
        const openDataOverviewResp = await callApi<OpenDataOverviewResponse>("/open-data/overview", "POST", {
          symbols: ["AAPL", "MSFT", "NVDA"],
          limit: 8,
        });
        setOpenDataOverview(openDataOverviewResp.items);
        setOpenDataOpenbbAvailable(openDataOverviewResp.openbb_available);
        const openDataDatasetsResp = await callApi<OpenDataDatasetsResponse>("/open-data/datasets", "POST", {
          query: openDataQuery,
          limit: 12,
        });
        setOpenDataDatasets(openDataDatasetsResp.items);
        const openStockResp = await callApi<OpenStockSnapshotResponse>("/open-stock/snapshot", "POST", {
          symbols: ["AAPL", "MSFT", "NVDA"],
          limit: 8,
        });
        setOpenStockSnapshotItems(openStockResp.items);
        const openStockCatalogResp = await callApi<OpenStockCatalogResponse>("/open-stock/catalog", "POST", {
          query: undefined,
          exchange: "ALL",
          stock_type: "ALL",
          limit: openStockCatalogLimit,
          offset: 0,
        });
        setOpenStockCatalogItems(openStockCatalogResp.items);
        setOpenStockCatalogTotal(openStockCatalogResp.total);
        const openClawHeartbeatResp = await callApi<OpenClawHeartbeatResponse>("/openclaw/heartbeat", "GET");
        setOpenClawHeartbeat(openClawHeartbeatResp);
        const openClawCronResp = await callApi<OpenClawCronResponse>("/openclaw/cron", "GET");
        setOpenClawCron(openClawCronResp);
        const openClawSettingsResp = await callApi<OpenClawSettingsResponse>("/openclaw/settings", "GET");
        setOpenClawSettings(openClawSettingsResp);
        const finnhubStatusResp = await callApi<FinnhubStatusResponse>("/finnhub/status", "GET");
        setFinnhubStatus(finnhubStatusResp);
        const finnhubMarketStatusResp = await callApi<FinnhubMarketStatusResponse>("/finnhub/market-status?exchange=US", "GET");
        setFinnhubMarketStatus(finnhubMarketStatusResp);
        const finnhubWidgetResp = await callApi<FinnhubTradingViewWidgetsResponse>(`/finnhub/tradingview/widgets?symbols=${encodeURIComponent("AAPL,MSFT,NVDA")}`, "GET");
        setFinnhubWidgetConfigs(finnhubWidgetResp);
      } catch (e) {
        setError((e as Error).message);
      }
    };
    void loadBootstrap();
  }, [runtimeAgentId, worldMonitorFocusMode, worldMonitorLimit, worldMonitorSymbols, openDataQuery, openStockCatalogLimit]);

  useEffect(() => {
    const saved = window.localStorage.getItem("portfolio-desk-theme");
    if (saved === "dark") {
      setDarkMode(true);
    }
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark-mode");
      window.localStorage.setItem("portfolio-desk-theme", "dark");
      return;
    }
    document.body.classList.remove("dark-mode");
    window.localStorage.setItem("portfolio-desk-theme", "light");
  }, [darkMode]);

  useEffect(() => {
    const rawLists = window.localStorage.getItem("portfolio-desk-watchlists");
    const rawActive = window.localStorage.getItem("portfolio-desk-active-watchlist");
    if (rawLists) {
      try {
        const parsed = JSON.parse(rawLists) as Record<string, string[]>;
        const normalized: Record<string, string[]> = {};
        Object.entries(parsed).forEach(([key, value]) => {
          if (typeof key !== "string" || !key.trim() || !Array.isArray(value)) {
            return;
          }
          const symbols = value
            .map((item) => (typeof item === "string" ? item.trim().toUpperCase() : ""))
            .filter((item) => item.length > 0);
          if (symbols.length) {
            normalized[key.trim()] = Array.from(new Set(symbols));
          }
        });
        if (Object.keys(normalized).length) {
          setWatchlists(normalized);
        }
      } catch {
        setWatchlists(DEFAULT_WATCHLISTS);
      }
    }
    if (rawActive) {
      setActiveWatchlistId(rawActive);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("portfolio-desk-watchlists", JSON.stringify(watchlists));
  }, [watchlists]);

  useEffect(() => {
    window.localStorage.setItem("portfolio-desk-active-watchlist", activeWatchlistId);
  }, [activeWatchlistId]);

  useEffect(() => {
    if (watchlists[activeWatchlistId]) {
      return;
    }
    const first = Object.keys(watchlists)[0];
    if (first) {
      setActiveWatchlistId(first);
    }
  }, [activeWatchlistId, watchlists]);

  useEffect(() => {
    const scope: PortfolioAccountScope = selectedBroker === "ibkr_paper" ? "ibkr" : "mt5";
    setPortfolioAccountScope(scope);
  }, [selectedBroker]);

  useEffect(() => {
    if (sessionCursor >= filteredSessions.length) {
      setSessionCursor(Math.max(0, filteredSessions.length - 1));
    }
  }, [filteredSessions.length, sessionCursor]);

  useEffect(() => {
    if (runtimeStatus.bindState === "connected" && connectionLifecycleState === "idle") {
      setConnectionLifecycleState("connected");
    }
  }, [connectionLifecycleState, runtimeStatus.bindState]);

  const runStartup = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    setReceipt(null);
    try {
      await callApi<{ risk_profile: RiskProfile }>(`/risk-profile/${riskProfile}`, "PUT");
      await callApi<{ portfolio_snapshot: PortfolioSnapshot }>("/portfolio", "PUT", {
        positions: [{ symbol: primarySymbol, asset: "stock", quantity: 10, avg_cost: 180, last_price: 185 }],
        cash: 10000
      });
      const data = await callApi<StartupReport>("/startup-report", "POST", { tracked_symbols: trackedSymbols });
      setPortfolio(data.portfolio_snapshot);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const refreshPortfolio = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ portfolio_snapshot: PortfolioSnapshot }>("/portfolio", "GET");
      setPortfolio(data.portfolio_snapshot);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runResearch = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<ResearchResult>("/research/query", "POST", { query: researchQuery });
      setResearch(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runTradeLane = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<TradeRun>("/trade-lane/run", "POST", { symbol: primarySymbol, profile: riskProfile });
      setTradeRun(data);
      setRunIdInput(data.run_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const submitPaper = async (): Promise<void> => {
    if (!tradeRun) {
      setError("Run trade lane before paper submit.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ receipt: ExecuteReceipt }>("/execution/paper-submit", "POST", {
        ticket: tradeRun.ticket,
        confirm: true,
        broker: selectedBroker
      });
      setReceipt(data.receipt);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadSuggestions = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ suggestions: SuggestionRecord[] }>("/suggestions", "GET");
      setSuggestions(data.suggestions);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadArtifacts = async (): Promise<void> => {
    if (!artifactRunId) {
      setError("Provide run id or run trade lane first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<ArtifactsResponse>(`/runs/${artifactRunId}/artifacts`, "GET");
      setArtifacts(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const fetchOrderStatus = async (): Promise<void> => {
    if (!activeOrderId) {
      setError("Submit an order first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ status: OrderStatus }>(`/execution/orders/${activeOrderId}/status`, "GET");
      setOrderStatus(data.status);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const cancelOrder = async (): Promise<void> => {
    if (!activeOrderId) {
      setError("Submit an order first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ status: OrderStatus }>(`/execution/orders/${activeOrderId}/cancel`, "POST");
      setOrderStatus(data.status);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const fetchOrderFills = async (): Promise<void> => {
    if (!activeOrderId) {
      setError("Submit an order first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ fills: OrderFill[] }>(`/execution/orders/${activeOrderId}/fills`, "GET");
      setOrderFills(data.fills);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const fetchOrderEvents = async (): Promise<void> => {
    if (!activeOrderId) {
      setError("Submit an order first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ events: OrderEvent[] }>(`/execution/orders/${activeOrderId}/events`, "GET");
      setOrderEvents(data.events);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const reconcileOrders = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      await callApi<{ count: number }>("/execution/reconcile", "POST", { broker: selectedBroker });
      if (activeOrderId) {
        await fetchOrderStatus();
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadBreakdown = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<PortfolioBreakdown>("/portfolio/breakdown", "POST", {
        period: breakdownPeriod,
        frequency: breakdownFrequency
      });
      setBreakdown(data);
      setRunIdInput(data.run_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadConsultantBrief = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<ConsultantBrief>("/consultant/brief", "POST", {
        period: breakdownPeriod,
        frequency: breakdownFrequency
      });
      setConsultantBrief(data);
      setRunIdInput(data.run_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runDailyCycle = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<DailyCycleResult>("/operator/daily-cycle", "POST", {
        tracked_symbols: trackedSymbols,
        period: breakdownPeriod,
        frequency: breakdownFrequency
      });
      setDailyCycle(data);
      setRunIdInput(data.run_id);
      await Promise.all([refreshPortfolio(), loadBreakdown(), loadConsultantBrief()]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const createRuntimeSession = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<RuntimeSessionInfo>("/runtime/chat/sessions", "POST", { title: "SuzyBae Session" });
      setRuntimeSession(data);
      setActiveSessionId(data.session_id);
      setRuntimeMessages([]);
      setHighlightMessageId("");
      await loadRuntimeSessions();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadRuntimeSessions = async (): Promise<void> => {
    const data = await callApi<{ sessions: RuntimeSessionInfo[] }>("/runtime/chat/sessions", "GET");
    setRuntimeSessions(data.sessions);
    if (!activeSessionId && data.sessions.length > 0) {
      setActiveSessionId(data.sessions[0].session_id);
      setRuntimeSession(data.sessions[0]);
    }
  };

  const selectRuntimeSession = async (sessionId: string): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ session: RuntimeSessionInfo; messages: RuntimeChatMessage[] }>(`/runtime/chat/sessions/${sessionId}`, "GET");
      setRuntimeSession(data.session);
      setActiveSessionId(sessionId);
      setRuntimeMessages(data.messages);
      setHighlightMessageId("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const openSessionsModal = (): void => {
    setShowSessionsModal(true);
    setSessionSearch("");
    setSessionCursor(0);
    const active = runtimeSessions.find((item) => item.session_id === activeSessionId);
    setRenameSessionTitle(active?.title ?? "");
  };

  const openModelsModal = (): void => {
    setShowProviderFlowModal(true);
    if (selectedProviderId) {
      void loadModelsForFlow();
    } else {
      setConnectionLifecycleState("selecting_provider");
    }
  };

  const createRuntimeSessionFromModal = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const title = newSessionTitle.trim() || "SuzyBae Session";
      const data = await callApi<RuntimeSessionInfo>("/runtime/chat/sessions", "POST", { title });
      setRuntimeSession(data);
      setActiveSessionId(data.session_id);
      setRuntimeMessages([]);
      await loadRuntimeSessions();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleSessionModalKeyDown = (event: { key: string; preventDefault: () => void }): void => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSessionCursor((prev) => Math.min(filteredSessions.length - 1, prev + 1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setSessionCursor((prev) => Math.max(0, prev - 1));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      if (selectedSessionFromModal) {
        void selectRuntimeSession(selectedSessionFromModal.session_id);
      }
    }
  };

  const deleteRuntimeSession = async (): Promise<void> => {
    const targetSessionId = activeSessionId || runtimeSession?.session_id;
    if (!targetSessionId) {
      setError("Select a session first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await callApi<{ deleted: boolean }>(`/runtime/chat/sessions/${targetSessionId}`, "DELETE");
      setRuntimeReply(null);
      await loadRuntimeSessions();
      const refreshed = await callApi<{ sessions: RuntimeSessionInfo[] }>("/runtime/chat/sessions", "GET");
      if (refreshed.sessions.length > 0) {
        await selectRuntimeSession(refreshed.sessions[0].session_id);
      } else {
        setRuntimeSession(null);
        setActiveSessionId("");
        setRuntimeMessages([]);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const renameRuntimeSession = async (): Promise<void> => {
    const targetSessionId = activeSessionId || runtimeSession?.session_id;
    if (!targetSessionId) {
      setError("Select a session first.");
      return;
    }
    const title = renameSessionTitle.trim();
    if (!title) {
      setError("Session title is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await callApi<{ session: RuntimeSessionInfo }>(`/runtime/chat/sessions/${targetSessionId}`, "PATCH", { title });
      await loadRuntimeSessions();
      await selectRuntimeSession(targetSessionId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const refreshProviderState = async (): Promise<{ connections: ProviderConnection[] }> => {
    const connData = await callApi<{ connections: ProviderConnection[] }>("/runtime/providers/connections", "GET");
    setRuntimeConnections(connData.connections);
    return {
      connections: connData.connections,
    };
  };

  const clearAuthInputs = (): void => {
    setAuthTokenInput("");
    setApiKeyInput("");
    setAuthBaseUrlInput("");
  };

  const resetConnectionUI = (): void => {
    setConnectionLifecycleState("idle");
    setConnectionBlockReason(null);
    setSelectedProviderId(idleConnectionSnapshot.providerId);
    setSelectedAuthMethod(idleConnectionSnapshot.authMethod);
    setSelectedModelId(idleConnectionSnapshot.modelId);
    setConnectionModels([]);
    clearAuthInputs();
  };

  const cancelActiveStreamsAndJobs = (): void => {
    runtimeAbortControllers.current.forEach((controller) => {
      controller.abort();
    });
    runtimeAbortControllers.current.clear();
    setRuntimeRuns((prev) => prev.map((item) => (
      item.status === "running"
        ? { ...item, status: "aborted", error: "Interrupted by lifecycle reset." }
        : item
    )));
    setSendingSessionId("");
  };

  const teardownBackendBinding = async (): Promise<void> => {
    if (!activeRuntimeSessionId) {
      return;
    }
    await callApi<{ binding: JsonObject }>("/session/unbind", "POST", { session_id: activeRuntimeSessionId });
    await callApi<{ binding: JsonObject }>("/session/reset", "POST", { session_id: activeRuntimeSessionId });
    setRuntimeConnectionId("");
  };

  const forgetStoredCredentials = async (providerId: string): Promise<void> => {
    if (!providerId || !activeRuntimeSessionId) {
      return;
    }
    await callApi<{ status: string }>("/auth/logout", "POST", {
      provider_id: providerId,
      session_id: activeRuntimeSessionId,
    });
    setModelCacheByProvider((prev) => {
      const next = { ...prev };
      delete next[providerId];
      return next;
    });
  };

  const disconnectCurrentConnection = async (): Promise<void> => {
    cancelActiveStreamsAndJobs();
    await teardownBackendBinding();
    resetConnectionUI();
  };

  const loadProviderRegistry = async (): Promise<void> => {
    const data = await callApi<{ providers: ProviderRegistryEntry[] }>("/providers", "GET");
    setConnectionProviders(
      data.providers.map((item) => ({
        provider_id: item.provider_id,
        label: item.label,
        group: item.group,
      }))
    );
    const methods: Record<string, string[]> = {};
    data.providers.forEach((item) => {
      methods[item.provider_id] = item.auth_methods;
    });
    setProviderAuthMethods(methods);
  };

  const openProviderFirstConnectFlow = async (): Promise<void> => {
    setShowProviderFlowModal(true);
    setConnectionLifecycleState("selecting_provider");
    setConnectionBlockReason(null);
    await loadProviderRegistry();
  };

  const selectProviderForFlow = async (providerId: string): Promise<void> => {
    if (selectedProviderId && selectedProviderId !== providerId) {
      await disconnectCurrentConnection();
    }
    const methods = providerAuthMethods[providerId] ?? [];
    setSelectedProviderId(providerId);
    setSelectedAuthMethod(methods[0] ?? "");
    setSelectedModelId("");
    setConnectionModels([]);
    setConnectionBlockReason(null);
    clearAuthInputs();
    setConnectionLifecycleState("awaiting_auth");
  };

  const changeAuthMethodForFlow = async (method: string): Promise<void> => {
    if (selectedProviderId) {
      await forgetStoredCredentials(selectedProviderId);
    }
    setSelectedAuthMethod(method);
    setSelectedModelId("");
    setConnectionModels([]);
    setConnectionBlockReason(null);
    clearAuthInputs();
    setConnectionLifecycleState("awaiting_auth");
  };

  const loadModelsForFlow = async (): Promise<void> => {
    if (!selectedProviderId) {
      setConnectionLifecycleState("provider_reset_required");
      setConnectionBlockReason("Provider is required before loading models.");
      return;
    }
    setConnectionLifecycleState("loading_models");
    setConnectionBlockReason(null);
    try {
      const cached = modelCacheByProvider[selectedProviderId];
      if (cached) {
        setConnectionModels(cached);
        setConnectionLifecycleState("auth_valid");
        return;
      }
      const payload = await callApi<{ provider_id: string; models: ProviderRuntimeModelEntry[] }>(
        `/runtime/providers/models?provider_id=${encodeURIComponent(selectedProviderId)}`,
        "GET",
      );
      const normalized = payload.models.map((item) => ({ model_id: item.model_id, label: item.label }));
      setConnectionModels(normalized);
      setModelCacheByProvider((prev) => ({ ...prev, [selectedProviderId]: normalized }));
      setConnectionLifecycleState("auth_valid");
    } catch (e) {
      setConnectionLifecycleState("model_load_failed");
      setConnectionBlockReason((e as Error).message);
      setError((e as Error).message);
    }
  };

  const completeAuthFlow = async (): Promise<void> => {
    if (!activeRuntimeSessionId) {
      setConnectionBlockReason("Session is required before authentication.");
      return;
    }
    if (!selectedProviderId || !selectedAuthMethod) {
      setConnectionBlockReason("Provider and authentication method are required.");
      return;
    }
    setBusy(true);
    setError(null);
    setConnectionBlockReason(null);
    try {
      if (selectedAuthMethod === "local-runtime") {
        setConnectionLifecycleState("auth_valid");
        await loadModelsForFlow();
        return;
      }

      if (OAUTH_METHOD_IDS.has(selectedAuthMethod)) {
        const normalizedMethod = normalizeOAuthMethod(selectedAuthMethod);
        const oauthConnectionId = `${selectedProviderId}-${normalizedMethod}-${activeRuntimeSessionId}`
          .replace(/[^a-zA-Z0-9_-]/g, "-")
          .toLowerCase();
        await callApi<{ connection: ProviderConnection }>("/runtime/providers/connections", "POST", {
          connection_id: oauthConnectionId,
          provider: selectedProviderId,
          model: selectedModelId || connectionModels[0]?.model_id || "openai/gpt-5.4",
          route_class: runtimeVariant === "deep" ? "deep_reasoning" : "fast_summary",
          enabled: false,
          auth_method: normalizedMethod,
          display_name: `${selectedProviderId}:${normalizedMethod}`,
        });
        const authorize = await callApi<{ url: string }>(`/runtime/providers/${selectedProviderId}/oauth/authorize`, "POST", {
          method_id: normalizedMethod,
          connection_id: oauthConnectionId,
        });
        if (authorize.url) {
          window.open(authorize.url, "_blank", "noopener,noreferrer");
        }
        await refreshProviderState();
        const refreshed = await callApi<{ connections: ProviderConnection[] }>("/runtime/providers/connections", "GET");
        const matched = refreshed.connections.find((item) => item.connection_id === oauthConnectionId);
        if (!matched?.oauth_connected) {
          setConnectionLifecycleState("awaiting_auth");
          setConnectionBlockReason("OAuth started. Finish provider sign-in, then click Authenticate again.");
          return;
        }
        setConnectionLifecycleState("auth_valid");
        setSelectedAuthMethod(normalizedMethod);
        await loadModelsForFlow();
        return;
      }

      await callApi<JsonObject>("/auth/start", "POST", {
        provider_id: selectedProviderId,
        auth_method: selectedAuthMethod,
        session_id: activeRuntimeSessionId,
      });

      const payload: JsonObject = {
        provider_id: selectedProviderId,
        auth_method: selectedAuthMethod,
        session_id: activeRuntimeSessionId,
      };
      if (API_KEY_METHOD_IDS.has(selectedAuthMethod)) {
        payload.api_key = apiKeyInput.trim();
      }
      if (selectedAuthMethod === "token") {
        payload.token = authTokenInput.trim();
      }
      if (selectedAuthMethod === "base_url" || selectedAuthMethod === "base_url_api_key") {
        payload.base_url = authBaseUrlInput.trim();
      }

      await callApi<JsonObject>("/auth/complete", "POST", payload);
      setConnectionLifecycleState("auth_valid");
      if (!API_KEY_METHOD_IDS.has(selectedAuthMethod)) {
        clearAuthInputs();
      }
      await loadModelsForFlow();
    } catch (e) {
      setConnectionLifecycleState("auth_failed");
      setConnectionBlockReason((e as Error).message);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const bindChatSession = async (
    {
      providerId,
      authMethod,
      modelId,
      baseUrl,
    }: { providerId: string; authMethod: string; modelId: string; baseUrl?: string },
  ): Promise<void> => {
    if (!activeRuntimeSessionId) {
      setConnectionLifecycleState("session_bind_failed");
      setConnectionBlockReason("Session is required before bind.");
      return;
    }
    if (!providerId || !authMethod || !modelId) {
      setConnectionLifecycleState("session_bind_failed");
      setConnectionBlockReason("Provider, authentication, and model are required before bind.");
      return;
    }
    setConnectionLifecycleState("binding_session");
    setConnectionBlockReason(null);
    setBusy(true);
    try {
      const normalizedAuthMethod = normalizeOAuthMethod(authMethod);
      cancelActiveStreamsAndJobs();
      await teardownBackendBinding();
      const connectionId = `${providerId}-${normalizedAuthMethod}-${activeRuntimeSessionId}`
        .replace(/[^a-zA-Z0-9_-]/g, "-")
        .toLowerCase();
      await callApi<{ connection: ProviderConnection }>("/runtime/providers/connections", "POST", {
        connection_id: connectionId,
        provider: providerId,
        model: modelId,
        route_class: runtimeVariant === "deep" ? "deep_reasoning" : "fast_summary",
        enabled: true,
        auth_method: normalizedAuthMethod,
        api_key: API_KEY_METHOD_IDS.has(normalizedAuthMethod) ? apiKeyInput.trim() : undefined,
        base_url: baseUrl ?? null,
        display_name: `${providerId}:${modelId}`,
      });
      await callApi<{ binding: JsonObject }>("/session/bind", "POST", {
        session_id: activeRuntimeSessionId,
        provider_id: providerId,
        auth_method: normalizedAuthMethod,
        model_id: modelId,
        base_url: baseUrl,
      });
      await bindConnectionForCurrentAgent(connectionId);
      setRuntimeConnectionId(connectionId);
      setSelectedProviderId(providerId);
      setSelectedAuthMethod(normalizedAuthMethod);
      setSelectedModelId(modelId);
      setConnectionLifecycleState("connected");
      setShowProviderFlowModal(false);
      clearAuthInputs();
      await refreshProviderState();
    } catch (e) {
      setConnectionLifecycleState("session_bind_failed");
      setConnectionBlockReason((e as Error).message);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const bindSelectedFlowSession = async (): Promise<void> => {
    await bindChatSession({
      providerId: selectedProviderId,
      authMethod: selectedAuthMethod,
      modelId: selectedModelId,
      baseUrl: authBaseUrlInput.trim() || undefined,
    });
  };

  const bindConnectionForCurrentAgent = async (connectionId: string): Promise<void> => {
    await callApi<{ binding: JsonObject }>(`/runtime/agents/${runtimeAgentId}/connection`, "POST", {
      connection_id: connectionId,
    });
  };

  const executeRuntimeCommand = async (prompt: string): Promise<boolean> => {
    const tokens = prompt.trim().split(/\s+/);
    const command = tokens[0]?.toLowerCase();
    if (!command.startsWith("/")) {
      return false;
    }

    if (command === "/sessions") {
      const data = await callApi<{ sessions: RuntimeSessionInfo[] }>("/runtime/chat/sessions", "GET");
      setRuntimeSessions(data.sessions);
      openSessionsModal();
      const requested = tokens[1];
      if (requested) {
        const matched = data.sessions.find((item) => item.session_id === requested || item.title === requested);
        if (matched) {
          await selectRuntimeSession(matched.session_id);
        }
      }
      setRuntimeReply({
        assistant: `Loaded ${data.sessions.length} sessions. Use selector to switch.`,
        agent: runtimeAgentId,
        variant: runtimeVariant,
        decision: { workflow: "command" },
        report: { command: "/sessions" },
        result: { sessions: data.sessions }
      });
      return true;
    }

    if (command === "/models") {
      setShowProviderFlowModal(true);
      if (selectedProviderId) {
        await loadModelsForFlow();
      } else {
        setConnectionLifecycleState("selecting_provider");
      }
      setRuntimeReply({
        assistant: "Model picker opened. Select provider/auth first if not completed.",
        agent: runtimeAgentId,
        variant: runtimeVariant,
        decision: { workflow: "command" },
        report: { command: "/models" },
        result: { provider: selectedProviderId || null, state: connectionLifecycleState }
      });
      return true;
    }

    if (command === "/agent") {
      const ids = runtimeAgents.length ? runtimeAgents.map((item) => item.agent_id) : ["suzybae"];
      const currentIndex = ids.indexOf(runtimeAgentId);
      const next = currentIndex >= 0 ? ids[(currentIndex + 1) % ids.length] : ids[0];
      setRuntimeAgentId(next);
      setRuntimeReply({
        assistant: `Switched to agent ${next}.`,
        agent: next,
        variant: runtimeVariant,
        decision: { workflow: "command" },
        report: { command: "/agent" },
        result: { agent: next },
      });
      return true;
    }

    if (command === "/connect") {
      await openProviderFirstConnectFlow();
      const provider = tokens[1];
      const method = tokens[2];
      if (provider) {
        await selectProviderForFlow(provider);
      }
      if (method) {
        await changeAuthMethodForFlow(method);
      }
      setRuntimeReply({
        assistant: "Provider-first connection flow opened.",
        agent: runtimeAgentId,
        variant: runtimeVariant,
        decision: { workflow: "command" },
        report: { command: "/connect" },
        result: { opened: true, provider: provider ?? null, auth_method: method ?? null }
      });
      return true;
    }

    if (command === "/new") {
      await createRuntimeSession();
      setRuntimeReply({
        assistant: "Created a new runtime session.",
        agent: runtimeAgentId,
        variant: runtimeVariant,
        decision: { workflow: "command" },
        report: { command: "/new" },
        result: { created: true }
      });
      return true;
    }

    if (command === HIDDEN_SUZY_COMMAND) {
      await activateSuzy();
      return true;
    }

    return false;
  };

  const sendRuntimeMessage = async (): Promise<void> => {
    const targetSessionId = activeSessionId || runtimeSession?.session_id;
    if (!targetSessionId) {
      setError("Create runtime session first.");
      return;
    }
    const promptValue = runtimePrompt.trim();
    if (!promptValue) {
      return;
    }
    const commandHandled = await executeRuntimeCommand(promptValue);
    if (commandHandled) {
      setRuntimePrompt("");
      return;
    }

    if (sendingSessionId === targetSessionId) {
      setError("Message send already in progress for this session.");
      return;
    }
    if (Date.now() < sendDebounceUntil) {
      return;
    }
    if (!runtimeCanSendMessage) {
      setError(runtimeCapabilities.sendBlockReason ?? "Session not bound. Bind session before sending.");
      return;
    }

    if (runningRuntimeRuns.length >= MAX_PARALLEL_RUNTIME_RUNS) {
      setError(`Too many runtime tasks in-flight. Wait for completion or interrupt one (max ${MAX_PARALLEL_RUNTIME_RUNS}).`);
      return;
    }

    const selectedModelLabel = selectedConnection
      ? `${selectedConnection.provider}:${selectedConnection.model}`
      : "auto";
    const duplicateRunning = runningRuntimeRuns.find(
      (item) => item.agent === runtimeAgentId && item.model === selectedModelLabel && item.prompt === promptValue,
    );
    if (duplicateRunning) {
      setError("Same prompt is already running for this agent/model.");
      return;
    }

    let outboundPrompt = promptValue;
    if (selectedConnection?.provider === "deepseek" && outboundPrompt.length > MAX_DEEPSEEK_PROMPT_CHARS) {
      outboundPrompt = outboundPrompt.slice(0, MAX_DEEPSEEK_PROMPT_CHARS);
    }

    setError(null);
    setSendDebounceUntil(Date.now() + 400);
    setSendingSessionId(targetSessionId);

    const runId = `run-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const controller = new AbortController();
    runtimeAbortControllers.current.set(runId, controller);
    setRuntimeRuns((prev) => ([
      {
        run_id: runId,
        prompt: outboundPrompt,
        agent: runtimeAgentId,
        model: selectedModelLabel,
        started_at: Date.now(),
        status: "running",
      },
      ...prev,
    ].slice(0, 30)));
    setRuntimePrompt("");
    try {
      const data = await callApi<RuntimeMessageResult>(
        `/runtime/chat/sessions/${targetSessionId}/message`,
        "POST",
        {
          message: outboundPrompt,
          source: "chat",
          agent_id: runtimeAgentId,
          connection_id: runtimeConnectionId || undefined,
          variant: runtimeVariant
        },
        controller.signal,
      );
      if (controller.signal.aborted) {
        return;
      }
      setRuntimeReply({
        ...data,
        assistant: data.assistant && data.assistant.trim().length > 0 ? data.assistant : "Response received.",
      });
      setRuntimeRuns((prev) => prev.map((item) => (
        item.run_id === runId
          ? { ...item, status: "completed" }
          : item
      )));
      await selectRuntimeSession(targetSessionId);
      await loadRuntimeChangeRequests();
      await loadRuntimeSessions();
    } catch (e) {
      const err = e as Error;
      if (err.name === "AbortError") {
        setRuntimeRuns((prev) => prev.map((item) => (
          item.run_id === runId
            ? { ...item, status: "aborted", error: "Interrupted by operator." }
            : item
        )));
      } else {
        setRuntimeRuns((prev) => prev.map((item) => (
          item.run_id === runId
            ? { ...item, status: "failed", error: err.message }
            : item
        )));
        setError(err.message);
      }
    } finally {
      runtimeAbortControllers.current.delete(runId);
      setSendingSessionId("");
    }
  };

  const interruptRuntimeRun = (runId: string): void => {
    const run = runtimeRuns.find((item) => item.run_id === runId);
    if (!run || run.status !== "running") {
      return;
    }
    const controller = runtimeAbortControllers.current.get(runId);
    if (controller) {
      controller.abort();
    }
  };

  const bindRuntimeAgentConnection = async (): Promise<void> => {
    if (!runtimeConnectionId) {
      setError("Select a provider connection first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await callApi<{ binding: JsonObject }>(`/runtime/agents/${runtimeAgentId}/connection`, "POST", {
        connection_id: runtimeConnectionId
      });
      await loadRuntimeProviderStatus();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const activateSuzy = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ active: boolean; message: string }>("/runtime/suzy/activate", "POST", {
        command: "/activateSuzy"
      });
      setSuzyActive(data.active);
      setRuntimeReply({
        assistant: data.message,
        agent: runtimeAgentId,
        variant: runtimeVariant,
        decision: { workflow: "command" },
        report: { command: "/activateSuzy" },
        result: { activated: data.active }
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runSuzySelfEdit = async (): Promise<void> => {
    if (!selfEditPath.trim() || !selfEditFind.trim()) {
      setError("Provide file path and find text for self edit.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<JsonObject>("/runtime/suzy/self-edit", "POST", {
        file_path: selfEditPath,
        find_text: selfEditFind,
        replace_text: selfEditReplace
      });
      setRuntimeReply({
        assistant: "Suzy self edit applied.",
        agent: runtimeAgentId,
        variant: runtimeVariant,
        decision: { workflow: "command" },
        report: { command: "suzy-self-edit" },
        result: data
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadRuntimeChangeRequests = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ change_requests: RuntimeChangeRequest[] }>("/runtime/change-requests", "GET");
      setRuntimeChangeRequests(data.change_requests);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadRuntimeProviderStatus = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ healthy: boolean }>("/runtime/providers/status", "GET");
      setRuntimeProvidersHealthy(data.healthy);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadRuntimeAgentValidation = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<JsonObject>("/runtime/agents/validation", "GET");
      setRuntimeAgentValidation(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadMarketConnectors = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<{ connectors: MarketConnectorStatus[] }>("/market/connectors/status", "GET");
      setMarketConnectors(data.connectors);
      const ibkrData = await callApi<IbkrSessionStatus>("/market/ibkr/session", "GET");
      setIbkrSessionStatus(ibkrData);
      const gatewayResp = await callApi<GatewayChannelsResponse>("/gateway/channels", "GET");
      setGatewayChannels(gatewayResp.channels);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const syncIbkrSession = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<IbkrSessionStatus>("/market/ibkr/session/init", "POST");
      setIbkrSessionStatus(data);
      await loadMarketConnectors();
      await refreshAllData();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const tickleIbkrSession = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<IbkrSessionStatus>("/market/ibkr/tickle", "POST");
      setIbkrSessionStatus(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadNewsFeed = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const selectedSources = newsSourceFilter === "all" ? undefined : [newsSourceFilter];
      const selectedCategories = newsCategoryFilter === "all" ? undefined : [newsCategoryFilter];
      const selectedClasses = newsClassFilter === "all" ? undefined : [newsClassFilter];
      const data = await callApi<NewsFeedResponse>("/news/feed", "POST", {
        symbols: trackedSymbols,
        sources: selectedSources,
        categories: selectedCategories,
        classes: selectedClasses,
        limit: 24,
        focus_mode: feedFocusMode,
      });
      setNewsFeed(data.items);
      setNewsFeedMeta({
        filterRelaxed: Boolean(data.filter_relaxed),
        cachedCount: Number(data.cached_count ?? 0),
        focusMode: data.focus_mode === "focused" ? "focused" : "general",
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadFlatRouterStatus = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<FlatRouterStatus>("/agent-router/status", "GET");
      setFlatRouterStatus(data);
      setFlatRouterEngineInput(asString(data.settings.engine, "openclaw_flat_router_v1"));
      setFlatRouterModeInput(asString(data.settings.routing_mode, "flat"));
      setFlatRouterDefaultAgentInput(asString(data.settings.default_agent, "suzybae"));
      setFlatRouterSkillsProfileInput(asString(data.settings.skills_profile, "openclaw_skeleton"));
      const gateways = Array.isArray(data.settings.enabled_gateways) ? data.settings.enabled_gateways.join(",") : "ibkr_cpapi,telegram,whatsapp";
      setFlatRouterGatewaysInput(gateways);
      await loadOpenClawSettings();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const saveFlatRouterSettings = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const payload = {
        engine: flatRouterEngineInput.trim(),
        routing_mode: flatRouterModeInput.trim(),
        default_agent: flatRouterDefaultAgentInput.trim(),
        skills_profile: flatRouterSkillsProfileInput.trim(),
        enabled_gateways: flatRouterGatewaysInput.split(",").map((item) => item.trim()).filter((item) => item.length > 0),
      };
      const data = await callApi<FlatRouterSettingsResponse>("/agent-router/settings", "POST", payload);
      setFlatRouterStatus((prev) => ({
        settings: data.settings,
        agents: prev?.agents ?? [],
        skills: prev?.skills ?? [],
        providers: prev?.providers ?? {},
        channels: prev?.channels ?? {},
        updated_at: new Date().toISOString(),
      }));
      await loadFlatRouterStatus();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runFlatRouterDecision = async (): Promise<void> => {
    const message = flatRouteInput.trim();
    if (!message) {
      setError("Route message is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<FlatRouteDecision>("/agent-router/route", "POST", { message });
      setFlatRouteDecision(data);
      if (!flatRouterStatus) {
        const statusData = await callApi<FlatRouterStatus>("/agent-router/status", "GET");
        setFlatRouterStatus(statusData);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadWorldMonitorFeed = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const selectedSymbols = parseSymbolCsv(worldMonitorSymbols);
      const data = await callApi<{ items: NewsFeedItem[] }>("/world-monitor/feed", "POST", {
        symbols: selectedSymbols.length ? selectedSymbols : trackedSymbols,
        limit: Math.max(1, Math.min(worldMonitorLimit, 50)),
        focus_mode: worldMonitorFocusMode,
      });
      setWorldMonitorFeed(data.items);
      await loadWorldMonitorSources();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadWorldMonitorSources = async (): Promise<void> => {
    try {
      const data = await callApi<WorldMonitorSourcesResponse>("/world-monitor/sources", "GET");
      setWorldMonitorSources(data.items);
    } catch {
      setWorldMonitorSources([]);
    }
  };

  const loadOpenClawHeartbeat = async (): Promise<void> => {
    try {
      const data = await callApi<OpenClawHeartbeatResponse>("/openclaw/heartbeat", "GET");
      setOpenClawHeartbeat(data);
    } catch {
      setOpenClawHeartbeat(null);
    }
  };

  const loadOpenClawCron = async (): Promise<void> => {
    try {
      const data = await callApi<OpenClawCronResponse>("/openclaw/cron", "GET");
      setOpenClawCron(data);
    } catch {
      setOpenClawCron(null);
    }
  };

  const loadOpenClawSettings = async (): Promise<void> => {
    try {
      const data = await callApi<OpenClawSettingsResponse>("/openclaw/settings", "GET");
      setOpenClawSettings(data);
    } catch {
      setOpenClawSettings(null);
    }
  };

  const loadFinnhubStatus = async (): Promise<void> => {
    try {
      const [status, marketStatus, widgets] = await Promise.all([
        callApi<FinnhubStatusResponse>("/finnhub/status", "GET"),
        callApi<FinnhubMarketStatusResponse>("/finnhub/market-status?exchange=US", "GET"),
        callApi<FinnhubTradingViewWidgetsResponse>(`/finnhub/tradingview/widgets?symbols=${encodeURIComponent(activeWatchlistSymbolsCsv || "AAPL,MSFT,NVDA")}`, "GET"),
      ]);
      setFinnhubStatus(status);
      setFinnhubMarketStatus(marketStatus);
      setFinnhubWidgetConfigs(widgets);
    } catch {
      setFinnhubStatus(null);
      setFinnhubMarketStatus(null);
      setFinnhubWidgetConfigs(null);
    }
  };

  const runFinnhubLookup = async (): Promise<void> => {
    const query = finnhubLookupQuery.trim();
    if (!query) {
      setError("Finnhub lookup query is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const [lookup, news] = await Promise.all([
        callApi<FinnhubLookupResponse>("/finnhub/search", "POST", { query, exchange: "US" }),
        callApi<FinnhubCompanyNewsResponse>("/finnhub/company-news", "POST", { symbol: query.toUpperCase() }),
      ]);
      setFinnhubLookupItems(lookup.items);
      setFinnhubCompanyNews(news.items);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadOpenDataDatasets = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenDataDatasetsResponse>("/open-data/datasets", "POST", {
        query: openDataQuery,
        limit: 12,
      });
      setOpenDataDatasets(data.items);
      setOpenDataOpenbbAvailable(data.openbb_available);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadOpenDataOverview = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenDataOverviewResponse>("/open-data/overview", "POST", {
        symbols: parseSymbolCsv(openDataOverviewSymbols),
        limit: 12,
      });
      setOpenDataOverview(data.items);
      setOpenDataOpenbbAvailable(data.openbb_available);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadOpenDataSeries = async (): Promise<void> => {
    const symbol = openDataSeriesSymbol.trim().toUpperCase();
    if (!symbol) {
      setError("Series symbol is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenDataSeriesResponse>("/open-data/series", "POST", {
        symbol,
        dataset_id: "equity_price_history",
        interval: openDataSeriesInterval,
        limit: Math.max(10, Math.min(openDataSeriesLimit, 300)),
      });
      setOpenDataSeries(data.points);
      setOpenDataSeriesBackend(data.backend);
      setOpenDataOpenbbAvailable(data.openbb_available);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadOpenDataSeriesForSymbol = async (symbol: string): Promise<void> => {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) {
      return;
    }
    const data = await callApi<OpenDataSeriesResponse>("/open-data/series", "POST", {
      symbol: normalized,
      dataset_id: "equity_price_history",
      interval: openDataSeriesInterval,
      limit: Math.max(10, Math.min(openDataSeriesLimit, 300)),
    });
    setOpenDataSeriesSymbol(normalized);
    setOpenDataSeries(data.points);
    setOpenDataSeriesBackend(data.backend);
    setOpenDataOpenbbAvailable(data.openbb_available);
  };

  const searchOpenStock = async (): Promise<void> => {
    const query = openStockQuery.trim();
    if (!query) {
      setError("Stock search query is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenStockSearchResponse>("/open-stock/search", "POST", {
        query,
        limit: 12,
      });
      setOpenStockSearchItems(data.items);
      if (data.items.length) {
        const topSymbols = data.items.slice(0, 5).map((item) => item.symbol).join(",");
        setOpenStockSnapshotSymbols(topSymbols);
        setOpenStockActiveSymbol(data.items[0].symbol);
        await loadOpenStockReference(data.items[0].symbol);
        await loadOpenDataSeriesForSymbol(data.items[0].symbol);
        const snapshot = await callApi<OpenStockSnapshotResponse>("/open-stock/snapshot", "POST", {
          symbols: data.items.slice(0, 5).map((item) => item.symbol),
          limit: 5,
        });
        setOpenStockSnapshotItems(snapshot.items);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadOpenStockCatalog = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenStockCatalogResponse>("/open-stock/catalog", "POST", {
        query: openStockCatalogQuery.trim() || undefined,
        exchange: openStockCatalogExchange,
        stock_type: openStockCatalogType,
        limit: openStockCatalogLimit,
        offset: openStockCatalogOffset,
      });
      setOpenStockCatalogItems(data.items);
      setOpenStockCatalogTotal(data.total);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const openStockCatalogNextPage = async (): Promise<void> => {
    const nextOffset = openStockCatalogOffset + openStockCatalogLimit;
    if (nextOffset >= openStockCatalogTotal) {
      return;
    }
    setOpenStockCatalogOffset(nextOffset);
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenStockCatalogResponse>("/open-stock/catalog", "POST", {
        query: openStockCatalogQuery.trim() || undefined,
        exchange: openStockCatalogExchange,
        stock_type: openStockCatalogType,
        limit: openStockCatalogLimit,
        offset: nextOffset,
      });
      setOpenStockCatalogItems(data.items);
      setOpenStockCatalogTotal(data.total);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const openStockCatalogPrevPage = async (): Promise<void> => {
    const nextOffset = Math.max(0, openStockCatalogOffset - openStockCatalogLimit);
    setOpenStockCatalogOffset(nextOffset);
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenStockCatalogResponse>("/open-stock/catalog", "POST", {
        query: openStockCatalogQuery.trim() || undefined,
        exchange: openStockCatalogExchange,
        stock_type: openStockCatalogType,
        limit: openStockCatalogLimit,
        offset: nextOffset,
      });
      setOpenStockCatalogItems(data.items);
      setOpenStockCatalogTotal(data.total);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadOpenStockSnapshot = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const selectedSymbols = parseSymbolCsv(openStockSnapshotSymbols);
      const data = await callApi<OpenStockSnapshotResponse>("/open-stock/snapshot", "POST", {
        symbols: selectedSymbols,
        limit: 12,
      });
      setOpenStockSnapshotItems(data.items);
      if (data.items.length) {
        setOpenStockActiveSymbol(data.items[0].symbol);
        await loadOpenStockReference(data.items[0].symbol);
        await loadOpenDataSeriesForSymbol(data.items[0].symbol);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadOpenStockReference = async (symbol: string): Promise<void> => {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) {
      return;
    }
    try {
      const data = await callApi<OpenStockReferenceResponse>("/open-stock/reference", "POST", { symbol: normalized });
      setOpenStockReference(data.item);
    } catch {
      setOpenStockReference(null);
    }
  };

  const inspectOpenStockSymbol = async (symbol: string): Promise<void> => {
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<OpenStockSnapshotResponse>("/open-stock/snapshot", "POST", {
        symbols: [normalized],
        limit: 1,
      });
      setOpenStockActiveSymbol(normalized);
      setOpenStockSnapshotSymbols(normalized);
      setOpenStockSnapshotItems(data.items);
      await loadOpenStockReference(normalized);
      await loadOpenDataSeriesForSymbol(normalized);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadMarketCandles = useCallback(async (instrumentId: string): Promise<void> => {
    if (!instrumentId) {
      return;
    }
    try {
      const data = await callApi<MarketCandlesResponse>("/market/candles", "POST", {
        instrument_id: instrumentId,
        interval: "5m",
        range: "1d",
      });
      setMarketCandles(data.candles);
      setMarketCandleSource(data.source);
      setMarketCandleStatus(data.status);
      setMarketCandleSymbol(data.symbol);
    } catch {
      setMarketCandles([]);
      setMarketCandleSource("-");
      setMarketCandleStatus("unavailable");
      setMarketCandleSymbol("-");
    }
  }, []);

  const createWatchlist = (): void => {
    const name = newWatchlistName.trim();
    if (!name) {
      return;
    }
    if (watchlists[name]) {
      return;
    }
    setWatchlists((prev) => ({ ...prev, [name]: [] }));
    setActiveWatchlistId(name);
    setNewWatchlistName("");
  };

  const removeWatchlist = (watchlistId: string): void => {
    if (!watchlists[watchlistId]) {
      return;
    }
    const next = { ...watchlists };
    delete next[watchlistId];
    const keys = Object.keys(next);
    if (!keys.length) {
      setWatchlists(DEFAULT_WATCHLISTS);
      setActiveWatchlistId("core");
      return;
    }
    setWatchlists(next);
    if (!next[activeWatchlistId]) {
      setActiveWatchlistId(keys[0]);
    }
  };

  const addTickerToWatchlist = (): void => {
    const symbol = watchlistTickerInput.trim().toUpperCase();
    if (!symbol || !watchlists[activeWatchlistId]) {
      return;
    }
    setWatchlists((prev) => {
      const current = prev[activeWatchlistId] ?? [];
      if (current.includes(symbol)) {
        return prev;
      }
      return {
        ...prev,
        [activeWatchlistId]: [...current, symbol],
      };
    });
    setWatchlistTickerInput("");
  };

  const removeTickerFromWatchlist = (symbol: string): void => {
    if (!watchlists[activeWatchlistId]) {
      return;
    }
    setWatchlists((prev) => ({
      ...prev,
      [activeWatchlistId]: (prev[activeWatchlistId] ?? []).filter((item) => item !== symbol),
    }));
  };

  useEffect(() => {
    if (!marketQuotes.length) {
      return;
    }
    const selectedExists = marketQuotes.some((item) => item.instrument_id === selectedMarketInstrumentId);
    const target = selectedExists ? selectedMarketInstrumentId : marketQuotes[0].instrument_id;
    if (target !== selectedMarketInstrumentId) {
      setSelectedMarketInstrumentId(target);
    }
    void loadMarketCandles(target);
  }, [loadMarketCandles, marketQuotes, selectedMarketInstrumentId]);

  const refreshAllData = useCallback(async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const selectedSources = newsSourceFilter === "all" ? undefined : [newsSourceFilter];
      const selectedCategories = newsCategoryFilter === "all" ? undefined : [newsCategoryFilter];
      const selectedClasses = newsClassFilter === "all" ? undefined : [newsClassFilter];
      const [
        portfolioResp,
        suggestionsResp,
        changeReqResp,
        quotesResp,
        newsResp,
        worldResp,
        worldSourcesResp,
        flatStatusResp,
        openClawHeartbeatResp,
        openClawCronResp,
        openClawSettingsResp,
        finnhubStatusResp,
        finnhubMarketStatusResp,
        finnhubWidgetResp,
        openDataDatasetsResp,
        openDataOverviewResp,
        openStockCatalogResp,
        openStockSnapshotResp,
        monitorResp,
        ibkrResp,
        gatewayResp,
      ] = await Promise.all([
        callApi<{ portfolio_snapshot: PortfolioSnapshot }>("/portfolio", "GET"),
        callApi<{ suggestions: SuggestionRecord[] }>("/suggestions", "GET"),
        callApi<{ change_requests: RuntimeChangeRequest[] }>("/runtime/change-requests", "GET"),
        callApi<MarketQuotesResponse>("/market/quotes", "POST", { instruments: TOP_INDEX_INSTRUMENTS, focus_mode: feedFocusMode }),
        callApi<NewsFeedResponse>("/news/feed", "POST", { symbols: trackedSymbols, sources: selectedSources, categories: selectedCategories, classes: selectedClasses, limit: 24, focus_mode: feedFocusMode }),
        callApi<{ items: NewsFeedItem[] }>("/world-monitor/feed", "POST", {
          symbols: parseSymbolCsv(worldMonitorSymbols).length ? parseSymbolCsv(worldMonitorSymbols) : trackedSymbols,
          limit: Math.max(1, Math.min(worldMonitorLimit, 50)),
          focus_mode: worldMonitorFocusMode,
        }),
        callApi<WorldMonitorSourcesResponse>("/world-monitor/sources", "GET"),
        callApi<FlatRouterStatus>("/agent-router/status", "GET"),
        callApi<OpenClawHeartbeatResponse>("/openclaw/heartbeat", "GET"),
        callApi<OpenClawCronResponse>("/openclaw/cron", "GET"),
        callApi<OpenClawSettingsResponse>("/openclaw/settings", "GET"),
        callApi<FinnhubStatusResponse>("/finnhub/status", "GET"),
        callApi<FinnhubMarketStatusResponse>("/finnhub/market-status?exchange=US", "GET"),
        callApi<FinnhubTradingViewWidgetsResponse>(`/finnhub/tradingview/widgets?symbols=${encodeURIComponent(activeWatchlistSymbolsCsv || "AAPL,MSFT,NVDA")}`, "GET"),
        callApi<OpenDataDatasetsResponse>("/open-data/datasets", "POST", { query: openDataQuery, limit: 12 }),
        callApi<OpenDataOverviewResponse>("/open-data/overview", "POST", { symbols: trackedSymbols, limit: 8 }),
        callApi<OpenStockCatalogResponse>("/open-stock/catalog", "POST", { query: openStockCatalogQuery || undefined, exchange: openStockCatalogExchange, stock_type: openStockCatalogType, limit: openStockCatalogLimit, offset: openStockCatalogOffset }),
        callApi<OpenStockSnapshotResponse>("/open-stock/snapshot", "POST", { symbols: trackedSymbols, limit: 8 }),
        callApi<JsonObject>("/monitor/refresh-now", "POST"),
        callApi<IbkrSessionStatus>("/market/ibkr/session", "GET"),
        callApi<GatewayChannelsResponse>("/gateway/channels", "GET"),
      ]);
      setPortfolio(portfolioResp.portfolio_snapshot);
      setSuggestions(suggestionsResp.suggestions);
      setRuntimeChangeRequests(changeReqResp.change_requests);
      setMarketQuotes(quotesResp.items);
      setNewsFeed(newsResp.items);
      setNewsFeedMeta({
        filterRelaxed: Boolean(newsResp.filter_relaxed),
        cachedCount: Number(newsResp.cached_count ?? 0),
        focusMode: newsResp.focus_mode === "focused" ? "focused" : "general",
      });
      setWorldMonitorFeed(worldResp.items);
      setWorldMonitorSources(worldSourcesResp.items);
      setFlatRouterStatus(flatStatusResp);
      setOpenClawHeartbeat(openClawHeartbeatResp);
      setOpenClawCron(openClawCronResp);
      setOpenClawSettings(openClawSettingsResp);
      setFinnhubStatus(finnhubStatusResp);
      setFinnhubMarketStatus(finnhubMarketStatusResp);
      setFinnhubWidgetConfigs(finnhubWidgetResp);
      setOpenDataDatasets(openDataDatasetsResp.items);
      setOpenDataOverview(openDataOverviewResp.items);
      setOpenDataOpenbbAvailable(openDataOverviewResp.openbb_available);
      setOpenStockCatalogItems(openStockCatalogResp.items);
      setOpenStockCatalogTotal(openStockCatalogResp.total);
      setOpenStockSnapshotItems(openStockSnapshotResp.items);
      setMonitorStatus(monitorResp);
      setIbkrSessionStatus(ibkrResp);
      setGatewayChannels(gatewayResp.channels);
      setLastUnifiedRefreshAt(new Date().toISOString());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [
    feedFocusMode,
    newsSourceFilter,
    newsCategoryFilter,
    newsClassFilter,
    trackedSymbols,
    openDataQuery,
    activeWatchlistSymbolsCsv,
    openStockCatalogExchange,
    openStockCatalogLimit,
    openStockCatalogOffset,
    openStockCatalogQuery,
    openStockCatalogType,
    worldMonitorFocusMode,
    worldMonitorLimit,
    worldMonitorSymbols,
  ]);

  const handleRuntimeInputKeyDown = (event: { key: string; ctrlKey: boolean; altKey: boolean; shiftKey: boolean; preventDefault: () => void }): void => {
    if (event.key === "Enter" && event.ctrlKey) {
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      void sendRuntimeMessage();
      return;
    }
    if (event.key === "Tab") {
      event.preventDefault();
      cycleRuntimeAgent();
      return;
    }
    if (event.ctrlKey && event.key.toLowerCase() === "t") {
      event.preventDefault();
      cycleRuntimeVariant();
      return;
    }
    if (event.ctrlKey && event.key.toLowerCase() === "m") {
      event.preventDefault();
      setShowCommandPalette(true);
      return;
    }
    if (event.ctrlKey && event.altKey && event.key.toLowerCase() === "p") {
      event.preventDefault();
      setShowRuntimeSettingsPanel(true);
      return;
    }
    if (event.key === "Escape") {
      const latest = [...runtimeRuns].reverse().find((item) => item.status === "running");
      if (latest) {
        event.preventDefault();
        const controller = runtimeAbortControllers.current.get(latest.run_id);
        if (controller) {
          controller.abort();
        }
      }
    }
  };

  const runCommandPaletteAction = async (cmd: string): Promise<void> => {
    if (cmd === "/sessions") {
      openSessionsModal();
      setShowCommandPalette(false);
      return;
    }
    if (cmd === "/connect") {
      await openProviderFirstConnectFlow();
      setShowCommandPalette(false);
      return;
    }
    if (cmd === "/models") {
      setShowProviderFlowModal(true);
      if (selectedProviderId) {
        await loadModelsForFlow();
      } else {
        setConnectionLifecycleState("selecting_provider");
      }
      setShowCommandPalette(false);
      return;
    }
    if (cmd === "/new") {
      await createRuntimeSession();
      setShowCommandPalette(false);
      return;
    }
    if (cmd === "/agent") {
      const ids = runtimeAgents.length ? runtimeAgents.map((item) => item.agent_id) : ["suzybae"];
      const currentIndex = ids.indexOf(runtimeAgentId);
      const next = currentIndex >= 0 ? ids[(currentIndex + 1) % ids.length] : ids[0];
      setRuntimeAgentId(next);
      setShowCommandPalette(false);
      return;
    }
  };

  useEffect(() => {
    const onWindowKeyDown = (event: KeyboardEvent): void => {
      const target = event.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        return;
      }
      if (event.ctrlKey && event.key.toLowerCase() === "m") {
        event.preventDefault();
        setShowCommandPalette(true);
        return;
      }
      if (event.ctrlKey && event.altKey && event.key.toLowerCase() === "p") {
        event.preventDefault();
        setShowRuntimeSettingsPanel(true);
        return;
      }
      if (event.key === "Escape") {
        const latest = [...runtimeRuns].reverse().find((item) => item.status === "running");
        if (latest) {
          event.preventDefault();
          const controller = runtimeAbortControllers.current.get(latest.run_id);
          if (controller) {
            controller.abort();
          }
        }
      }
    };
    window.addEventListener("keydown", onWindowKeyDown);
    return () => window.removeEventListener("keydown", onWindowKeyDown);
  }, [runtimeRuns]);

  useEffect(() => {
    if (!runningRuntimeRuns.length) {
      return;
    }
    const timer = window.setInterval(() => {
      setRuntimePulse((prev) => prev + 1);
    }, 500);
    return () => window.clearInterval(timer);
  }, [runningRuntimeRuns.length]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void refreshAllData();
    }, 60000);
    return () => window.clearInterval(timer);
  }, [refreshAllData]);

  useEffect(() => {
    return () => {
      runtimeAbortControllers.current.forEach((controller) => {
        controller.abort();
      });
      runtimeAbortControllers.current.clear();
    };
  }, []);

  const refreshMonitorStatus = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<JsonObject>("/monitor/status", "GET");
      setMonitorStatus(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadGatewayChannels = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<GatewayChannelsResponse>("/gateway/channels", "GET");
      setGatewayChannels(data.channels);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const sendTelegramGatewayTest = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      await callApi<JsonObject>("/gateway/telegram/test", "POST", { text: "Agentic Portfolio Telegram gateway test" });
      await loadGatewayChannels();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const sendWhatsappGatewayTest = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      await callApi<JsonObject>("/gateway/whatsapp/test", "POST", { text: "Agentic Portfolio WhatsApp gateway test" });
      await loadGatewayChannels();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const enableMonitor = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<JsonObject>("/monitor/enable", "POST", {
        tracked_symbols: trackedSymbols,
        interval_seconds: monitorInterval
      });
      setMonitorStatus(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const disableMonitor = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const data = await callApi<JsonObject>("/monitor/disable", "POST");
      setMonitorStatus(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const runtimeWorkspaceCard = (
    <article className="panel runtime-workspace-panel">
      <h3>SuzyBae Runtime Workspace</h3>
      <p className="muted">Orchestrator: oh-my-opencode-sisyphus</p>
      <p className="muted">Session: {activeSessionId || runtimeSession?.session_id || "-"}</p>
      <p className="muted">Connection Health: {runtimeProvidersHealthy === null ? "unknown" : (runtimeProvidersHealthy ? "healthy" : "degraded")}</p>
      <p className="muted">Connection binding scope: global per agent</p>
      <div className="runtime-transcript" role="log" aria-label="SuzyBae session transcript">
        {runtimeMessages.length ? runtimeMessages.map((item) => (
          <div
            key={item.message_id}
            className={`runtime-msg ${item.role === "user" ? "user" : "reply"} ${highlightMessageId === item.message_id ? "highlight" : ""}`}
          >
            <div className="runtime-msg-head">
              <strong>{item.role === "user" ? "You" : "SuzyBae"}</strong>
              <span>{new Date(item.created_at).toLocaleTimeString()}</span>
            </div>
            <pre className="runtime-msg-body">{item.content}</pre>
            {item.role !== "user" ? (
              <>
                <span className="runtime-meta"><strong>Process:</strong> {runtimeProcessLabel(item.artifact as JsonObject | null)}</span>
                <span className="runtime-meta"><strong>Thinking:</strong> {asString((item.artifact as JsonObject | null)?.thinking)}</span>
                {Array.isArray((item.artifact as JsonObject | null)?.todos) ? (
                  <div className="runtime-todos">
                    <strong>Todos</strong>
                    <ul>
                      {((item.artifact as JsonObject).todos as unknown[]).map((todo) => (
                        <li key={`${item.message_id}-todo-${asString(todo, "todo")}`}>[ ] {asString(todo)}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </>
            ) : null}
          </div>
        )) : <p className="muted">No transcript yet for this session.</p>}
        {runningRuntimeRuns.map((run) => (
          <div key={run.run_id} className="runtime-msg running">
            <div className="runtime-msg-head">
              <strong>{run.agent.toUpperCase()}</strong>
              <span>{Math.floor((Date.now() - run.started_at) / 1000)}s</span>
            </div>
            <pre className="runtime-msg-body">Thinking{".".repeat(runtimeDotCount)} {run.prompt}</pre>
            <span className="runtime-meta"><strong>Process:</strong> agent {run.agent} | model {run.model}</span>
          </div>
        ))}
      </div>
      <textarea
        className="runtime-input-box"
        value={runtimePrompt}
        onChange={(e) => {
          setRuntimePrompt(e.target.value);
        }}
        onKeyDown={handleRuntimeInputKeyDown}
        rows={3}
      />
      <div className="runtime-input-toolbar">
        <div className="runtime-context-badges">
          <span className="runtime-badge">agent:{runtimeAgentId}</span>
          <span className="runtime-badge">provider:{selectedConnection ? selectedConnection.provider : "auto"}</span>
          <span className="runtime-badge">model:{selectedConnection ? selectedConnection.model : "auto"}</span>
          {runtimeVariant !== "default" ? <span className="runtime-badge">variant:{runtimeVariant}</span> : null}
        </div>
        <div className={`runtime-run-indicator ${latestRunningRun ? "running" : "idle"}`}>
          <span>
            {latestRunningRun
              ? `running${".".repeat(runtimeDotCount)} ${latestRunningRun.agent}:${latestRunningRun.model}`
              : "idle"}
          </span>
          {latestRunningRun ? (
            <button type="button" onClick={() => interruptRuntimeRun(latestRunningRun.run_id)}>Interrupt</button>
          ) : null}
        </div>
      </div>
      <div className="action-row runtime-actions">
        <button type="button" onClick={sendRuntimeMessage} disabled={!runtimePrompt.trim() || busy || !runtimeCanSendMessage}>Send Message</button>
        <button
          type="button"
          onClick={() => setShowRuntimeSettingsPanel((prev) => !prev)}
          disabled={busy}
          title="Command settings (Ctrl+Alt+P)"
        >
          Gear
        </button>
        <button type="button" onClick={() => setShowRuntimeConnectionInfo((prev) => !prev)} disabled={busy}>Health</button>
        <button type="button" onClick={() => setShowCommandPalette(true)} disabled={busy}>Command Center</button>
        {runtimeIsProcessing ? <span className="runtime-spinner" /> : <span className="runtime-state-pill">idle</span>}
      </div>
      {showRuntimeSettingsPanel ? (
        <div className="compact-output runtime-settings-panel">
          <p><strong>Command Settings</strong></p>
          <div className="action-row runtime-actions">
            <button type="button" onClick={() => { void openProviderFirstConnectFlow(); }} disabled={busy}>Provider</button>
            <button type="button" onClick={() => { void openModelsModal(); }} disabled={busy || !selectedProviderId}>Load models</button>
            <button type="button" onClick={() => { void bindSelectedFlowSession(); }} disabled={busy || !selectedModelId || connectionLifecycleState === "binding_session"}>Bind session</button>
            <button type="button" onClick={() => { void bindRuntimeAgentConnection(); }} disabled={busy || !runtimeConnectionId}>Bind agent connection</button>
            <button type="button" onClick={() => { void loadRuntimeProviderStatus(); }} disabled={busy}>Provider health</button>
            <button type="button" onClick={() => { void loadRuntimeAgentValidation(); }} disabled={busy}>Agent validation</button>
            <button type="button" onClick={() => { void loadRuntimeChangeRequests(); }} disabled={busy}>Change requests</button>
            <button type="button" onClick={createRuntimeSession} disabled={busy}>New session</button>
            <button type="button" onClick={() => setShowRuntimeSettingsPanel(false)} disabled={busy}>Close</button>
          </div>
        </div>
      ) : null}
      {showRuntimeConnectionInfo ? (
        <div className="compact-output">
          <ConnectionStatus
            provider={selectedProviderId || runtimeStatus.provider || "-"}
            authentication={selectedAuthMethod || "-"}
            model={selectedModelId || runtimeStatus.model || "-"}
            session={activeRuntimeSessionId || "-"}
            state={connectionLifecycleState}
          />
          <p><strong>Agent:</strong> {runtimeReply?.agent ?? runtimeAgentId}</p>
          <p><strong>Variant:</strong> {runtimeReply?.variant ?? runtimeVariant}</p>
          <p><strong>Model:</strong> {selectedConnection ? `${selectedConnection.provider}:${selectedConnection.model}` : "auto"}</p>
          <p><strong>Blocked:</strong> {connectionBlockReason ?? runtimeCapabilities.sendBlockReason ?? "-"}</p>
          <p><strong>Reply:</strong> {runtimeReply?.assistant ?? "-"}</p>
          <p><strong>Thinking:</strong> {asString((runtimeReply?.decision as JsonObject | undefined)?.reason)}</p>
          <p><strong>Provider Health:</strong> {runtimeProvidersHealthy === null ? "-" : (runtimeProvidersHealthy ? "healthy" : "degraded")}</p>
          <p><strong>Agent Validation:</strong> {runtimeAgentValidation ? `${Object.keys(runtimeAgentValidation).length} checks` : "-"}</p>
          <p><strong>Change Requests:</strong> {runtimeChangeRequests.length}</p>
          <p><strong>Route:</strong> {asString(runtimeReply?.decision?.workflow)}</p>
          <ResetConnectionButton
            onReset={() => {
              void disconnectCurrentConnection();
            }}
            onForget={() => {
              void forgetStoredCredentials(selectedProviderId);
            }}
          />
        </div>
      ) : null}
      {suzyActive ? (
        <div className="compact-output">
          <p><strong>Suzy Self Edit</strong></p>
          <input value={selfEditPath} onChange={(e) => setSelfEditPath(e.target.value)} placeholder="File path" />
          <input value={selfEditFind} onChange={(e) => setSelfEditFind(e.target.value)} placeholder="Find text" />
          <input value={selfEditReplace} onChange={(e) => setSelfEditReplace(e.target.value)} placeholder="Replace text" />
          <div className="action-row">
            <button type="button" onClick={runSuzySelfEdit} disabled={busy}>Run Self Edit</button>
          </div>
        </div>
      ) : null}
      <div className="runtime-hints">
        <span>`Tab` switch agent</span>
        <span>`Ctrl+T` switch variant</span>
        <span>`Ctrl+M` commands</span>
        <span>`Ctrl+Alt+P` settings</span>
        <span>`Ctrl+Enter` newline</span>
        <span>`Esc` interrupt latest run</span>
        <span>Commands: {RUNTIME_PUBLIC_COMMANDS.join(" ")}</span>
      </div>
      <div className="runtime-runner-strip">
        {runtimeRuns.length ? runtimeRuns.slice(0, 6).map((run) => (
          <div key={`runner-${run.run_id}`} className={`runtime-runner-item ${run.status}`}>
            <span>[{run.agent}, {run.model}] {run.status === "running" ? `running${".".repeat(runtimeDotCount)}` : run.status}</span>
            {run.status === "running" ? (
              <button type="button" onClick={() => interruptRuntimeRun(run.run_id)}>Interrupt</button>
            ) : null}
            {run.status === "failed" ? <span>{run.error}</span> : null}
            {run.status === "aborted" ? <span>{run.error ?? "Interrupted."}</span> : null}
          </div>
        )) : <div className="runtime-runner-item idle"><span>No active runtime tasks.</span></div>}
      </div>
    </article>
  );

  const indexTicker = marketQuotes;
  const portfolioSymbols = new Set((portfolio?.positions ?? []).map((position) => position.symbol.toUpperCase()));
  const selectedTradeAccountScope: Exclude<PortfolioAccountScope, "overall"> = selectedBroker === "ibkr_paper" ? "ibkr" : "mt5";
  const quoteBySymbol = new Map(marketQuotes.map((item) => [item.symbol.toUpperCase(), item]));
  const activeWatchlistSymbols = activeWatchlistSymbolsMemo;
  const watchlistRows = activeWatchlistSymbols
    .map((symbol) => quoteBySymbol.get(symbol.toUpperCase()))
    .filter((item): item is MarketQuoteItem => Boolean(item));
  const watchlistNews = newsFeed.filter((item) => activeWatchlistSymbols.includes(item.symbol.toUpperCase())).slice(0, 6);
  const missingWatchlistSymbols = activeWatchlistSymbols.filter((symbol) => !quoteBySymbol.has(symbol.toUpperCase()));
  const topPortfolioRows = [...marketQuotes]
    .filter((item) => portfolioSymbols.size === 0 || portfolioSymbols.has(item.symbol.toUpperCase()))
    .sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct))
    .slice(0, 4);
  const overviewAlerts = [
    ...suggestions.slice(0, 3).map((item) => ({
      id: item.suggestion_id,
      title: asString(item.payload.title, "Action required"),
      summary: `Status: ${item.status}.`,
      tab: "Trade",
    })),
    ...runtimeChangeRequests.slice(0, 3).map((item) => ({
      id: item.change_id,
      title: item.summary,
      summary: `Change request: ${item.status}`,
      tab: "Research",
    })),
  ].slice(0, 6);
  const impactingNews = newsFeed.filter((item) => portfolioSymbols.has(item.symbol.toUpperCase())).slice(0, 3);
  const allHoldings = breakdown?.holdings ?? [];
  const scopedHoldings = allHoldings.filter((item) => {
    if (portfolioAccountScope === "overall") {
      return true;
    }
    return mapSymbolToAccountScope(asString(item.symbol, "")) === portfolioAccountScope;
  });
  const totalHoldingMarketValue = allHoldings.reduce((acc, item) => acc + asNumber(item.market_value), 0);
  const scopedHoldingMarketValue = scopedHoldings.reduce((acc, item) => acc + asNumber(item.market_value), 0);
  const scopedCash = portfolioAccountScope === "overall"
    ? (portfolio?.cash ?? 0)
    : (portfolio?.cash ?? 0) * (totalHoldingMarketValue > 0 ? scopedHoldingMarketValue / totalHoldingMarketValue : 0.5);
  const activeTradeHoldings = allHoldings.filter(
    (item) => mapSymbolToAccountScope(asString(item.symbol, "")) === selectedTradeAccountScope,
  );
  const integrityIssues: string[] = [];
  if (missingWatchlistSymbols.length > 0) {
    integrityIssues.push(`watchlist symbols missing live quotes: ${missingWatchlistSymbols.join(", ")}`);
  }
  if (portfolioAccountScope !== selectedTradeAccountScope) {
    integrityIssues.push("portfolio account scope is out of sync with selected trade account");
  }
  const integrityStatus = integrityIssues.length === 0 ? "healthy" : "mismatch";
  const monitorFlashOn = runtimePulse % 2 === 0;

  const openInstrumentChart = (instrumentId: string): void => {
    setSelectedMarketInstrumentId(instrumentId);
    void loadMarketCandles(instrumentId);
    setActiveNavTab("Overview");
  };

  const chartCandles = marketCandles.slice(-48);
  const chartHigh = chartCandles.length ? Math.max(...chartCandles.map((item) => item.high)) : 0;
  const chartLow = chartCandles.length ? Math.min(...chartCandles.map((item) => item.low)) : 0;
  const chartRangeValue = chartHigh - chartLow || 1;

  return (
    <main className={`screen ${darkMode ? "theme-dark" : "theme-light"}`}>
      <section className="ticker-strip">
        {indexTicker.length > 0 ? (
          indexTicker.map((item) => (
            <a
              key={item.instrument_id}
              className="ticker-item ticker-link"
              href={item.quote_url}
              target="_blank"
              rel="noreferrer"
              onClick={(event) => {
                event.preventDefault();
                openInstrumentChart(item.instrument_id);
              }}
              title={`Source: ${item.source_label} | status: ${item.status} | as of: ${new Date(item.as_of_ts).toLocaleString()}`}
            >
              <strong>{item.name}</strong>
              <span>{formatQuoteValue(item.value, item.currency)}</span>
              <span className={item.change_pct >= 0 ? "pnl-up" : "pnl-down"}>{formatQuoteChange(item.change_pct)}</span>
            </a>
          ))
        ) : (
          <span className="ticker-item">Loading live index strip...</span>
        )}
      </section>

      <header className="topbar">
        <button type="button" className="brand brand-btn" onClick={() => setActiveNavTab("Overview")}>Portfolio Desk</button>
        <nav className="main-nav">
          {(["Portfolio", "Trade", "Research", "Performance"] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              className={activeNavTab === tab ? "nav-btn active" : "nav-btn"}
              onClick={() => setActiveNavTab(tab)}
            >
              {tab}
            </button>
          ))}
        </nav>
        <div className="action-row">
          <span className="muted">Page: {activeNavTab}</span>
          <span className="muted">Refresh: {lastUnifiedRefreshAt ? new Date(lastUnifiedRefreshAt).toLocaleTimeString() : "not yet"}</span>
          <button type="button" className="nav-btn" onClick={() => { void refreshAllData(); }} disabled={busy}>Refresh All</button>
          <button type="button" className="nav-btn" onClick={() => setDarkMode((prev) => !prev)}>
            {darkMode ? "Light Mode" : "Dark Mode"}
          </button>
          <button type="button" className="trade-btn" onClick={submitPaper} disabled={busy}>Trade</button>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar panel">
          <h2>All Accounts</h2>
          <p className="muted">Primary risk profile: {riskProfile}</p>
          <div className="metric-list">
            <div><span>Equity</span><strong>{portfolio ? usd(portfolio.equity) : "-"}</strong></div>
            <div><span>Cash</span><strong>{portfolio ? usd(portfolio.cash) : "-"}</strong></div>
            <div><span>Daily P&L</span><strong>{portfolio ? usd(portfolio.daily_pnl) : "-"}</strong></div>
            <div><span>Drawdown</span><strong>{portfolio ? toFixedPercent(portfolio.drawdown) : "-"}</strong></div>
          </div>

          <label htmlFor="symbols">Tracked symbols</label>
          <input id="symbols" value={symbols} onChange={(e) => setSymbols(e.target.value)} placeholder="AAPL,MSFT,NVDA" />

          <label htmlFor="risk">Risk profile</label>
          <select id="risk" value={riskProfile} onChange={(e) => setRiskProfile(e.target.value as RiskProfile)}>
            <option value="conservative">Conservative</option>
            <option value="neutral">Neutral</option>
            <option value="aggressive">Aggressive</option>
          </select>

          <label htmlFor="broker">Paper broker</label>
          <select id="broker" value={selectedBroker} onChange={(e) => setSelectedBroker(e.target.value as BrokerType)}>
            {brokers.length > 0 ? brokers.map((broker) => (
              <option key={broker.broker} value={broker.broker}>{broker.broker}</option>
            )) : (
              <>
                <option value="ibkr_paper">ibkr_paper</option>
                <option value="mt5_paper">mt5_paper</option>
              </>
            )}
          </select>

          <div className="stack-actions">
            <button type="button" onClick={runStartup} disabled={busy}>Startup Refresh + Report</button>
            <button type="button" onClick={refreshPortfolio} disabled={busy}>Refresh Portfolio</button>
            <button type="button" onClick={loadSuggestions} disabled={busy}>Load Suggestions</button>
            <button type="button" onClick={loadBreakdown} disabled={busy}>Run Breakdown</button>
            <button type="button" onClick={loadConsultantBrief} disabled={busy}>Run Consultant Brief</button>
            <button type="button" onClick={runDailyCycle} disabled={busy}>Run Daily Cycle</button>
            <button type="button" onClick={createRuntimeSession} disabled={busy}>New Runtime Session</button>
            <button type="button" onClick={() => setChatDocked((prev) => !prev)} disabled={busy}>{chatDocked ? "Undock SuzyBae" : "Dock SuzyBae"}</button>
            <button type="button" onClick={() => setChatMinimized((prev) => !prev)} disabled={busy}>{chatMinimized ? "Expand SuzyBae" : "Minimize SuzyBae"}</button>
          </div>
          <p className="muted">
            Runtime session: {runtimeSession ? runtimeSession.session_id : "not created"}
          </p>
        </aside>

        <section className="main-area">
          {activeNavTab === "Overview" ? (
            <>
              <article className="panel" id="overview-page">
                <div className="title-row">
                  <h1>Your Portfolio</h1>
                  <button type="button" onClick={() => { void refreshAllData(); }} disabled={busy}>Refresh</button>
                </div>
                <div className="metric-list">
                  <div><span>Account Focus</span><strong>Primary</strong></div>
                  <div><span>Equity</span><strong>{portfolio ? usd(portfolio.equity) : "-"}</strong></div>
                  <div><span>Cash</span><strong>{portfolio ? usd(portfolio.cash) : "-"}</strong></div>
                  <div><span>Total Exposure</span><strong>{portfolio ? usd(Math.max(0, portfolio.equity - portfolio.cash)) : "-"}</strong></div>
                </div>
                <div className="action-row">
                  <button type="button" className={chartMode === "value" ? "tab active" : "tab"} onClick={() => setChartMode("value")}>Value</button>
                  <button type="button" className={chartMode === "performance" ? "tab active" : "tab"} onClick={() => setChartMode("performance")}>Performance</button>
                </div>
                <div className="action-row">
                  {(["1W", "MTD", "YTD", "1Y", "ALL"] as const).map((range) => (
                    <button key={range} type="button" className={chartRange === range ? "tab active" : "tab"} onClick={() => setChartRange(range)}>{range}</button>
                  ))}
                  <button type="button" onClick={loadBreakdown} disabled={busy}>Refresh Chart Data</button>
                </div>
                <p className="muted">
                  {breakdown?.nav_series?.length
                    ? `Mode ${chartMode} | ${chartRange} | latest ${usd(breakdown.nav_series[breakdown.nav_series.length - 1].nav)}`
                    : "Chart data not loaded yet."}
                </p>
              </article>

              <article className="panel">
                <h3>Selected Instrument Candlestick</h3>
                <p className="muted">
                  Instrument: {marketCandleSymbol} | source: {marketCandleSource} | status: {marketCandleStatus}
                </p>
                <div className="candle-chart" role="img" aria-label={`Candlestick chart for ${marketCandleSymbol}`}>
                  {chartCandles.length ? chartCandles.map((candle) => {
                    const wickTop = ((chartHigh - candle.high) / chartRangeValue) * 100;
                    const wickHeight = Math.max(2, ((candle.high - candle.low) / chartRangeValue) * 100);
                    const bodyTop = ((chartHigh - Math.max(candle.open, candle.close)) / chartRangeValue) * 100;
                    const bodyHeight = Math.max(2, (Math.abs(candle.close - candle.open) / chartRangeValue) * 100);
                    const up = candle.close >= candle.open;
                    return (
                      <div key={candle.ts} className="candle-item" title={`${new Date(candle.ts).toLocaleString()} O:${candle.open.toFixed(2)} H:${candle.high.toFixed(2)} L:${candle.low.toFixed(2)} C:${candle.close.toFixed(2)}`}>
                        <span className="candle-wick" style={{ top: `${wickTop}%`, height: `${wickHeight}%` }} />
                        <span className={up ? "candle-body up" : "candle-body down"} style={{ top: `${bodyTop}%`, height: `${bodyHeight}%` }} />
                      </div>
                    );
                  }) : <p className="muted">No candle data available for selected instrument.</p>}
                </div>
              </article>

              <article className="panel">
                <h3>Your Dashboard</h3>
                <div className="operator-grid">
                  <article className="panel">
                    <h3>For You</h3>
                    <div className="list-box">
                      {overviewAlerts.length ? overviewAlerts.map((item) => (
                        <button key={item.id} type="button" className="list-item" onClick={() => setActiveNavTab(item.tab)}>
                          <strong>{item.title}</strong>
                          <span>{item.summary}</span>
                        </button>
                      )) : <p className="muted">No pending alerts.</p>}
                      {impactingNews.length ? impactingNews.map((item) => (
                        <button key={`impact-${item.news_id}`} type="button" className="list-item" onClick={() => setActiveNavTab("Research")}>
                          <strong>Portfolio News: {item.symbol}</strong>
                          <span>{item.title}</span>
                        </button>
                      )) : null}
                    </div>
                  </article>
                  <article className="panel">
                    <h3>Market Overview</h3>
                    <div className="list-box">
                      {newsFeed.slice(0, 4).map((item) => (
                        <a key={`overview-news-${item.news_id}`} className="list-item" href={item.url} target="_blank" rel="noreferrer">
                          <div>
                            <strong>{item.title}</strong>
                            <span>{item.summary}</span>
                          </div>
                          {item.thumbnail_url ? <img className="news-thumb" src={item.thumbnail_url} alt={item.source} /> : null}
                        </a>
                      ))}
                    </div>
                  </article>
                  <article className="panel">
                    <h3>Top Portfolio Positions</h3>
                    <div className="list-box">
                      {topPortfolioRows.map((item) => (
                        <a
                          key={`top-${item.instrument_id}`}
                          className={`list-item position-row ${item.change_pct >= 0 ? "gain" : "loss"}`}
                          href={item.quote_url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(event) => {
                            event.preventDefault();
                            openInstrumentChart(item.instrument_id);
                          }}
                        >
                          <div>
                            <strong>{item.symbol}</strong>
                            <span>{formatQuoteValue(item.value, item.currency)}</span>
                            <span className={item.change_pct >= 0 ? "pnl-up" : "pnl-down"}>{formatQuoteChange(item.change_pct)}</span>
                          </div>
                          <div className="move-bar-track" aria-hidden="true">
                            <div
                              className={item.change_pct >= 0 ? "move-bar-fill up" : "move-bar-fill down"}
                              style={{ width: `${quoteMoveBarWidth(item.change_pct)}%` }}
                            />
                          </div>
                        </a>
                      ))}
                    </div>
                  </article>
                  <article className="panel">
                    <h3>Watchlist</h3>
                    <div className="action-row">
                      <select value={activeWatchlistId} onChange={(event) => setActiveWatchlistId(event.target.value)}>
                        {Object.keys(watchlists).map((watchlistId) => (
                          <option key={watchlistId} value={watchlistId}>{watchlistId}</option>
                        ))}
                      </select>
                      <input
                        value={newWatchlistName}
                        onChange={(event) => setNewWatchlistName(event.target.value)}
                        placeholder="New watchlist"
                      />
                      <button type="button" onClick={createWatchlist} disabled={busy}>Create</button>
                      <button
                        type="button"
                        onClick={() => removeWatchlist(activeWatchlistId)}
                        disabled={busy || Object.keys(watchlists).length <= 1}
                      >
                        Remove List
                      </button>
                    </div>
                    <div className="action-row">
                      <input
                        value={watchlistTickerInput}
                        onChange={(event) => setWatchlistTickerInput(event.target.value)}
                        placeholder="Add ticker (e.g. AAPL)"
                      />
                      <button type="button" onClick={addTickerToWatchlist} disabled={busy}>Add Ticker</button>
                    </div>
                    <div className="list-box">
                      {activeWatchlistSymbols.length ? activeWatchlistSymbols.map((symbol) => {
                        const quote = quoteBySymbol.get(symbol.toUpperCase());
                        if (!quote) {
                          return (
                            <div key={`watch-missing-${symbol}`} className="list-item">
                              <div>
                                <strong>{symbol}</strong>
                                <span className="muted">No live quote in current feed.</span>
                              </div>
                              <button type="button" onClick={() => removeTickerFromWatchlist(symbol)} disabled={busy}>Remove</button>
                            </div>
                          );
                        }
                        return (
                          <div key={`watch-${quote.instrument_id}`} className="list-item">
                            <div>
                              <strong>{quote.name}</strong>
                              <span>{formatQuoteValue(quote.value, quote.currency)}</span>
                              <span className={quote.change_pct >= 0 ? "pnl-up" : "pnl-down"}>{formatQuoteChange(quote.change_pct)}</span>
                            </div>
                            <div className="action-row">
                              <button type="button" onClick={() => openInstrumentChart(quote.instrument_id)} disabled={busy}>Open</button>
                              <button type="button" onClick={() => removeTickerFromWatchlist(symbol)} disabled={busy}>Remove</button>
                            </div>
                          </div>
                        );
                      }) : <p className="muted">No tickers in this watchlist.</p>}
                    </div>
                  </article>
                </div>
              </article>
            </>
          ) : null}

          {activeNavTab === "Portfolio" ? (
            <>
              <div className="title-row" id="portfolio-page">
                <h1>Portfolio Page</h1>
                <div className="tabs">
                  {(["Positions", "Balances", "Breakdown"] as const).map((tab) => (
                    <button key={tab} type="button" className={activeAccountTab === tab ? "tab active" : "tab"} onClick={() => setActiveAccountTab(tab)}>{tab}</button>
                  ))}
                </div>
              </div>
              <article className="panel">
                <h3>Account Scope</h3>
                <div className="action-row">
                  <button type="button" className={portfolioAccountScope === "overall" ? "tab active" : "tab"} onClick={() => setPortfolioAccountScope("overall")}>Overall</button>
                  <button type="button" className={portfolioAccountScope === "ibkr" ? "tab active" : "tab"} onClick={() => setPortfolioAccountScope("ibkr")}>IBKR Paper</button>
                  <button type="button" className={portfolioAccountScope === "mt5" ? "tab active" : "tab"} onClick={() => setPortfolioAccountScope("mt5")}>MT5 Paper</button>
                </div>
                <p className="muted">Scope: {portfolioAccountScope === "overall" ? "All accounts" : `${portfolioAccountScope.toUpperCase()} account`}.</p>
              </article>
              {activeAccountTab === "Positions" ? (
                <article className="panel">
                  <h3>Your Holdings</h3>
                  <table className="holdings-table">
                    <thead>
                      <tr><th>Instrument</th><th>Account</th><th>Position</th><th>Last</th><th>Cost Basis</th><th>Market Value</th><th>Unrealized P&L</th></tr>
                    </thead>
                    <tbody>
                      {scopedHoldings.length ? scopedHoldings.map((item) => {
                        const symbol = asString(item.symbol);
                        const qty = asNumber(item.quantity);
                        const last = asNumber(item.last_price);
                        const avgCost = asNumber(item.avg_cost);
                        const marketValue = asNumber(item.market_value);
                        const unrealized = asNumber(item.unrealized_pnl);
                        const account = mapSymbolToAccountScope(symbol);
                        return <tr key={`${portfolioAccountScope}-${symbol}`}><td>{symbol}</td><td>{account.toUpperCase()}</td><td>{qty.toFixed(2)}</td><td>{usd(last)}</td><td>{usd(avgCost)}</td><td>{usd(marketValue)}</td><td className={unrealized >= 0 ? "pnl-up" : "pnl-down"}>{usd(unrealized)}</td></tr>;
                      }) : <tr><td colSpan={7} className="empty-row">No positions loaded for this account scope.</td></tr>}
                    </tbody>
                  </table>
                </article>
              ) : null}
              {activeAccountTab === "Balances" ? (
                <article className="panel">
                  <h3>Cash Holdings</h3>
                  <table className="cash-table">
                    <tbody>
                      <tr><td>USD (base)</td><td>{usd(scopedCash)}</td></tr>
                      <tr><td>Scope Equity</td><td>{usd(scopedCash + scopedHoldingMarketValue)}</td></tr>
                    </tbody>
                  </table>
                </article>
              ) : null}
              {activeAccountTab === "Breakdown" ? (
                <article className="panel">
                  <h3>Scope Breakdown</h3>
                  <div className="compact-output">
                    <p><strong>Positions:</strong> {scopedHoldings.length}</p>
                    <p><strong>Scoped Holdings Value:</strong> {usd(scopedHoldingMarketValue)}</p>
                    <p><strong>Scoped Cash:</strong> {usd(scopedCash)}</p>
                    <p><strong>Scoped Equity:</strong> {usd(scopedCash + scopedHoldingMarketValue)}</p>
                  </div>
                </article>
              ) : null}
            </>
          ) : null}

          {activeNavTab === "Trade" ? (
            <div className="operator-grid" id="trade-page">
              <article className="panel">
                <h3>Trade Lane</h3>
                <div className="action-row">
                  <label htmlFor="trade-account">Active Trade Account</label>
                  <select id="trade-account" value={selectedBroker} onChange={(e) => setSelectedBroker(e.target.value as BrokerType)}>
                    {brokers.length > 0 ? brokers.map((broker) => (
                      <option key={`trade-${broker.broker}`} value={broker.broker}>{broker.broker}</option>
                    )) : (
                      <>
                        <option value="ibkr_paper">ibkr_paper</option>
                        <option value="mt5_paper">mt5_paper</option>
                      </>
                    )}
                  </select>
                  <span className={integrityStatus === "healthy" ? "watchlist-integrity ok" : "watchlist-integrity mismatch"}>
                    Integrity: {integrityStatus === "healthy" ? "aligned" : "mismatch"}
                  </span>
                </div>
                <div className="stack-actions">
                  <button type="button" onClick={runTradeLane} disabled={busy}>Run Trade Lane</button>
                  <button type="button" onClick={submitPaper} disabled={busy}>Submit Paper Order</button>
                </div>
                {tradeRun ? <div className="compact-output"><p><strong>Run:</strong> {tradeRun.run_id}</p><p><strong>Symbol:</strong> {asString(tradeRun.proposal.symbol)}</p><p><strong>Side:</strong> {asString(tradeRun.proposal.side)}</p><p><strong>Expected Return:</strong> {toFixedPercent(asNumber(tradeRun.simulation.expected_return_pct))}</p></div> : null}
              </article>
              <article className="panel">
                <h3>Trading Watchlist (Shared)</h3>
                <p className="muted">Watchlist: {activeWatchlistId} | Symbols: {activeWatchlistSymbols.join(", ") || "-"}</p>
                <div className="list-box">
                  {watchlistRows.length ? watchlistRows.map((item) => (
                    <button
                      key={`trade-watch-${item.instrument_id}`}
                      type="button"
                      className="list-item"
                      onClick={() => {
                        setSymbols(item.symbol);
                        openInstrumentChart(item.instrument_id);
                      }}
                    >
                      <div>
                        <strong>{item.symbol}</strong>
                        <span>{formatQuoteValue(item.value, item.currency)}</span>
                      </div>
                      <span className={item.change_pct >= 0 ? "pnl-up" : "pnl-down"}>{formatQuoteChange(item.change_pct)}</span>
                    </button>
                  )) : <p className="muted">No quoted symbols from current watchlist.</p>}
                </div>
                {integrityIssues.length ? (
                  <div className="compact-output">
                    <p><strong>Integrity Check</strong></p>
                    {integrityIssues.map((issue) => (<p key={issue}>{issue}</p>))}
                  </div>
                ) : <p className="muted">Cross-validation passed: watchlist, account scope, and trade context are aligned.</p>}
              </article>
              <article className="panel">
                <h3>Active Account Holdings</h3>
                <p className="muted">Account scope: {selectedTradeAccountScope.toUpperCase()}</p>
                <table className="holdings-table">
                  <thead>
                    <tr><th>Instrument</th><th>Position</th><th>Last</th><th>Market Value</th><th>Unrealized P&L</th></tr>
                  </thead>
                  <tbody>
                    {activeTradeHoldings.length ? activeTradeHoldings.map((item) => {
                      const symbol = asString(item.symbol);
                      const qty = asNumber(item.quantity);
                      const last = asNumber(item.last_price);
                      const marketValue = asNumber(item.market_value);
                      const unrealized = asNumber(item.unrealized_pnl);
                      return (
                        <tr key={`trade-holding-${selectedTradeAccountScope}-${symbol}`}>
                          <td>{symbol}</td>
                          <td>{qty.toFixed(2)}</td>
                          <td>{usd(last)}</td>
                          <td>{usd(marketValue)}</td>
                          <td className={unrealized >= 0 ? "pnl-up" : "pnl-down"}>{usd(unrealized)}</td>
                        </tr>
                      );
                    }) : <tr><td colSpan={5} className="empty-row">No holdings mapped to active trade account.</td></tr>}
                  </tbody>
                </table>
              </article>
              <article className="panel">
                <h3>Execution Lifecycle</h3>
                <p className="muted">Order ID: {activeOrderId || "-"}</p>
                <div className="action-row">
                  <button type="button" onClick={fetchOrderStatus} disabled={busy}>Status</button>
                  <button type="button" onClick={fetchOrderFills} disabled={busy}>Fills</button>
                  <button type="button" onClick={fetchOrderEvents} disabled={busy}>Events</button>
                  <button type="button" onClick={cancelOrder} disabled={busy}>Cancel</button>
                  <button type="button" onClick={reconcileOrders} disabled={busy}>Reconcile</button>
                </div>
                <div className="compact-output"><p><strong>Receipt:</strong> {receipt ? `${receipt.order_id} (${receipt.status})` : "-"}</p><p><strong>Status:</strong> {orderStatus ? `${orderStatus.status} @ ${orderStatus.updated_at}` : "-"}</p><p><strong>Fills:</strong> {orderFills.length}</p><p><strong>Events:</strong> {orderEvents.length}</p></div>
              </article>
              <article className="panel">
                <h3>Suggestions</h3>
                <div className="list-box">{suggestions.length ? suggestions.slice(0, 5).map((item) => (<div key={item.suggestion_id} className="list-item"><strong>{asString(item.payload.title, item.suggestion_id)}</strong><span>{item.status}</span></div>)) : <p className="muted">No suggestions loaded.</p>}</div>
              </article>
              <article className="panel">
                <h3>Run Artifacts</h3>
                <div className="artifact-actions">
                  <input value={runIdInput} onChange={(e) => setRunIdInput(e.target.value)} placeholder="Run ID" />
                  <button type="button" onClick={loadArtifacts} disabled={busy}>Load Artifacts</button>
                </div>
                <p className="muted">Artifacts loaded: {artifacts?.artifacts.length ?? 0}</p>
              </article>
            </div>
          ) : null}

          {activeNavTab === "Research" ? (
            <div className="operator-grid" id="research-page">
              <article className="panel">
                <h3>Research Desk</h3>
                <label htmlFor="researchQuery">Research prompt</label>
                <textarea id="researchQuery" value={researchQuery} onChange={(e) => setResearchQuery(e.target.value)} rows={3} />
                <button type="button" onClick={runResearch} disabled={busy}>Run Research</button>
                {research ? <div className="compact-output"><p><strong>Backend:</strong> {research.backend}</p><p><strong>Answer:</strong> {research.answer}</p></div> : null}
              </article>
              <article className="panel">
                <h3>Market Connections</h3>
                <div className="action-row">
                  <button type="button" onClick={loadMarketConnectors} disabled={busy}>Refresh Connections</button>
                  <button type="button" onClick={syncIbkrSession} disabled={busy}>Sync IBKR Login</button>
                  <button type="button" onClick={tickleIbkrSession} disabled={busy}>IBKR Tickle</button>
                  {ibkrSessionStatus?.login_url ? (
                    <a href={ibkrSessionStatus.login_url} target="_blank" rel="noreferrer">Open Gateway</a>
                  ) : null}
                </div>
                {ibkrSessionStatus ? (
                  <div className="compact-output">
                    <p><strong>IBKR Session:</strong> {ibkrSessionStatus.status}</p>
                    <p><strong>Authenticated:</strong> {String(ibkrSessionStatus.authenticated)} | <strong>Connected:</strong> {String(ibkrSessionStatus.connected)}</p>
                    <p><strong>Next Action:</strong> {ibkrSessionStatus.next_action ?? "-"}</p>
                    <p><strong>Hint:</strong> {ibkrSessionStatus.hint ?? ibkrSessionStatus.message ?? "-"}</p>
                    <p><strong>Updated:</strong> {ibkrSessionStatus.updated_at ? new Date(ibkrSessionStatus.updated_at).toLocaleString() : "-"}</p>
                  </div>
                ) : null}
                <div className="list-box">{marketConnectors.length ? marketConnectors.map((item) => (<div key={item.source} className="list-item"><strong>{item.label}</strong><span>{item.status} | {item.mode}</span></div>)) : <p className="muted">No connector status loaded.</p>}</div>
              </article>
              <article className="panel">
                <h3>News Feed</h3>
                <div className="action-row">
                  <select value={feedFocusMode} onChange={(event) => setFeedFocusMode(event.target.value as "general" | "focused")}> 
                    <option value="general">General Feed</option>
                    <option value="focused">User Focused Feed</option>
                  </select>
                  <select value={newsSourceFilter} onChange={(event) => setNewsSourceFilter(event.target.value)}>
                    <option value="all">All sources</option>
                    <option value="yahoo_finance">Yahoo Finance</option>
                    <option value="investing_com">Investing.com</option>
                    <option value="reuters">Reuters</option>
                    <option value="worldmonitor">World Monitor</option>
                    <option value="ibkr">IBKR</option>
                    <option value="tradingview">TradingView</option>
                  </select>
                  <select value={newsCategoryFilter} onChange={(event) => setNewsCategoryFilter(event.target.value)}>
                    <option value="all">All financial categories</option>
                    <option value="stock_markets">Stock Markets</option>
                    <option value="earnings">Earnings</option>
                    <option value="analyst_ratings">Analyst Ratings</option>
                    <option value="transcripts">Transcripts</option>
                    <option value="cryptocurrency">Cryptocurrency</option>
                    <option value="commodities">Commodities</option>
                    <option value="currencies">Currencies</option>
                    <option value="economy">Economy</option>
                    <option value="economic_indicators">Economic Indicators</option>
                    <option value="breaking_news">Breaking News</option>
                  </select>
                  <select value={newsClassFilter} onChange={(event) => setNewsClassFilter(event.target.value)}>
                    <option value="all">All classes</option>
                    <option value="latest">Latest</option>
                    <option value="most_popular">Most Popular</option>
                    <option value="world">World</option>
                    <option value="politics">Politics</option>
                    <option value="company_news">Company News</option>
                    <option value="insider_trading_news">Insider Trading News</option>
                  </select>
                  <button type="button" onClick={loadNewsFeed} disabled={busy}>Refresh News</button>
                </div>
                <p className="muted">Focus: {newsFeedMeta.focusMode} | cached items: {newsFeedMeta.cachedCount} | filter relaxed: {String(newsFeedMeta.filterRelaxed)}</p>
                <div className="list-box">{newsFeed.length ? newsFeed.slice(0, 18).map((item) => (<a key={item.news_id} className="list-item" href={item.url} target="_blank" rel="noreferrer"><div><strong>{item.symbol} | {item.source}</strong><p className="muted">{item.news_category ?? "stock_markets"} | {item.news_class ?? "latest"}</p><p className="muted">{item.title}</p><p className="muted">{item.summary}</p></div>{item.thumbnail_url ? <img className="news-thumb" src={item.thumbnail_url} alt={item.source} /> : null}</a>)) : <p className="muted">No news loaded.</p>}</div>
              </article>
              <article className="panel">
                <h3>Finnhub + TradingView</h3>
                <div className="action-row">
                  <input value={finnhubLookupQuery} onChange={(event) => setFinnhubLookupQuery(event.target.value)} placeholder="Lookup symbol" />
                  <button type="button" onClick={runFinnhubLookup} disabled={busy}>Lookup</button>
                  <button type="button" onClick={loadFinnhubStatus} disabled={busy}>Reload Finnhub</button>
                </div>
                <div className="compact-output">
                  <p><strong>Configured:</strong> {String(finnhubStatus?.configured ?? false)}</p>
                  <p><strong>Webhook Secret:</strong> {String(finnhubStatus?.webhook_secret_configured ?? false)}</p>
                  <p><strong>Webhook URL:</strong> {finnhubStatus?.webhook_url ?? "-"}</p>
                  <p><strong>US Market:</strong> {String(finnhubMarketStatus?.isOpen ?? false)} | {finnhubMarketStatus?.session ?? "-"}</p>
                </div>
                <div className="list-box">
                  {finnhubLookupItems.length ? finnhubLookupItems.slice(0, 8).map((item) => (
                    <div key={`finnhub-lookup-${item.symbol}`} className="list-item">
                      <strong>{item.displaySymbol} | {item.description}</strong>
                      <span>{item.type}</span>
                      <button type="button" onClick={() => { void inspectOpenStockSymbol(item.symbol); }} disabled={busy}>Open</button>
                    </div>
                  )) : <p className="muted">No Finnhub lookup results loaded.</p>}
                </div>
                <div className="list-box">
                  {finnhubCompanyNews.length ? finnhubCompanyNews.slice(0, 6).map((item) => (
                    <a key={`finnhub-news-${item.id}`} className="list-item" href={item.url} target="_blank" rel="noreferrer">
                      <div>
                        <strong>{item.source} | {item.related || "MARKET"}</strong>
                        <span>{item.headline}</span>
                        <p className="muted">{item.summary}</p>
                      </div>
                    </a>
                  )) : <p className="muted">No Finnhub company news loaded.</p>}
                </div>
                {finnhubWidgetConfigs ? (
                  <div className="operator-grid">
                    <div className="panel inset-panel">
                      <h4>Heatmap</h4>
                      <TradingViewEmbed scriptUrl={finnhubWidgetConfigs.heatmap.script_url} config={finnhubWidgetConfigs.heatmap.config} height={520} />
                    </div>
                    <div className="panel inset-panel">
                      <h4>Market Quotes</h4>
                      <TradingViewEmbed scriptUrl={finnhubWidgetConfigs.market_quotes.script_url} config={finnhubWidgetConfigs.market_quotes.config} height={420} />
                    </div>
                    <div className="panel inset-panel">
                      <h4>Advanced Chart</h4>
                      <TradingViewEmbed scriptUrl={finnhubWidgetConfigs.advanced_chart.script_url} config={finnhubWidgetConfigs.advanced_chart.config} height={520} />
                    </div>
                    <div className="panel inset-panel">
                      <h4>Timeline</h4>
                      <TradingViewEmbed scriptUrl={finnhubWidgetConfigs.timeline.script_url} config={finnhubWidgetConfigs.timeline.config} height={520} />
                    </div>
                  </div>
                ) : <p className="muted">TradingView widget config unavailable until Finnhub status loads.</p>}
              </article>
              <article className="panel">
                <h3>External Gateways</h3>
                <div className="action-row">
                  <button type="button" onClick={loadGatewayChannels} disabled={busy}>Refresh Gateways</button>
                  <button type="button" onClick={sendTelegramGatewayTest} disabled={busy}>Telegram Test</button>
                  <button type="button" onClick={sendWhatsappGatewayTest} disabled={busy}>WhatsApp Test</button>
                </div>
                <div className="list-box">
                  {gatewayChannels.length ? gatewayChannels.map((item) => (
                    <div key={item.channel} className="list-item">
                      <div>
                        <strong>{item.label}</strong>
                        <p className="muted">{item.status} | {item.mode}</p>
                        <p className="muted">{item.message}</p>
                        <p className="muted">{item.hint ?? "-"}</p>
                        <p className="muted">Webhook: {item.webhook_url ?? "not available"}</p>
                      </div>
                    </div>
                  )) : <p className="muted">No gateway status loaded.</p>}
                </div>
              </article>
              <article className="panel">
                <h3>Flat Router</h3>
                <div className="action-row">
                  <input value={flatRouteInput} onChange={(event) => setFlatRouteInput(event.target.value)} placeholder="Route prompt" />
                  <button type="button" onClick={runFlatRouterDecision} disabled={busy}>Route</button>
                  <button type="button" onClick={loadFlatRouterStatus} disabled={busy}>Status</button>
                  <button type="button" onClick={saveFlatRouterSettings} disabled={busy}>Save Settings</button>
                </div>
                <div className="action-row">
                  <input value={flatRouterEngineInput} onChange={(event) => setFlatRouterEngineInput(event.target.value)} placeholder="Engine" />
                  <input value={flatRouterModeInput} onChange={(event) => setFlatRouterModeInput(event.target.value)} placeholder="Mode" />
                </div>
                <div className="action-row">
                  <input value={flatRouterDefaultAgentInput} onChange={(event) => setFlatRouterDefaultAgentInput(event.target.value)} placeholder="Default agent" />
                  <input value={flatRouterSkillsProfileInput} onChange={(event) => setFlatRouterSkillsProfileInput(event.target.value)} placeholder="Skills profile" />
                </div>
                <div className="action-row">
                  <input value={flatRouterGatewaysInput} onChange={(event) => setFlatRouterGatewaysInput(event.target.value)} placeholder="Gateways CSV" />
                  <button type="button" onClick={loadOpenClawSettings} disabled={busy}>Reload Config</button>
                  <button type="button" onClick={loadOpenClawHeartbeat} disabled={busy}>Heartbeat</button>
                  <button type="button" onClick={loadOpenClawCron} disabled={busy}>Cron</button>
                </div>
                <div className="compact-output">
                  <p><strong>Engine:</strong> {asString(flatRouterStatus?.settings?.engine)}</p>
                  <p><strong>Mode:</strong> {asString(flatRouterStatus?.settings?.routing_mode)}</p>
                  <p><strong>Default Agent:</strong> {asString(flatRouterStatus?.settings?.default_agent)}</p>
                  <p><strong>Agents:</strong> {flatRouterStatus?.agents?.length ?? 0} | <strong>Skills:</strong> {flatRouterStatus?.skills?.length ?? 0}</p>
                </div>
                <div className="compact-output">
                  <p><strong>Version:</strong> {openClawSettings?.app_version ?? "-"}</p>
                  <p><strong>Heartbeat:</strong> {asString(openClawHeartbeat?.scheduler?.heartbeat)}</p>
                  <p><strong>Scheduler Running:</strong> {String(openClawHeartbeat?.scheduler?.running ?? false)}</p>
                  <p><strong>Cron Jobs:</strong> {openClawCron?.count ?? 0}</p>
                </div>
                <div className="list-box">
                  {openClawCron?.jobs?.length ? openClawCron.jobs.slice(0, 6).map((job) => (
                    <div key={`cron-job-${asString(job.job_id, asString(job.name, "job"))}`} className="list-item">
                      <strong>{asString(job.name, asString(job.job_id, "job"))}</strong>
                      <span>{asString(job.job_type)} | {asString(job.schedule_cron, "manual")}</span>
                    </div>
                  )) : <p className="muted">No cron jobs registered.</p>}
                </div>
                <div className="list-box">
                  {openClawCron?.job_runs?.length ? openClawCron.job_runs.slice(0, 6).map((run) => (
                    <div key={`cron-run-${asString(run.job_run_id, asString(run.job_id, "run"))}`} className="list-item">
                      <strong>{asString(run.job_id, "job-run")}</strong>
                      <span>{asString(run.status)} | attempt {asString(run.attempt, "0")}</span>
                    </div>
                  )) : <p className="muted">No cron runs recorded.</p>}
                </div>
                {flatRouteDecision ? (
                  <div className="compact-output">
                    <p><strong>Selected Agent:</strong> {flatRouteDecision.selected_agent}</p>
                    <p><strong>Route:</strong> {flatRouteDecision.route}</p>
                    <p><strong>Reason:</strong> {flatRouteDecision.reason}</p>
                    <p><strong>Skills:</strong> {flatRouteDecision.skills.join(", ") || "-"}</p>
                  </div>
                ) : null}
              </article>
              <article className="panel">
                <h3>World Monitor</h3>
                <div className="action-row">
                  <input value={worldMonitorSymbols} onChange={(event) => setWorldMonitorSymbols(event.target.value)} placeholder="Symbols CSV" />
                  <select value={worldMonitorFocusMode} onChange={(event) => setWorldMonitorFocusMode(event.target.value as "general" | "focused")}>
                    <option value="general">General</option>
                    <option value="focused">Focused</option>
                  </select>
                  <input type="number" min={1} max={50} value={worldMonitorLimit} onChange={(event) => setWorldMonitorLimit(Number(event.target.value) || 18)} placeholder="Limit" />
                  <button type="button" onClick={loadWorldMonitorFeed} disabled={busy}>Refresh World Feed</button>
                </div>
                <div className="list-box">
                  {worldMonitorFeed.length ? worldMonitorFeed.slice(0, 10).map((item) => (
                    <a key={`world-${item.news_id}`} className="list-item" href={item.url} target="_blank" rel="noreferrer">
                      <div>
                        <strong>{item.symbol} | {item.source}</strong>
                        <p className="muted">{item.news_category ?? "economy"} | {item.news_class ?? "world"} | {item.world_source ?? "feed"}</p>
                        <p className="muted">{item.title}</p>
                        <p className="muted">{item.summary}</p>
                        <p className="muted">{new Date(item.published_at).toLocaleString()}</p>
                      </div>
                    </a>
                  )) : <p className="muted">No world monitor headlines loaded.</p>}
                </div>
                <div className="compact-output">
                  <p><strong>Sources:</strong> {worldMonitorSources.length ? worldMonitorSources.map((item) => item.source).join(", ") : "-"}</p>
                </div>
              </article>
              <article className="panel">
                <h3>Open Data</h3>
                <div className="action-row">
                  <input value={openDataQuery} onChange={(event) => setOpenDataQuery(event.target.value)} placeholder="Dataset query" />
                  <button type="button" onClick={loadOpenDataDatasets} disabled={busy}>Datasets</button>
                </div>
                <div className="action-row">
                  <input value={openDataOverviewSymbols} onChange={(event) => setOpenDataOverviewSymbols(event.target.value)} placeholder="Symbols CSV" />
                  <button type="button" onClick={loadOpenDataOverview} disabled={busy}>Overview</button>
                </div>
                <div className="action-row">
                  <input value={openDataSeriesSymbol} onChange={(event) => setOpenDataSeriesSymbol(event.target.value)} placeholder="Series symbol" />
                  <select value={openDataSeriesInterval} onChange={(event) => setOpenDataSeriesInterval(event.target.value)}>
                    <option value="1d">1d</option>
                    <option value="1wk">1wk</option>
                    <option value="1mo">1mo</option>
                  </select>
                  <input type="number" min={10} max={300} value={openDataSeriesLimit} onChange={(event) => setOpenDataSeriesLimit(Number(event.target.value) || 120)} placeholder="Points" />
                  <button type="button" onClick={loadOpenDataSeries} disabled={busy}>Series</button>
                </div>
                <div className="compact-output">
                  <p><strong>OpenBB available:</strong> {String(openDataOpenbbAvailable)}</p>
                  <p><strong>Datasets:</strong> {openDataDatasets.length}</p>
                  <p><strong>Overview rows:</strong> {openDataOverview.length}</p>
                  <p><strong>Series points:</strong> {openDataSeries.length} | <strong>Backend:</strong> {openDataSeriesBackend}</p>
                </div>
                <div className="list-box">
                  {openDataOverview.length ? openDataOverview.slice(0, 8).map((item) => (
                    <div key={`opendata-${item.symbol}`} className="list-item">
                      <strong>{item.symbol} | {item.name}</strong>
                      <span>{item.price.toFixed(2)} {item.currency} | {formatQuoteChange(item.change_pct / 100)}</span>
                    </div>
                  )) : <p className="muted">No open data overview loaded.</p>}
                </div>
                <div className="list-box">
                  {openDataDatasets.length ? openDataDatasets.slice(0, 8).map((item) => (
                    <div key={`dataset-${item.dataset_id}`} className="list-item">
                      <strong>{item.dataset_id} | {item.label}</strong>
                      <span>{item.provider}</span>
                      <p className="muted">{item.description}</p>
                    </div>
                  )) : <p className="muted">No open data datasets loaded.</p>}
                </div>
                <div className="list-box">
                  {openDataSeries.length ? openDataSeries.slice(-12).map((point) => (
                    <div key={`series-${point.ts}`} className="list-item">
                      <strong>{new Date(point.ts).toLocaleDateString()}</strong>
                      <span>O:{point.open.toFixed(2)} H:{point.high.toFixed(2)} L:{point.low.toFixed(2)} C:{point.close.toFixed(2)}</span>
                    </div>
                  )) : <p className="muted">No open data series loaded.</p>}
                </div>
              </article>
              <article className="panel">
                <h3>Open Stock</h3>
                <div className="action-row">
                  <input value={openStockQuery} onChange={(event) => setOpenStockQuery(event.target.value)} placeholder="Search stock" />
                  <button type="button" onClick={searchOpenStock} disabled={busy}>Search</button>
                </div>
                <div className="action-row">
                  <input value={openStockCatalogQuery} onChange={(event) => setOpenStockCatalogQuery(event.target.value)} placeholder="Catalog query" />
                  <select value={openStockCatalogExchange} onChange={(event) => setOpenStockCatalogExchange(event.target.value)}>
                    <option value="ALL">All exchanges</option>
                    <option value="NASDAQ">NASDAQ</option>
                    <option value="NYSE">NYSE</option>
                    <option value="NYSEARCA">NYSEARCA</option>
                  </select>
                  <select value={openStockCatalogType} onChange={(event) => setOpenStockCatalogType(event.target.value)}>
                    <option value="ALL">All types</option>
                    <option value="EQUITY">Equity</option>
                    <option value="ETF">ETF</option>
                  </select>
                  <input type="number" min={5} max={30} value={openStockCatalogLimit} onChange={(event) => setOpenStockCatalogLimit(Number(event.target.value) || 12)} placeholder="Rows" />
                  <button type="button" onClick={loadOpenStockCatalog} disabled={busy}>Catalog</button>
                </div>
                <div className="action-row">
                  <input value={openStockSnapshotSymbols} onChange={(event) => setOpenStockSnapshotSymbols(event.target.value)} placeholder="Snapshot symbols CSV" />
                  <button type="button" onClick={loadOpenStockSnapshot} disabled={busy}>Snapshot</button>
                </div>
                <div className="compact-output">
                  <p><strong>Search rows:</strong> {openStockSearchItems.length}</p>
                  <p><strong>Catalog rows:</strong> {openStockCatalogItems.length} / {openStockCatalogTotal}</p>
                  <p><strong>Snapshot rows:</strong> {openStockSnapshotItems.length}</p>
                  <p><strong>Active Symbol:</strong> {openStockActiveSymbol || "-"}</p>
                </div>
                <div className="compact-output">
                  <p><strong>Portfolio Lens:</strong> {watchlists[activeWatchlistId]?.includes(openStockActiveSymbol) ? "Tracked in watchlist" : "Reference only"}</p>
                  <p><strong>Account Scope:</strong> {portfolioAccountScope}</p>
                  <p><strong>Primary Research Symbol:</strong> {openDataSeriesSymbol}</p>
                </div>
                <div className="compact-output">
                  <p><strong>Name:</strong> {openStockReference?.name ?? "-"}</p>
                  <p><strong>Day Range:</strong> {openStockReference ? `${openStockReference.day_low.toFixed(2)} - ${openStockReference.day_high.toFixed(2)}` : "-"}</p>
                  <p><strong>52W Range:</strong> {openStockReference ? `${openStockReference.year_low.toFixed(2)} - ${openStockReference.year_high.toFixed(2)}` : "-"}</p>
                  <p><strong>Quote:</strong> {openStockReference?.website ? <a href={openStockReference.website} target="_blank" rel="noreferrer">Open</a> : "-"}</p>
                </div>
                <div className="list-box">
                  {openStockCatalogItems.length ? openStockCatalogItems.map((item) => (
                    <div key={`openstock-catalog-${item.symbol}`} className="list-item">
                      <strong>{item.symbol} | {item.name}</strong>
                      <span>{item.exchange} | {item.type}</span>
                      <button type="button" onClick={() => { void inspectOpenStockSymbol(item.symbol); }} disabled={busy}>Open</button>
                    </div>
                  )) : <p className="muted">No open stock catalog loaded.</p>}
                </div>
                <div className="action-row">
                  <button type="button" onClick={openStockCatalogPrevPage} disabled={busy || openStockCatalogOffset === 0}>Prev</button>
                  <button type="button" onClick={openStockCatalogNextPage} disabled={busy || openStockCatalogOffset + openStockCatalogLimit >= openStockCatalogTotal}>Next</button>
                </div>
                <div className="panel inset-panel">
                  <h4>OpenStock Monitor Board</h4>
                  <div className="list-box">
                    {watchlistRows.length ? watchlistRows.map((item) => (
                      <div key={`openstock-monitor-${item.instrument_id}`} className="list-item">
                        <div>
                          <strong>{item.symbol} | {item.name}</strong>
                          <span>{formatQuoteValue(item.value, item.currency)} | {formatQuoteChange(item.change_pct)}</span>
                          <p className="muted">Source: {item.source_label} | Status: {item.status} | Portfolio: {portfolioSymbols.has(item.symbol.toUpperCase()) ? "held" : "watchlist"}</p>
                        </div>
                        <div className="action-row">
                          <span className={item.change_pct >= 0 ? "pnl-up" : "pnl-down"}>{monitorFlashOn ? "●" : "○"}</span>
                          <button type="button" onClick={() => { void inspectOpenStockSymbol(item.symbol); }} disabled={busy}>Inspect</button>
                        </div>
                      </div>
                    )) : <p className="muted">Add symbols to the watchlist to monitor them here.</p>}
                  </div>
                </div>
                <div className="list-box">
                  {openStockSearchItems.length ? openStockSearchItems.slice(0, 6).map((item) => (
                    <div key={`openstock-search-${item.symbol}`} className="list-item">
                      <strong>{item.symbol} | {item.name}</strong>
                      <span>{item.exchange} | {item.type}</span>
                      <button type="button" onClick={() => { void inspectOpenStockSymbol(item.symbol); }} disabled={busy}>Inspect</button>
                    </div>
                  )) : <p className="muted">No open stock search results.</p>}
                </div>
                <div className="list-box">
                  {openStockSnapshotItems.length ? openStockSnapshotItems.slice(0, 6).map((item) => (
                    <div key={`openstock-snapshot-${item.symbol}`} className="list-item">
                      <strong>{item.symbol} | {item.name}</strong>
                      <span>{item.price.toFixed(2)} {item.currency} | {formatQuoteChange(item.change_pct / 100)}</span>
                      <p className="muted">{item.exchange} | {item.type}</p>
                      <p className="muted">Market Cap: {formatCompactNumber(item.market_cap)} | Volume: {formatCompactNumber(item.volume)}</p>
                    </div>
                  )) : <p className="muted">No open stock snapshot loaded.</p>}
                </div>
                <div className="panel inset-panel">
                  <h4>{openStockActiveSymbol} Candlestick</h4>
                  <div className="action-row">
                    <button type="button" onClick={loadOpenDataSeries} disabled={busy}>Refresh Candles</button>
                  </div>
                  {openDataSeries.length ? (() => {
                    const chartPoints = openDataSeries.slice(-30);
                    const metrics = computeCandleChartMetrics(chartPoints);
                    const width = 640;
                    const height = 240;
                    const candleWidth = Math.max(6, Math.floor(width / Math.max(chartPoints.length, 1)) - 4);
                    return (
                      <svg viewBox={`0 0 ${width} ${height}`} className="chart-surface" role="img" aria-label={`${openStockActiveSymbol} candlestick chart`}>
                        {chartPoints.map((point, index) => {
                          const x = 12 + index * (candleWidth + 4);
                          const toY = (value: number) => 10 + ((metrics.max - value) / metrics.range) * (height - 20);
                          const openY = toY(point.open);
                          const closeY = toY(point.close);
                          const highY = toY(point.high);
                          const lowY = toY(point.low);
                          const candleTop = Math.min(openY, closeY);
                          const candleHeight = Math.max(Math.abs(closeY - openY), 2);
                          const rising = point.close >= point.open;
                          return (
                            <g key={`candle-${point.ts}`}>
                              <line x1={x + candleWidth / 2} y1={highY} x2={x + candleWidth / 2} y2={lowY} stroke={rising ? "#18a957" : "#d64545"} strokeWidth="2" />
                              <rect x={x} y={candleTop} width={candleWidth} height={candleHeight} fill={rising ? "#18a957" : "#d64545"} rx="1" />
                            </g>
                          );
                        })}
                      </svg>
                    );
                  })() : <p className="muted">Load open data series to render candlesticks.</p>}
                </div>
                <div className="panel inset-panel">
                  <h4>OpenStock News Grid</h4>
                  <div className="list-box">
                    {watchlistNews.length ? watchlistNews.map((item) => (
                      <a key={`openstock-news-${item.news_id}`} className="list-item" href={item.url} target="_blank" rel="noreferrer">
                        <div>
                          <strong>{item.symbol} | {item.source}</strong>
                          <span>{item.title}</span>
                          <p className="muted">{item.summary}</p>
                        </div>
                      </a>
                    )) : <p className="muted">No watchlist-linked market news loaded.</p>}
                  </div>
                </div>
              </article>
              <article className="panel">
                <h3>Linked Daily Cycle</h3>
                <div className="compact-output"><p><strong>Cycle Run:</strong> {dailyCycle?.run_id ?? "-"}</p><p><strong>Startup:</strong> {dailyCycle?.linked_runs.startup ?? "-"}</p><p><strong>Breakdown Run:</strong> {dailyCycle?.linked_runs.breakdown_run_id ?? "-"}</p><p><strong>Consultant Run:</strong> {dailyCycle?.linked_runs.consultant_run_id ?? "-"}</p></div>
              </article>
            </div>
          ) : null}

          {activeNavTab === "Performance" ? (
            <div className="operator-grid" id="performance-page">
              <article className="panel">
                <h3>Breakdown Controls</h3>
                <div className="action-row">
                  <select value={breakdownPeriod} onChange={(e) => setBreakdownPeriod(e.target.value)}><option value="1d">1D</option><option value="7d">7D</option><option value="30d">30D</option></select>
                  <select value={breakdownFrequency} onChange={(e) => setBreakdownFrequency(e.target.value)}><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select>
                  <button type="button" onClick={loadBreakdown} disabled={busy}>Refresh Breakdown</button>
                </div>
                <div className="action-row">
                  <input type="number" value={monitorInterval} min={5} onChange={(e) => setMonitorInterval(Number(e.target.value) || 60)} placeholder="Monitor interval seconds" />
                  <button type="button" onClick={enableMonitor} disabled={busy}>Enable Monitor</button>
                  <button type="button" onClick={disableMonitor} disabled={busy}>Disable Monitor</button>
                  <button type="button" onClick={refreshMonitorStatus} disabled={busy}>Monitor Status</button>
                </div>
                <p className="muted">Breakdown run id: {breakdown?.run_id ?? "-"}</p>
                <p className="muted">Monitor enabled: {String(monitorStatus?.enabled ?? false)}</p>
              </article>
              <article className="panel"><h3>Allocation</h3><div className="list-box">{breakdown?.allocation?.asset_class?.length ? breakdown.allocation.asset_class.map((item) => (<div key={item.bucket} className="list-item"><strong>{item.bucket}</strong><span>{toFixedPercent(item.weight_pct / 100)}</span></div>)) : <p className="muted">Run breakdown to view allocation.</p>}</div></article>
              <article className="panel"><h3>Portfolio Movers</h3><div className="compact-output"><p><strong>Top:</strong> {breakdown?.movers?.top?.[0]?.symbol ?? "-"}</p><p><strong>Bottom:</strong> {breakdown?.movers?.bottom?.[0]?.symbol ?? "-"}</p><p><strong>Top Contribution:</strong> {breakdown?.movers?.top?.[0] ? usd(breakdown.movers.top[0].contribution) : "-"}</p></div></article>
              <article className="panel"><h3>Risk Measures</h3><div className="compact-output"><p><strong>Drawdown:</strong> {breakdown ? toFixedPercent(breakdown.risk.drawdown_pct / 100) : "-"}</p><p><strong>Concentration:</strong> {breakdown ? breakdown.risk.concentration_score.toFixed(4) : "-"}</p><p><strong>Largest Position:</strong> {breakdown ? toFixedPercent(breakdown.risk.largest_position_pct / 100) : "-"}</p></div></article>
              <article className="panel"><h3>NAV Series</h3><div className="compact-output"><p><strong>Points:</strong> {breakdown?.nav_series?.length ?? 0}</p><p><strong>Latest NAV:</strong> {breakdown?.nav_series?.length ? usd(breakdown.nav_series[breakdown.nav_series.length - 1].nav) : "-"}</p><p><strong>Latest Return:</strong> {breakdown?.nav_series?.length ? toFixedPercent(breakdown.nav_series[breakdown.nav_series.length - 1].return_pct / 100) : "-"}</p></div></article>
              <article className="panel"><h3>Institutional Consultant Brief</h3><div className="compact-output"><p><strong>Run:</strong> {consultantBrief?.run_id ?? "-"}</p><p><strong>Objective:</strong> {asString(consultantBrief?.ic_brief?.objective)}</p><p><strong>Risk Profile:</strong> {asString(consultantBrief?.ic_brief?.risk_profile)}</p><p><strong>Scenarios:</strong> {consultantBrief?.scenario_table?.length ?? 0}</p></div></article>
            </div>
          ) : null}

          {chatDocked ? runtimeWorkspaceCard : null}
          {error ? <article className="panel error">{error}</article> : null}
        </section>
      </div>
      {!chatDocked ? (
        <section className={`suzybae-bottom ${chatMinimized ? "minimized" : ""}`}>
          <div className="suzybae-head">
            <strong>SuzyBae</strong>
            <span>oh-my-opencode-sisyphus</span>
            <div className="suzybae-actions">
              <button type="button" onClick={() => setChatMinimized((prev) => !prev)}>{chatMinimized ? "Expand" : "Minimize"}</button>
              <button type="button" onClick={() => setChatDocked(true)}>Dock</button>
            </div>
          </div>
          {!chatMinimized ? runtimeWorkspaceCard : null}
        </section>
      ) : null}
      {showProviderFlowModal ? (
        <AuthModal
          open={showProviderFlowModal}
          providerLabel={selectedProviderLabel || "-"}
          authMethod={selectedAuthMethod || "-"}
          error={connectionBlockReason}
          onClose={() => {
            setShowProviderFlowModal(false);
          }}
        >
          <div>
            {connectionLifecycleState === "selecting_provider" ? (
              <ProviderPicker
                providers={connectionProviders}
                selectedProviderId={selectedProviderId}
                onSelect={(providerId) => {
                  void selectProviderForFlow(providerId);
                }}
              />
            ) : null}

            {connectionLifecycleState === "awaiting_auth" || connectionLifecycleState === "auth_failed" ? (
              <div>
                <label htmlFor="auth-method">Authentication</label>
                <select
                  id="auth-method"
                  value={selectedAuthMethod}
                  onChange={(event) => {
                    void changeAuthMethodForFlow(event.target.value);
                  }}
                >
                  {availableAuthMethods.map((method) => (
                    <option key={method} value={method}>{method}</option>
                  ))}
                </select>
                {selectedAuthMethod === "api_key" || selectedAuthMethod === "api-key" || selectedAuthMethod === "base_url_api_key" ? (
                  <input
                    type="password"
                    value={apiKeyInput}
                    onChange={(event) => setApiKeyInput(event.target.value)}
                    placeholder="API key"
                  />
                ) : null}
                {selectedAuthMethod === "token" ? (
                  <input
                    type="password"
                    value={authTokenInput}
                    onChange={(event) => setAuthTokenInput(event.target.value)}
                    placeholder="Token"
                  />
                ) : null}
                {selectedAuthMethod === "base_url" || selectedAuthMethod === "base_url_api_key" ? (
                  <input
                    value={authBaseUrlInput}
                    onChange={(event) => setAuthBaseUrlInput(event.target.value)}
                    placeholder="Base URL"
                  />
                ) : null}
                <div className="action-row">
                  <button type="button" onClick={() => { void completeAuthFlow(); }} disabled={busy}>Authenticate</button>
                </div>
              </div>
            ) : null}

            {connectionLifecycleState === "auth_valid"
            || connectionLifecycleState === "loading_models"
            || connectionLifecycleState === "model_selected"
            || connectionLifecycleState === "binding_session"
            || connectionLifecycleState === "connected"
            || connectionLifecycleState === "model_load_failed" ? (
              <div>
                <ModelPicker
                  models={connectionModels}
                  selectedModelId={selectedModelId}
                  onLoadModels={() => {
                    void loadModelsForFlow();
                  }}
                  onSelect={(modelId) => {
                    setSelectedModelId(modelId);
                    setConnectionLifecycleState("model_selected");
                  }}
                />
                <div className="action-row">
                  <button type="button" onClick={() => { void bindSelectedFlowSession(); }} disabled={busy || !selectedModelId}>Bind session</button>
                </div>
              </div>
            ) : null}
          </div>
        </AuthModal>
      ) : null}
      {showCommandPalette ? (
        <section className="runtime-modal" role="dialog" aria-label="Runtime command center">
          <article className="panel runtime-modal-card">
            <h3>Runtime Command Center</h3>
            {commandPaletteSections.map((section) => (
              <div key={section.title}>
                <p className="runtime-group-title">{section.title}</p>
                <div className="runtime-modal-list">
                  {section.items.map((item) => (
                      <button
                        type="button"
                        key={item.id}
                        className="runtime-modal-item"
                      onClick={() => {
                        void runCommandPaletteAction(item.action);
                      }}
                      disabled={busy}
                    >
                      <strong>{item.label}</strong>
                      <span>{item.description}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
            <div className="action-row">
              <button type="button" onClick={() => setShowCommandPalette(false)} disabled={busy}>Close</button>
            </div>
          </article>
        </section>
      ) : null}
      {showSessionsModal ? (
        <section className="runtime-modal" role="dialog" aria-label="Session management">
          <article className="panel runtime-modal-card">
            <h3>Sessions</h3>
            <input
              value={sessionSearch}
              onChange={(e) => {
                setSessionSearch(e.target.value);
                setSessionCursor(0);
              }}
              onKeyDown={handleSessionModalKeyDown}
              placeholder="Search sessions"
            />
            <div className="runtime-modal-list" role="listbox" aria-label="Sessions list">
              {filteredSessions.length ? filteredSessions.map((item, idx) => (
                <button
                  type="button"
                  key={item.session_id}
                  className={`runtime-modal-item ${idx === sessionCursor ? "active" : ""}`}
                  onClick={() => {
                    setSessionCursor(idx);
                    void selectRuntimeSession(item.session_id);
                  }}
                  disabled={busy}
                >
                  <strong>{item.title}</strong>
                  <span>{item.session_id}</span>
                </button>
              )) : <p className="muted">No matching sessions.</p>}
            </div>
            <div className="action-row">
              <input
                value={newSessionTitle}
                onChange={(e) => setNewSessionTitle(e.target.value)}
                placeholder="New session title"
              />
              <button type="button" onClick={createRuntimeSessionFromModal} disabled={busy}>/new</button>
            </div>
            <div className="action-row">
              <input
                value={renameSessionTitle}
                onChange={(e) => setRenameSessionTitle(e.target.value)}
                placeholder="Rename selected session"
              />
              <button type="button" onClick={renameRuntimeSession} disabled={busy}>Rename</button>
              <button type="button" onClick={deleteRuntimeSession} disabled={busy}>Delete</button>
              <button type="button" onClick={() => setShowSessionsModal(false)} disabled={busy}>Close</button>
            </div>
          </article>
        </section>
      ) : null}
    </main>
  );
}
