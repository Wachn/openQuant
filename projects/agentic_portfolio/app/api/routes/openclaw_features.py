from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas import (
    FlatRouterRouteRequest,
    FlatRouterUpdateSettingsRequest,
    OpenDataDatasetsRequest,
    OpenDataOverviewRequest,
    OpenDataSeriesRequest,
    OpenStockSearchRequest,
    OpenStockSnapshotRequest,
    WorldMonitorFeedRequest,
)

router = APIRouter()


@router.get("/agent-router/status")
def agent_router_status(request: Request) -> dict[str, object]:
    svc = request.app.state.flat_routing_agent_service
    return svc.status()


@router.get("/agent-router/settings")
def agent_router_settings(request: Request) -> dict[str, object]:
    svc = request.app.state.flat_routing_agent_service
    return {"settings": svc.get_settings()}


@router.post("/agent-router/settings")
def agent_router_update_settings(payload: FlatRouterUpdateSettingsRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.flat_routing_agent_service
    updates = {key: value for key, value in payload.model_dump(mode="json").items() if value is not None}
    return {"settings": svc.update_settings(updates)}


@router.post("/agent-router/route")
def agent_router_route(payload: FlatRouterRouteRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.flat_routing_agent_service
    return svc.route(message=payload.message, preferred_agent=payload.preferred_agent)


@router.post("/world-monitor/feed")
def world_monitor_feed(payload: WorldMonitorFeedRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.world_monitor_service
    items = svc.fetch_headlines(symbols=payload.symbols, limit=payload.limit, focus_mode=payload.focus_mode)
    return {
        "source": "worldmonitor",
        "symbols": payload.symbols,
        "focus_mode": payload.focus_mode,
        "items": items,
    }


@router.post("/open-data/datasets")
def open_data_datasets(payload: OpenDataDatasetsRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.open_data_service
    return svc.datasets(query=payload.query, limit=payload.limit)


@router.post("/open-data/overview")
def open_data_overview(payload: OpenDataOverviewRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.open_data_service
    return svc.overview(symbols=payload.symbols, limit=payload.limit)


@router.post("/open-data/series")
def open_data_series(payload: OpenDataSeriesRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.open_data_service
    try:
        return svc.series(
            symbol=payload.symbol,
            dataset_id=payload.dataset_id,
            interval=payload.interval,
            limit=payload.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/open-stock/search")
def open_stock_search(payload: OpenStockSearchRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.open_stock_service
    try:
        return svc.search(query=payload.query, limit=payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/open-stock/snapshot")
def open_stock_snapshot(payload: OpenStockSnapshotRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.open_stock_service
    return svc.snapshot(symbols=payload.symbols, limit=payload.limit)


@router.get("/openclaw/overview")
def openclaw_overview(request: Request) -> dict[str, object]:
    store = request.app.state.store
    session_count = len(store.list_chat_sessions())
    connection_count = len(store.list_provider_connections())
    connectors = request.app.state.platform_service.market_connector_status()
    gateways = request.app.state.channel_gateway_service.channels_status()
    router_status = request.app.state.flat_routing_agent_service.status()
    return {
        "health": "ok",
        "runtime": {
            "sessions": session_count,
            "provider_connections": connection_count,
        },
        "connectors": connectors,
        "gateways": gateways,
        "agent_router": {
            "engine": router_status.get("settings", {}).get("engine"),
            "routing_mode": router_status.get("settings", {}).get("routing_mode"),
            "agent_count": len(router_status.get("agents", [])),
            "skill_count": len(router_status.get("skills", [])),
        },
    }


@router.get("/openclaw/instances")
def openclaw_instances(request: Request) -> dict[str, object]:
    store = request.app.state.store
    sessions = store.list_chat_sessions()
    connections = store.list_provider_connections()
    return {
        "sessions": sessions,
        "provider_connections": connections,
        "session_count": len(sessions),
        "provider_connection_count": len(connections),
    }


@router.get("/openclaw/nodes")
def openclaw_nodes(request: Request) -> dict[str, object]:
    router_status = request.app.state.flat_routing_agent_service.status()
    return {
        "agents": router_status.get("agents", []),
        "skills": router_status.get("skills", []),
        "providers": request.app.state.provider_gateway.status(),
        "channels": request.app.state.channel_gateway_service.channels_status(),
    }


@router.get("/openclaw/usage")
def openclaw_usage(request: Request) -> dict[str, object]:
    store = request.app.state.store
    sessions = store.list_chat_sessions()
    changes = store.list_change_requests()
    suggestions = store.list_suggestions()
    orders = store.list_execution_orders()
    return {
        "sessions_total": len(sessions),
        "change_requests_total": len(changes),
        "suggestions_total": len(suggestions),
        "execution_orders_total": len(orders),
        "open_data_enabled": True,
        "open_stock_enabled": True,
        "world_monitor_enabled": True,
    }


@router.get("/openclaw/logs")
def openclaw_logs(request: Request, session_id: str = "", limit: int = 20) -> dict[str, object]:
    store = request.app.state.store
    normalized_limit = max(1, min(limit, 200))
    traces = store.list_runtime_route_traces(session_id=session_id, limit=normalized_limit)
    return {
        "session_id": session_id,
        "limit": normalized_limit,
        "items": traces,
    }


@router.get("/openclaw/approvals")
def openclaw_approvals(request: Request, status: str | None = None) -> dict[str, object]:
    store = request.app.state.store
    items = store.list_change_requests(status=status)
    return {
        "status": status,
        "items": items,
        "count": len(items),
    }


@router.get("/openclaw/features")
def openclaw_features_contracts() -> dict[str, object]:
    return {
        "ui_feature_groups": {
            "overview": ["/openclaw/overview"],
            "sessions": ["/runtime/chat/sessions", "/openclaw/instances"],
            "skills": ["/agent-router/status", "/plugins/capabilities", "/openclaw/nodes"],
            "usage": ["/openclaw/usage"],
            "logs": ["/openclaw/logs"],
            "approvals": ["/openclaw/approvals", "/runtime/change-requests"],
            "gateway_channels": ["/gateway/channels", "/market/connectors/status"],
        },
        "integrated_features": {
            "worldmonitor": ["/world-monitor/feed", "/news/feed?sources=worldmonitor"],
            "openbb_style_open_data": ["/open-data/datasets", "/open-data/overview", "/open-data/series"],
            "openstock_style_reference": ["/open-stock/search", "/open-stock/snapshot"],
        },
    }
