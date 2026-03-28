from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/watchlists")
def watchlists(request: Request) -> dict[str, object]:
    service = request.app.state.watchlist_query_service
    return service.list()
