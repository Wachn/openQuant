from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/engine/health")
def engine_health(provider_id: str, request: Request, base_url: str | None = None) -> dict[str, object]:
    service = request.app.state.engine_service
    return service.health(provider_id=provider_id, base_url=base_url)


@router.get("/engine/models")
def engine_models(provider_id: str, request: Request) -> dict[str, object]:
    service = request.app.state.engine_service
    return service.models(provider_id=provider_id)
