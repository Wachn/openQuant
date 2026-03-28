from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/instruments/{symbol}")
def instrument(symbol: str, request: Request) -> dict[str, object]:
    service = request.app.state.instrument_query_service
    return service.detail(symbol)
