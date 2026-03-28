from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MarketDataServiceV21:
    def __init__(self, platform_service) -> None:
        self.platform_service = platform_service

    def refresh_quotes(self, symbols: list[str]) -> dict[str, object]:
        snapshots = self.platform_service.refresh_market(symbols)
        payload = [item.model_dump(mode="json") for item in snapshots]
        return {
            "market_snapshot_id": f"snapshot-{int(datetime.now(timezone.utc).timestamp())}",
            "as_of_ts": utc_now_iso(),
            "quotes": payload,
        }
