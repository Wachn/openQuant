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
        {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "NFLX", "name": "Netflix Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "ADBE", "name": "Adobe Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "AMD", "name": "Advanced Micro Devices Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "INTC", "name": "Intel Corporation", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "QCOM", "name": "QUALCOMM Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "AVGO", "name": "Broadcom Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "CSCO", "name": "Cisco Systems Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "PEP", "name": "PepsiCo Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "COST", "name": "Costco Wholesale Corporation", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "TMUS", "name": "T-Mobile US Inc.", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "SBUX", "name": "Starbucks Corporation", "exchange": "NASDAQ", "type": "Equity"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "BAC", "name": "Bank of America Corporation", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "WFC", "name": "Wells Fargo & Company", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "GS", "name": "Goldman Sachs Group Inc.", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "V", "name": "Visa Inc.", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "MA", "name": "Mastercard Incorporated", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "PFE", "name": "Pfizer Inc.", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "UNH", "name": "UnitedHealth Group Incorporated", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "XOM", "name": "Exxon Mobil Corporation", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "CVX", "name": "Chevron Corporation", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "BA", "name": "Boeing Company", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "KO", "name": "Coca-Cola Company", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "MCD", "name": "McDonald's Corporation", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "DIS", "name": "Walt Disney Company", "exchange": "NYSE", "type": "Equity"},
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust", "exchange": "NASDAQ", "type": "ETF"},
        {"symbol": "IWM", "name": "iShares Russell 2000 ETF", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average ETF Trust", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "ARKK", "name": "ARK Innovation ETF", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "XLF", "name": "Financial Select Sector SPDR Fund", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "XLK", "name": "Technology Select Sector SPDR Fund", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "XLE", "name": "Energy Select Sector SPDR Fund", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "GLD", "name": "SPDR Gold Shares", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "SLV", "name": "iShares Silver Trust", "exchange": "NYSEARCA", "type": "ETF"},
        {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "exchange": "NASDAQ", "type": "ETF"},
        {"symbol": "HYG", "name": "iShares iBoxx $ High Yield Corporate Bond ETF", "exchange": "NYSEARCA", "type": "ETF"},
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

    def catalog(
        self,
        query: str | None = None,
        exchange: str | None = None,
        stock_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, object]:
        filtered = self.DEFAULT_CATALOG
        search = (query or "").strip().upper()
        normalized_exchange = (exchange or "").strip().upper()
        normalized_type = (stock_type or "").strip().upper()

        if search:
            filtered = [
                row
                for row in filtered
                if search in str(row.get("symbol", "")).upper() or search in str(row.get("name", "")).upper()
            ]
        if normalized_exchange and normalized_exchange != "ALL":
            filtered = [row for row in filtered if str(row.get("exchange", "")).upper() == normalized_exchange]
        if normalized_type and normalized_type != "ALL":
            filtered = [row for row in filtered if str(row.get("type", "")).upper() == normalized_type]

        sorted_rows = sorted(filtered, key=lambda row: str(row.get("symbol", "")))
        total = len(sorted_rows)
        normalized_offset = max(0, int(offset))
        max_items = max(1, min(int(limit), 200))
        paged = sorted_rows[normalized_offset:normalized_offset + max_items]

        return {
            "items": paged,
            "total": total,
            "offset": normalized_offset,
            "limit": max_items,
            "backend": "openstock_bridge",
            "updated_at": _utc_now_iso(),
        }

    def reference(self, symbol: str) -> dict[str, object]:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol is required")

        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(normalized)}"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})

        detail: dict[str, object] | None = None
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            results = ((payload.get("quoteResponse") or {}).get("result") or []) if isinstance(payload, dict) else []
            if isinstance(results, list) and results:
                entry = results[0] if isinstance(results[0], dict) else {}
                if isinstance(entry, dict):
                    detail = {
                        "symbol": normalized,
                        "name": entry.get("longName") or entry.get("shortName") or normalized,
                        "exchange": entry.get("fullExchangeName") or entry.get("exchange") or "-",
                        "type": entry.get("quoteType") or "-",
                        "currency": entry.get("currency") or "USD",
                        "price": float(entry.get("regularMarketPrice") or 0.0),
                        "change_pct": float(entry.get("regularMarketChangePercent") or 0.0),
                        "day_high": float(entry.get("regularMarketDayHigh") or 0.0),
                        "day_low": float(entry.get("regularMarketDayLow") or 0.0),
                        "year_high": float(entry.get("fiftyTwoWeekHigh") or 0.0),
                        "year_low": float(entry.get("fiftyTwoWeekLow") or 0.0),
                        "market_cap": float(entry.get("marketCap") or 0.0),
                        "volume": float(entry.get("regularMarketVolume") or 0.0),
                        "website": f"https://finance.yahoo.com/quote/{normalized}",
                    }
        except Exception:
            detail = None

        if detail is None:
            catalog_item = next((row for row in self.DEFAULT_CATALOG if row["symbol"] == normalized), None)
            detail = {
                "symbol": normalized,
                "name": catalog_item["name"] if catalog_item else normalized,
                "exchange": catalog_item["exchange"] if catalog_item else "-",
                "type": catalog_item["type"] if catalog_item else "Equity",
                "currency": "USD",
                "price": 0.0,
                "change_pct": 0.0,
                "day_high": 0.0,
                "day_low": 0.0,
                "year_high": 0.0,
                "year_low": 0.0,
                "market_cap": 0.0,
                "volume": 0.0,
                "website": f"https://finance.yahoo.com/quote/{normalized}",
            }

        peers = [
            row
            for row in self.DEFAULT_CATALOG
            if row.get("symbol") != normalized and row.get("exchange") == detail.get("exchange")
        ][:6]

        return {
            "item": detail,
            "peers": peers,
            "backend": "openstock_bridge",
            "updated_at": _utc_now_iso(),
        }
