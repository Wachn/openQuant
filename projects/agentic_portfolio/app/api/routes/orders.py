from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/orders")
def orders(request: Request) -> dict[str, object]:
    service = request.app.state.order_query_service
    return service.list_orders()
