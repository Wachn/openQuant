from __future__ import annotations

import importlib.util
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpenDataService:
    DATASETS = [
        {
            "dataset_id": "equity_price_history",
            "label": "Equity Price History",
            "description": "OHLCV time series for listed symbols.",
            "provider": "openbb_bridge",
        },
        {
            "dataset_id": "equity_quote_snapshot",
            "label": "Equity Quote Snapshot",
            "description": "Latest quote, change, and volume snapshot.",
            "provider": "openbb_bridge",
        },
        {
            "dataset_id": "macro_proxy_series",
            "label": "Macro Proxy Series",
            "description": "Macro proxy through market symbols (e.g., DXY, gold, treasury ETFs).",
            "provider": "openbb_bridge",
        },
    ]

    def openbb_available(self) -> bool:
        return importlib.util.find_spec("openbb") is not None

    def datasets(self, query: str | None = None, limit: int = 20) -> dict[str, object]:
        max_items = max(1, min(int(limit), 100))
        q = (query or "").strip().lower()
        rows = self.DATASETS
        if q:
            rows = [
                item
                for item in rows
                if q in str(item.get("dataset_id", "")).lower() or q in str(item.get("label", "")).lower()
            ]
        return {
            "items": rows[:max_items],
            "openbb_available": self.openbb_available(),
            "updated_at": _utc_now_iso(),
        }

    def overview(self, symbols: list[str], limit: int = 20) -> dict[str, object]:
        normalized = [item.strip().upper() for item in symbols if isinstance(item, str) and item.strip()]
        deduped: list[str] = []
        for symbol in normalized:
            if symbol not in deduped:
                deduped.append(symbol)
        if not deduped:
            deduped = ["AAPL", "MSFT", "NVDA"]

        max_items = max(1, min(int(limit), 100))
        selected = deduped[:max_items]
        joined = ",".join(selected)
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(joined)}"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})

        items: list[dict[str, object]] = []
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            results = ((payload.get("quoteResponse") or {}).get("result") or []) if isinstance(payload, dict) else []
            if isinstance(results, list):
                for entry in results:
                    if not isinstance(entry, dict):
                        continue
                    symbol = str(entry.get("symbol") or "").upper()
                    if not symbol:
                        continue
                    items.append(
                        {
                            "symbol": symbol,
                            "name": entry.get("shortName") or symbol,
                            "price": float(entry.get("regularMarketPrice") or 0.0),
                            "change_pct": float(entry.get("regularMarketChangePercent") or 0.0),
                            "volume": float(entry.get("regularMarketVolume") or 0.0),
                            "currency": entry.get("currency") or "USD",
                        }
                    )
        except Exception:
            items = []

        if not items:
            for symbol in selected:
                items.append(
                    {
                        "symbol": symbol,
                        "name": symbol,
                        "price": 0.0,
                        "change_pct": 0.0,
                        "volume": 0.0,
                        "currency": "USD",
                    }
                )

        return {
            "symbols": selected,
            "items": items[:max_items],
            "backend": "openbb_bridge",
            "openbb_available": self.openbb_available(),
            "updated_at": _utc_now_iso(),
        }

    def series(self, symbol: str, dataset_id: str = "equity_price_history", interval: str = "1d", limit: int = 120) -> dict[str, object]:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol is required")
        max_points = max(1, min(int(limit), 500))
        range_value = "1y" if max_points >= 200 else "6mo" if max_points >= 120 else "3mo" if max_points >= 60 else "1mo"
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(normalized)}"
            f"?interval={urllib.parse.quote(interval)}&range={urllib.parse.quote(range_value)}"
        )
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})

        points: list[dict[str, object]] = []
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = (((payload.get("chart") or {}).get("result") or [None])[0]) if isinstance(payload, dict) else None
            if isinstance(result, dict):
                timestamps = result.get("timestamp") if isinstance(result.get("timestamp"), list) else []
                indicators = result.get("indicators") if isinstance(result.get("indicators"), dict) else {}
                quote = ((indicators.get("quote") or [None])[0]) if isinstance(indicators, dict) else None
                if isinstance(quote, dict):
                    opens = quote.get("open") if isinstance(quote.get("open"), list) else []
                    highs = quote.get("high") if isinstance(quote.get("high"), list) else []
                    lows = quote.get("low") if isinstance(quote.get("low"), list) else []
                    closes = quote.get("close") if isinstance(quote.get("close"), list) else []
                    volumes = quote.get("volume") if isinstance(quote.get("volume"), list) else []
                    count = min(len(timestamps), len(opens), len(highs), len(lows), len(closes))
                    for idx in range(count):
                        ts = timestamps[idx]
                        op = opens[idx]
                        hi = highs[idx]
                        lo = lows[idx]
                        cl = closes[idx]
                        if not all(isinstance(v, (int, float)) for v in [ts, op, hi, lo, cl]):
                            continue
                        point: dict[str, object] = {
                            "ts": datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat(),
                            "open": float(op),
                            "high": float(hi),
                            "low": float(lo),
                            "close": float(cl),
                        }
                        vol = volumes[idx] if idx < len(volumes) else None
                        if isinstance(vol, (int, float)):
                            point["volume"] = float(vol)
                        points.append(point)
        except Exception:
            points = []

        if len(points) > max_points:
            points = points[-max_points:]

        return {
            "symbol": normalized,
            "dataset_id": dataset_id,
            "interval": interval,
            "points": points,
            "backend": "openbb_bridge",
            "openbb_available": self.openbb_available(),
            "updated_at": _utc_now_iso(),
        }
