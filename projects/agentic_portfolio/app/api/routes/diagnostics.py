from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/diagnostics")
def diagnostics(request: Request) -> dict[str, object]:
    service = request.app.state.diagnostics_service
    return service.collect(error=None)
