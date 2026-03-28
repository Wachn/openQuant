from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas import AuthCompleteRequest, AuthLogoutRequest, AuthStartRequest

router = APIRouter()


@router.post("/auth/start")
def auth_start(payload: AuthStartRequest, request: Request) -> dict[str, object]:
    service = request.app.state.auth_service
    try:
        return service.start(
            provider_id=payload.provider_id,
            method=payload.auth_method,
            session_id=payload.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/complete")
def auth_complete(payload: AuthCompleteRequest, request: Request) -> dict[str, object]:
    service = request.app.state.auth_service
    try:
        return service.complete(
            provider_id=payload.provider_id,
            method=payload.auth_method,
            session_id=payload.session_id,
            state=payload.state,
            code=payload.code,
            api_key=payload.api_key,
            token=payload.token,
            base_url=payload.base_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/logout")
def auth_logout(payload: AuthLogoutRequest, request: Request) -> dict[str, object]:
    service = request.app.state.auth_service
    return service.logout(provider_id=payload.provider_id, session_id=payload.session_id)
