from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PortfolioServiceV21:
    def __init__(self, platform_service) -> None:
        self.platform_service = platform_service

    def list_accounts(self) -> list[dict[str, object]]:
        return [
            {
                "account_id": "paper-default",
                "broker_id": "ibkr_paper",
                "broker_account_id": "PAPER-001",
                "base_currency": "USD",
            }
        ]

    def import_account(self, broker_id: str, broker_account_id: str) -> dict[str, object]:
        return {
            "account_id": f"{broker_id}:{broker_account_id}",
            "broker_id": broker_id,
            "broker_account_id": broker_account_id,
            "base_currency": "USD",
            "created_at": utc_now_iso(),
        }

    def positions(self, _account_id: str) -> list[dict[str, object]]:
        snapshot = self.platform_service.latest_portfolio().model_dump(mode="json")
        return snapshot.get("positions", [])

    def nav_points(self, account_id: str) -> list[dict[str, object]]:
        snapshot = self.platform_service.latest_portfolio().model_dump(mode="json")
        return [
            {
                "ts": snapshot["as_of_ts"],
                "account_id": account_id,
                "nav": snapshot["equity"],
                "cash": snapshot["cash"],
                "source": "portfolio_snapshot",
            }
        ]

    def allocation(self, _account_id: str, dimension: str) -> list[dict[str, object]]:
        breakdown = self.platform_service.portfolio_breakdown(period="7d", frequency="daily")
        allocation = breakdown.get("allocation", {})
        if dimension == "symbol":
            return allocation.get("symbol", [])
        return allocation.get("asset_class", [])
