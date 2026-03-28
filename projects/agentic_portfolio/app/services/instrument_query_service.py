from __future__ import annotations


class InstrumentQueryService:
    def __init__(self, market_data_service_v21, portfolio_service_v21) -> None:
        self.market_data_service_v21 = market_data_service_v21
        self.portfolio_service_v21 = portfolio_service_v21

    def detail(self, symbol: str) -> dict[str, object]:
        quote = self.market_data_service_v21.refresh_quotes([symbol])
        positions = self.portfolio_service_v21.positions("paper-default")
        exposure = [item for item in positions if str(item.get("symbol")) == symbol]
        return {
            "symbol": symbol,
            "quote": quote,
            "exposure": exposure,
            "chart": {"type": "placeholder", "status": "available"},
        }
