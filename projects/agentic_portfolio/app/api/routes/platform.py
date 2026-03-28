from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.domain.core_models import RiskProfile, TradeTicket
from app.schemas import (
    ConsultantBriefRequest,
    DailyCycleRequest,
    ExecuteTicketRequest,
    ExecutionReconcileRequest,
    IbkrHistoryRequest,
    MarketCandlesRequest,
    MarketQuotesRequest,
    MonitorEnableRequest,
    NewsCachePurgeRequest,
    NewsFeedRequest,
    PluginInvokeRequest,
    PortfolioBreakdownRequest,
    PortfolioUpsertRequest,
    ResearchQueryRequest,
    StartupReportRequest,
    TradeLaneRequest,
)

router = APIRouter()


@router.put("/portfolio")
def upsert_portfolio(payload: PortfolioUpsertRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    snapshot = svc.upsert_portfolio(
        positions=[item.model_dump(mode="json") for item in payload.positions],
        cash=payload.cash,
    )
    return {"portfolio_snapshot": snapshot.model_dump(mode="json")}


@router.get("/portfolio")
def get_portfolio(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    snapshot = svc.latest_portfolio()
    return {"portfolio_snapshot": snapshot.model_dump(mode="json")}


@router.post("/portfolio/breakdown")
def portfolio_breakdown(payload: PortfolioBreakdownRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.portfolio_breakdown(period=payload.period, frequency=payload.frequency)


@router.post("/consultant/brief")
def consultant_brief(payload: ConsultantBriefRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.consultant_brief(period=payload.period, frequency=payload.frequency)


@router.post("/operator/daily-cycle")
def operator_daily_cycle(payload: DailyCycleRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        return svc.run_daily_cycle(
            tracked_symbols=payload.tracked_symbols,
            period=payload.period,
            frequency=payload.frequency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/monitor/enable")
def monitor_enable(payload: MonitorEnableRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        return svc.enable_monitor(payload.tracked_symbols, payload.interval_seconds)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/monitor/disable")
def monitor_disable(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.disable_monitor()


@router.get("/monitor/status")
def monitor_status(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.monitor_status()


@router.post("/monitor/refresh-now")
def monitor_refresh_now(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        status = svc.run_monitor_cycle_once()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return status


@router.get("/market/connectors/status")
def market_connectors_status(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.market_connector_status()


@router.post("/market/quotes")
def market_quotes(payload: MarketQuotesRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.market_quotes(payload.instruments, focus_mode=payload.focus_mode)


@router.post("/market/candles")
def market_candles(payload: MarketCandlesRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        return svc.market_candles(
            instrument_id=payload.instrument_id,
            interval=payload.interval,
            range_value=payload.range,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/market/ibkr/session")
def market_ibkr_session(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.ibkr_gateway_session()


@router.post("/market/ibkr/session/init")
def market_ibkr_session_init(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.ibkr_gateway_init_session()


@router.post("/market/ibkr/tickle")
def market_ibkr_tickle(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.ibkr_gateway_tickle()


@router.post("/market/ibkr/history")
def market_ibkr_history(payload: IbkrHistoryRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.ibkr_market_history(conid=payload.conid, period=payload.period, bar=payload.bar)


@router.post("/news/feed")
def news_feed(payload: NewsFeedRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.news_feed(
        symbols=payload.symbols,
        sources=payload.sources,
        categories=payload.categories,
        classes=payload.classes,
        limit=payload.limit,
        focus_mode=payload.focus_mode,
    )


@router.post("/news/cache")
def news_cache(payload: NewsFeedRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.cached_news_feed(
        symbols=payload.symbols,
        sources=payload.sources,
        categories=payload.categories,
        classes=payload.classes,
        limit=payload.limit,
        focus_mode=payload.focus_mode,
    )


@router.post("/news/cache/purge")
def news_cache_purge(_payload: NewsCachePurgeRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.purge_news_cache()


@router.put("/risk-profile/{profile}")
def set_risk_profile(profile: str, request: Request) -> dict[str, str]:
    svc = request.app.state.platform_service
    try:
        rp = RiskProfile(profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid risk profile") from exc
    svc.set_risk_profile(rp)
    return {"risk_profile": rp.value}


@router.post("/startup-report")
def startup_report(payload: StartupReportRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    report = svc.startup_report(payload.tracked_symbols)
    return report


@router.post("/research/query")
def research_query(payload: ResearchQueryRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.research_query(payload.query)


@router.post("/trade-lane/run")
def run_trade_lane(payload: TradeLaneRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return svc.run_trade_lane(payload.symbol, payload.profile)


@router.post("/execution/paper-submit")
def paper_submit(payload: ExecuteTicketRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    ticket = TradeTicket.model_validate(payload.ticket.model_dump(mode="json"))
    try:
        receipt = svc.submit_paper_order(ticket=ticket, confirm=payload.confirm, broker=payload.broker)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"receipt": receipt.model_dump(mode="json")}


@router.get("/execution/brokers")
def execution_brokers(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return {"brokers": svc.broker_capabilities()}


@router.get("/execution/orders/{order_id}/status")
def execution_order_status(order_id: str, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        status = svc.execution_status(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": status}


@router.post("/execution/orders/{order_id}/cancel")
def execution_order_cancel(order_id: str, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        status = svc.cancel_execution_order(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": status}


@router.get("/execution/orders/{order_id}/fills")
def execution_order_fills(order_id: str, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        fills = svc.execution_fills(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"order_id": order_id, "fills": fills}


@router.post("/execution/reconcile")
def execution_reconcile(payload: ExecutionReconcileRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    reconciled = svc.reconcile_execution_orders(payload.broker)
    return {"reconciled": reconciled, "count": len(reconciled)}


@router.get("/execution/orders/{order_id}/events")
def execution_order_events(order_id: str, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    try:
        events = svc.execution_events(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"order_id": order_id, "events": events}


@router.get("/suggestions")
def list_suggestions(request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return {"suggestions": svc.list_suggestions()}


@router.get("/runs/{run_id}/artifacts")
def run_artifacts(run_id: str, request: Request) -> dict[str, object]:
    svc = request.app.state.platform_service
    return {"run_id": run_id, "artifacts": svc.run_artifacts(run_id)}


@router.post("/plugins/reload")
def plugins_reload(request: Request) -> dict[str, object]:
    runtime = request.app.state.openclaw_runtime
    return runtime.reload()


@router.get("/plugins/status")
def plugins_status(request: Request) -> dict[str, object]:
    runtime = request.app.state.openclaw_runtime
    return {"plugins": runtime.status()}


@router.get("/plugins/capabilities")
def plugins_capabilities(request: Request) -> dict[str, object]:
    runtime = request.app.state.openclaw_runtime
    return {"capabilities": runtime.capabilities()}


@router.post("/plugins/invoke")
def plugins_invoke(payload: PluginInvokeRequest, request: Request) -> dict[str, object]:
    runtime = request.app.state.openclaw_runtime
    try:
        result = runtime.invoke(
            plugin_id=payload.plugin_id,
            capability=payload.capability,
            payload=payload.payload,
            run_id=payload.run_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.get("/brokers/mt5/health")
def mt5_health(request: Request) -> dict[str, object]:
    connector = request.app.state.mt5_connector
    return connector.health()
