from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/portfolio/accounts")
def portfolio_accounts(request: Request) -> dict[str, object]:
    service = request.app.state.portfolio_service_v21
    return {"accounts": service.list_accounts()}


@router.post("/portfolio/accounts/import")
def portfolio_account_import(payload: dict[str, str], request: Request) -> dict[str, object]:
    service = request.app.state.portfolio_service_v21
    account = service.import_account(
        broker_id=payload.get("broker_id", "ibkr_paper"),
        broker_account_id=payload.get("broker_account_id", "PAPER-001"),
    )
    return {"account": account}


@router.get("/portfolio/accounts/{account_id}/positions")
def portfolio_positions(account_id: str, request: Request) -> dict[str, object]:
    service = request.app.state.portfolio_service_v21
    return {"positions": service.positions(account_id)}


@router.get("/portfolio/accounts/{account_id}/nav")
def portfolio_nav(account_id: str, request: Request) -> dict[str, object]:
    service = request.app.state.portfolio_service_v21
    return {"points": service.nav_points(account_id)}


@router.get("/portfolio/accounts/{account_id}/allocation")
def portfolio_allocation(account_id: str, request: Request, dimension: str = "asset_class") -> dict[str, object]:
    service = request.app.state.portfolio_service_v21
    return {"items": service.allocation(account_id, dimension)}
