from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpenStockService:
    DEFAULT_CATALOG = [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "exchange": "NASDAQ", "type": "Equity"},
    ]

    def search(self, query: str, limit: int = 10) -> dict[str, object]:
        q = query.strip()
        if not q:
            raise ValueError("query is required")
        max_items = max(1, min(int(limit), 50))

        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(q)}"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})
        items: list[dict[str, object]] = []

        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            quotes = payload.get("quotes", []) if isinstance(payload, dict) else []
            if isinstance(quotes, list):
                for entry in quotes:
                    if not isinstance(entry, dict):
                        continue
                    symbol = str(entry.get("symbol") or "").upper()
                    if not symbol:
                        continue
                    items.append(
                        {
                            "symbol": symbol,
                            "name": entry.get("shortname") or entry.get("longname") or symbol,
                            "exchange": entry.get("exchDisp") or entry.get("exchange") or "-",
                            "type": entry.get("typeDisp") or entry.get("quoteType") or "-",
                            "score": float(entry.get("score") or 0.0),
                        }
                    )
        except Exception:
            items = []

        if not items:
            upper_q = q.upper()
            items = [
                row
                for row in self.DEFAULT_CATALOG
                if upper_q in str(row.get("symbol", "")).upper() or upper_q in str(row.get("name", "")).upper()
            ]

        return {
            "query": q,
            "items": items[:max_items],
            "backend": "openstock_bridge",
            "updated_at": _utc_now_iso(),
        }

    def snapshot(self, symbols: list[str], limit: int = 20) -> dict[str, object]:
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
                            "exchange": entry.get("fullExchangeName") or entry.get("exchange") or "-",
                            "type": entry.get("quoteType") or "-",
                            "currency": entry.get("currency") or "USD",
                            "price": float(entry.get("regularMarketPrice") or 0.0),
                            "change_pct": float(entry.get("regularMarketChangePercent") or 0.0),
                            "market_cap": float(entry.get("marketCap") or 0.0),
                            "volume": float(entry.get("regularMarketVolume") or 0.0),
                        }
                    )
        except Exception:
            items = []

        if not items:
            for symbol in selected:
                catalog_item = next((row for row in self.DEFAULT_CATALOG if row["symbol"] == symbol), None)
                items.append(
                    {
                        "symbol": symbol,
                        "name": catalog_item["name"] if catalog_item else symbol,
                        "exchange": catalog_item["exchange"] if catalog_item else "-",
                        "type": catalog_item["type"] if catalog_item else "Equity",
                        "currency": "USD",
                        "price": 0.0,
                        "change_pct": 0.0,
                        "market_cap": 0.0,
                        "volume": 0.0,
                    }
                )

        return {
            "symbols": selected,
            "items": items[:max_items],
            "backend": "openstock_bridge",
            "updated_at": _utc_now_iso(),
        }
