from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    config = request.app.state.config
    return HealthResponse(
        status="ok",
        app_name=config.app_name,
        app_version=config.app_version,
        app_env=config.app_env,
        started_at=request.app.state.started_at,
    )
