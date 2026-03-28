from __future__ import annotations


class PortfolioQueryService:
    def __init__(self, portfolio_service_v21) -> None:
        self.portfolio_service_v21 = portfolio_service_v21

    def screen_payload(self, account_id: str) -> dict[str, object]:
        return {
            "account_id": account_id,
            "positions": self.portfolio_service_v21.positions(account_id),
            "allocation": self.portfolio_service_v21.allocation(account_id, "asset_class"),
            "nav": self.portfolio_service_v21.nav_points(account_id),
        }
