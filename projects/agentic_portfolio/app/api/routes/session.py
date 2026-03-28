from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas import SessionBindRequest, SessionResetRequest, SessionUnbindRequest

router = APIRouter()


@router.post("/session/bind")
def session_bind(payload: SessionBindRequest, request: Request) -> dict[str, object]:
    service = request.app.state.session_binding_service
    auth_service = request.app.state.auth_service
    model_service = request.app.state.model_service
    provider_gateway = request.app.state.provider_gateway
    auth_status = auth_service.status(payload.session_id)
    auth_valid = auth_status.get("status") == "auth_valid"
    runtime_connection_ready = False
    for connection in provider_gateway.list_connections():
        if connection.get("provider") != payload.provider_id:
            continue
        if connection.get("model") != payload.model_id:
            continue
        if not connection.get("enabled"):
            continue
        auth_method = connection.get("auth_method")
        if auth_method in {"chatgpt-browser", "chatgpt-headless"} and not connection.get("oauth_connected"):
            continue
        runtime_connection_ready = True
        break
    if not auth_valid and not runtime_connection_ready:
        raise HTTPException(status_code=400, detail="auth_valid required before bind")
    models = model_service.models_for_provider(payload.provider_id)
    if not any(item["model_id"] == payload.model_id for item in models):
        raise HTTPException(status_code=400, detail="model selection required before bind")
    try:
        return {
            "binding": service.bind(
                session_id=payload.session_id,
                provider_id=payload.provider_id,
                auth_method=payload.auth_method,
                model_id=payload.model_id,
                base_url=payload.base_url,
            )
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/session/unbind")
def session_unbind(payload: SessionUnbindRequest, request: Request) -> dict[str, object]:
    service = request.app.state.session_binding_service
    return {"binding": service.unbind(payload.session_id)}


@router.post("/session/reset")
def session_reset(payload: SessionResetRequest, request: Request) -> dict[str, object]:
    service = request.app.state.session_binding_service
    model_service = request.app.state.model_service
    model_service.invalidate_cache()
    return {"binding": service.reset(payload.session_id)}
