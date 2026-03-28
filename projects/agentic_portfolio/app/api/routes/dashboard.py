from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request) -> dict[str, object]:
    service = request.app.state.dashboard_service
    return service.snapshot()
