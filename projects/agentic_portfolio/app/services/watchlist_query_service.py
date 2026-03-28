from __future__ import annotations


class WatchlistQueryService:
    def __init__(self) -> None:
        self._watchlist = ["AAPL", "MSFT", "NVDA", "SPY"]

    def list(self) -> dict[str, object]:
        return {"symbols": list(self._watchlist)}
