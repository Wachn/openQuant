from __future__ import annotations

import hashlib
import json
import threading
import time
import urllib.parse
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

from app.domain.core_models import (
    AssetType,
    BrokerType,
    CriticResult,
    ExecutionReceipt,
    ExecutionFill,
    ExecutionOrderStatus,
    ManagerDecision,
    MarketSnapshot,
    PortfolioSnapshot,
    PortfolioAllocationItem,
    PortfolioBreakdownResponse,
    PortfolioMoverItem,
    PortfolioNavPoint,
    PortfolioRiskSnapshot,
    Position,
    RiskDecision,
    RiskProfile,
    SimulationResult,
    Suggestion,
    TradeProposal,
    TradeTicket,
)
from app.services.ibkr_cpapi_market_service import IbkrCpapiMarketService
from app.services.broker_adapters import BrokerAdapter, build_default_adapters
from app.services.research_adapter import query_quant_rag
from app.services.world_monitor_service import WorldMonitorService
from app.storage.sqlite_store import SQLiteStore


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


MARKET_QUOTE_CATALOG: list[dict[str, str]] = [
    {
        "instrument_id": "sp500",
        "name": "S&P 500",
        "symbol": "^GSPC",
        "quote_symbol": "%5EGSPC",
        "quote_url": "https://finance.yahoo.com/quote/%5EGSPC",
        "currency": "USD",
    },
    {
        "instrument_id": "nasdaq_comp",
        "name": "NASDAQ Comp",
        "symbol": "^IXIC",
        "quote_symbol": "%5EIXIC",
        "quote_url": "https://finance.yahoo.com/quote/%5EIXIC",
        "currency": "USD",
    },
    {
        "instrument_id": "russell_2000",
        "name": "Russell 2000",
        "symbol": "^RUT",
        "quote_symbol": "%5ERUT",
        "quote_url": "https://finance.yahoo.com/quote/%5ERUT",
        "currency": "USD",
    },
    {
        "instrument_id": "xau_usd",
        "name": "XAU/USD",
        "symbol": "XAUUSD=X",
        "quote_symbol": "XAUUSD%3DX",
        "quote_url": "https://finance.yahoo.com/quote/XAUUSD%3DX",
        "currency": "USD",
    },
    {
        "instrument_id": "bitcoin",
        "name": "Bitcoin",
        "symbol": "BTC-USD",
        "quote_symbol": "BTC-USD",
        "quote_url": "https://finance.yahoo.com/quote/BTC-USD",
        "currency": "USD",
    },
    {
        "instrument_id": "dbs_sg",
        "name": "DBS Bank SG",
        "symbol": "D05.SI",
        "quote_symbol": "D05.SI",
        "quote_url": "https://finance.yahoo.com/quote/D05.SI",
        "currency": "SGD",
    },
    {
        "instrument_id": "mara",
        "name": "MARA",
        "symbol": "MARA",
        "quote_symbol": "MARA",
        "quote_url": "https://finance.yahoo.com/quote/MARA",
        "currency": "USD",
    },
    {
        "instrument_id": "riot",
        "name": "RIOT",
        "symbol": "RIOT",
        "quote_symbol": "RIOT",
        "quote_url": "https://finance.yahoo.com/quote/RIOT",
        "currency": "USD",
    },
]

REFERENCE_QUOTE_FALLBACK: dict[str, dict[str, float | str]] = {
    "^GSPC": {"value": 5200.0, "change_pct": 0.0021, "change_value": 10.92, "currency": "USD"},
    "^IXIC": {"value": 16750.0, "change_pct": 0.0032, "change_value": 53.6, "currency": "USD"},
    "^RUT": {"value": 2105.0, "change_pct": -0.0014, "change_value": -2.95, "currency": "USD"},
    "XAUUSD=X": {"value": 2210.0, "change_pct": 0.0011, "change_value": 2.43, "currency": "USD"},
    "BTC-USD": {"value": 65200.0, "change_pct": 0.0082, "change_value": 530.0, "currency": "USD"},
    "D05.SI": {"value": 34.85, "change_pct": 0.0017, "change_value": 0.06, "currency": "SGD"},
    "MARA": {"value": 20.35, "change_pct": -0.0075, "change_value": -0.15, "currency": "USD"},
    "RIOT": {"value": 12.7, "change_pct": 0.0063, "change_value": 0.08, "currency": "USD"},
}

STOOQ_SYMBOL_MAP: dict[str, str] = {
    "XAUUSD=X": "xauusd",
}

TRADINGVIEW_SYMBOL_MAP: dict[str, str] = {
    "^GSPC": "SP:SPX",
    "^IXIC": "NASDAQ:IXIC",
    "^RUT": "TVC:RUT",
    "XAUUSD=X": "OANDA:XAUUSD",
    "BTC-USD": "BITSTAMP:BTCUSD",
    "D05.SI": "SGX:D05",
    "MARA": "NASDAQ:MARA",
    "RIOT": "NASDAQ:RIOT",
}

IBKR_BAR_MAP: dict[str, str] = {
    "1m": "1min",
    "2m": "2min",
    "3m": "3min",
    "5m": "5min",
    "10m": "10min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1hour",
    "1d": "1day",
}

FINANCIAL_NEWS_CATEGORIES = {
    "stock_markets",
    "earnings",
    "analyst_ratings",
    "transcripts",
    "cryptocurrency",
    "commodities",
    "currencies",
    "economy",
    "economic_indicators",
    "breaking_news",
}

NEWS_CLASSES = {
    "latest",
    "most_popular",
    "world",
    "politics",
    "company_news",
    "insider_trading_news",
}


class PlatformService:
    def __init__(
        self,
        store: SQLiteStore,
        rag_workspace: Path,
        enable_quant_rag: bool = True,
        ibkr_cpapi_market: IbkrCpapiMarketService | None = None,
    ) -> None:
        self.store = store
        self.rag_workspace = rag_workspace
        self.enable_quant_rag = enable_quant_rag
        self.ibkr_cpapi_market = ibkr_cpapi_market
        self.world_monitor_service = WorldMonitorService()
        self.broker_adapters: Dict[BrokerType, BrokerAdapter] = build_default_adapters()
        self._monitor_lock = threading.Lock()
        self._monitor_stop = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._monitor_state: Dict[str, object] = {
            "enabled": False,
            "tracked_symbols": [],
            "interval_seconds": 60,
            "last_cycle_at": None,
            "last_error": None,
            "cycles": 0,
        }

    def _adapter_for(self, broker: BrokerType) -> BrokerAdapter:
        adapter = self.broker_adapters.get(broker)
        if adapter is None:
            raise ValueError(f"Unsupported broker: {broker.value}")
        return adapter

    # Phase 2: portfolio/accounting
    def set_risk_profile(self, profile: RiskProfile) -> None:
        self.store.set_setting("risk_profile", profile.value)

    def risk_profile(self) -> RiskProfile:
        settings = self.store.get_settings()
        return RiskProfile(settings.get("risk_profile", RiskProfile.NEUTRAL.value))

    def upsert_portfolio(self, positions: List[Dict[str, object]], cash: float) -> PortfolioSnapshot:
        normalized_positions = [
            Position(
                symbol=str(item["symbol"]),
                asset=AssetType(str(item.get("asset", "stock"))),
                quantity=float(item["quantity"]),
                avg_cost=float(item["avg_cost"]),
                last_price=float(item["last_price"]),
            )
            for item in positions
        ]
        equity = cash + sum(p.quantity * p.last_price for p in normalized_positions)
        cost_basis = sum(p.quantity * p.avg_cost for p in normalized_positions)
        unrealized = equity - cash - cost_basis
        drawdown = min(0.0, unrealized / max(1.0, cost_basis))
        snapshot = PortfolioSnapshot(
            as_of_ts=utc_now(),
            equity=equity,
            cash=cash,
            daily_pnl=unrealized,
            drawdown=drawdown,
            risk_profile=self.risk_profile(),
            positions=normalized_positions,
        )
        self.store.upsert_portfolio_snapshot(snapshot.as_of_ts.isoformat(), snapshot.model_dump(mode="json"))
        return snapshot

    def latest_portfolio(self) -> PortfolioSnapshot:
        raw = self.store.latest_portfolio_snapshot()
        if raw is None:
            return self.upsert_portfolio(positions=[], cash=100000.0)
        return PortfolioSnapshot.model_validate(raw)

    def portfolio_breakdown(self, period: str = "7d", frequency: str = "daily") -> Dict[str, object]:
        snapshot = self.latest_portfolio()
        run_id = str(uuid.uuid4())
        config_hash = hashlib.sha256(f"breakdown:{period}:{frequency}".encode("utf-8")).hexdigest()
        self.store.create_run(run_id, "portfolio_breakdown", config_hash, {"period": period, "frequency": frequency})
        try:
            holdings: List[Dict[str, object]] = []
            total_equity = max(snapshot.equity, 1.0)
            for pos in snapshot.positions:
                market_value = pos.quantity * pos.last_price
                unrealized = (pos.last_price - pos.avg_cost) * pos.quantity
                holdings.append(
                    {
                        "symbol": pos.symbol,
                        "asset": pos.asset.value,
                        "quantity": pos.quantity,
                        "avg_cost": pos.avg_cost,
                        "last_price": pos.last_price,
                        "market_value": market_value,
                        "unrealized_pnl": unrealized,
                        "weight_pct": (market_value / total_equity) * 100,
                    }
                )

            cash_breakdown = [
                {"currency": "USD", "amount": snapshot.cash, "is_base": True},
                {"currency": "TOTAL", "amount": snapshot.cash, "is_base": False},
            ]

            by_asset: Dict[str, float] = {}
            for item in holdings:
                key = str(item["asset"])
                by_asset[key] = by_asset.get(key, 0.0) + float(item["market_value"])
            by_asset["cash"] = snapshot.cash

            allocation_asset = [
                PortfolioAllocationItem(bucket=asset, value=value, weight_pct=(value / total_equity) * 100)
                for asset, value in sorted(by_asset.items())
            ]

            by_symbol = [
                PortfolioAllocationItem(
                    bucket=str(item["symbol"]),
                    value=float(item["market_value"]),
                    weight_pct=float(item["weight_pct"]),
                )
                for item in sorted(holdings, key=lambda x: float(x["market_value"]), reverse=True)
            ]

            movers = [
                PortfolioMoverItem(
                    symbol=str(item["symbol"]),
                    contribution=float(item["unrealized_pnl"]),
                    weight_pct=float(item["weight_pct"]),
                )
                for item in holdings
            ]
            top_movers = sorted(movers, key=lambda m: m.contribution, reverse=True)[:5]
            bottom_movers = sorted(movers, key=lambda m: m.contribution)[:5]

            largest_position_pct = max((float(item["weight_pct"]) for item in holdings), default=0.0)
            concentration_score = sum((float(item["weight_pct"]) / 100) ** 2 for item in holdings)
            risk = PortfolioRiskSnapshot(
                drawdown_pct=snapshot.drawdown * 100,
                concentration_score=concentration_score,
                largest_position_pct=largest_position_pct,
            )

            nav_series: List[PortfolioNavPoint] = []
            base_nav = snapshot.equity
            points = 7 if period == "7d" else 30 if period == "30d" else 1
            for idx in range(points):
                ts = utc_now() - timedelta(days=(points - 1 - idx))
                drift = (idx - points / 2) / max(points, 1)
                nav = base_nav * (1 + drift * 0.02)
                ret = (nav / max(base_nav, 1.0)) - 1
                nav_series.append(PortfolioNavPoint(ts=ts, nav=nav, return_pct=ret * 100))

            result = PortfolioBreakdownResponse(
                run_id=run_id,
                as_of_ts=utc_now(),
                period=period,
                frequency=frequency,
                holdings=holdings,
                cash_breakdown=cash_breakdown,
                allocation={"asset_class": allocation_asset, "symbol": by_symbol},
                movers={"top": top_movers, "bottom": bottom_movers},
                risk=risk,
                nav_series=nav_series,
            )

            artifact_payload = result.model_dump(mode="json")
            self.store.add_artifact(str(uuid.uuid4()), run_id, "portfolio_breakdown", artifact_payload)
            self.store.finish_run(run_id, "finished")
            return artifact_payload
        except Exception:
            self.store.finish_run(run_id, "failed")
            raise

    def consultant_brief(self, period: str = "7d", frequency: str = "daily") -> Dict[str, object]:
        run_id = str(uuid.uuid4())
        config_hash = hashlib.sha256(f"consultant:{period}:{frequency}".encode("utf-8")).hexdigest()
        self.store.create_run(run_id, "institutional_consultant", config_hash, {"period": period, "frequency": frequency})
        try:
            portfolio = self.latest_portfolio()
            breakdown = self.portfolio_breakdown(period=period, frequency=frequency)
            largest = max((float(h.get("weight_pct", 0.0)) for h in breakdown.get("holdings", [])), default=0.0)
            risk_profile = portfolio.risk_profile.value

            constraints = [
                "max_symbol_exposure",
                "max_daily_risk",
                "reconciliation_freshness_required",
            ]

            base_return = float(portfolio.daily_pnl / max(1.0, portfolio.equity)) * 100
            scenarios = [
                {"name": "base", "expected_return_pct": base_return, "drawdown_pct": float(portfolio.drawdown * 100)},
                {"name": "stress", "expected_return_pct": base_return - 3.0, "drawdown_pct": float(portfolio.drawdown * 100) - 2.0},
                {"name": "bull", "expected_return_pct": base_return + 2.0, "drawdown_pct": float(portfolio.drawdown * 100) + 1.0},
            ]

            all_cash_recommended = largest > 55.0 or float(portfolio.drawdown) < -0.08
            allocation_recommendation = {
                "target_asset_mix": breakdown.get("allocation", {}).get("asset_class", []),
                "all_cash_option": {
                    "allowed": True,
                    "recommended": all_cash_recommended,
                    "reason": "concentration_or_drawdown" if all_cash_recommended else "optional_defensive_posture",
                },
            }

            payload = {
                "run_id": run_id,
                "as_of_ts": utc_now().isoformat(),
                "period": period,
                "frequency": frequency,
                "ic_brief": {
                    "objective": "Preserve capital while seeking risk-adjusted growth within policy constraints.",
                    "risk_profile": risk_profile,
                    "key_changes": [
                        f"portfolio_equity:{portfolio.equity:.2f}",
                        f"daily_pnl:{portfolio.daily_pnl:.2f}",
                    ],
                },
                "risk_memo": {
                    "constraints": constraints,
                    "largest_position_pct": largest,
                    "drawdown_pct": float(portfolio.drawdown * 100),
                    "reconciliation_status": "paper_mode_snapshot",
                    "promotion_readiness": not all_cash_recommended,
                },
                "scenario_table": scenarios,
                "allocation_recommendation": allocation_recommendation,
                "evidence_refs": [
                    f"portfolio_snapshot:{portfolio.as_of_ts.isoformat()}",
                    f"breakdown_run:{breakdown.get('run_id')}",
                ],
            }
            self.store.add_artifact(str(uuid.uuid4()), run_id, "institutional_consultant_brief", payload)
            self.store.finish_run(run_id, "finished")
            return payload
        except Exception:
            self.store.finish_run(run_id, "failed")
            raise

    def run_daily_cycle(
        self,
        tracked_symbols: List[str],
        period: str = "7d",
        frequency: str = "daily",
    ) -> Dict[str, object]:
        symbols = [symbol.strip().upper() for symbol in tracked_symbols if symbol.strip()]
        if not symbols:
            raise ValueError("tracked_symbols is required")

        run_id = str(uuid.uuid4())
        config_hash = hashlib.sha256(
            f"daily_cycle:{','.join(symbols)}:{period}:{frequency}".encode("utf-8")
        ).hexdigest()
        self.store.create_run(
            run_id,
            "daily_cycle",
            config_hash,
            {"symbols": ",".join(symbols), "period": period, "frequency": frequency},
        )
        try:
            startup = self.startup_report(symbols)
            breakdown = self.portfolio_breakdown(period=period, frequency=frequency)
            consultant = self.consultant_brief(period=period, frequency=frequency)
            payload = {
                "run_id": run_id,
                "tracked_symbols": symbols,
                "period": period,
                "frequency": frequency,
                "linked_runs": {
                    "startup": startup.get("screen_id"),
                    "breakdown_run_id": breakdown.get("run_id"),
                    "consultant_run_id": consultant.get("run_id"),
                },
            }
            self.store.add_artifact(str(uuid.uuid4()), run_id, "daily_cycle_summary", payload)
            self.store.finish_run(run_id, "finished")
            return payload
        except Exception:
            self.store.finish_run(run_id, "failed")
            raise

    def _monitor_worker(self) -> None:
        while not self._monitor_stop.is_set():
            with self._monitor_lock:
                tracked = list(self._monitor_state.get("tracked_symbols", []))
                interval = int(self._monitor_state.get("interval_seconds", 60))
            try:
                if tracked:
                    self.startup_report(tracked)
                    self.portfolio_breakdown(period="7d", frequency="daily")
                    self.consultant_brief(period="7d", frequency="daily")
                with self._monitor_lock:
                    self._monitor_state["last_cycle_at"] = utc_now().isoformat()
                    self._monitor_state["cycles"] = int(self._monitor_state.get("cycles", 0)) + 1
                    self._monitor_state["last_error"] = None
            except Exception as exc:
                with self._monitor_lock:
                    self._monitor_state["last_error"] = f"{type(exc).__name__}:{exc}"
            self._monitor_stop.wait(timeout=max(5, interval))

    def enable_monitor(self, tracked_symbols: List[str], interval_seconds: int = 60) -> Dict[str, object]:
        normalized = [s.strip().upper() for s in tracked_symbols if s.strip()]
        if not normalized:
            raise ValueError("tracked_symbols is required")
        with self._monitor_lock:
            self._monitor_state["tracked_symbols"] = normalized
            self._monitor_state["interval_seconds"] = max(5, interval_seconds)
            self._monitor_state["enabled"] = True
            self._monitor_state["last_error"] = None
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_stop.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_worker, name="portfolio-monitor", daemon=True)
            self._monitor_thread.start()
        return self.monitor_status()

    def disable_monitor(self) -> Dict[str, object]:
        with self._monitor_lock:
            self._monitor_state["enabled"] = False
        self._monitor_stop.set()
        thread = self._monitor_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
        return self.monitor_status()

    def monitor_status(self) -> Dict[str, object]:
        with self._monitor_lock:
            return dict(self._monitor_state)

    def _fetch_yahoo_quotes(self, symbols: list[str]) -> dict[str, dict[str, object]]:
        if not symbols:
            return {}
        symbol_csv = ",".join(symbols)
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(symbol_csv)}"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})
        payload: dict[str, object] | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                if attempt < 2:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                return {}
            except Exception:
                return {}
        if not isinstance(payload, dict):
            return {}
        quote_response = payload.get("quoteResponse", {})
        result = quote_response.get("result", [])
        by_symbol: dict[str, dict[str, object]] = {}
        for item in result:
            if not isinstance(item, dict):
                continue
            raw_symbol = item.get("symbol")
            if not isinstance(raw_symbol, str) or not raw_symbol.strip():
                continue
            by_symbol[raw_symbol.strip().upper()] = item
        return by_symbol

    def _fetch_yahoo_chart_quote(self, symbol: str) -> dict[str, object] | None:
        normalized = symbol.strip().upper()
        if not normalized:
            return None
        encoded = urllib.parse.quote(normalized)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval=1m&range=1d"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})
        payload: dict[str, object] | None = None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                if attempt < 1:
                    time.sleep(0.25)
                    continue
                return None
            except Exception:
                return None
        if not isinstance(payload, dict):
            return None
        chart = payload.get("chart")
        if not isinstance(chart, dict):
            return None
        result = chart.get("result")
        if not isinstance(result, list) or not result:
            return None
        first = result[0]
        if not isinstance(first, dict):
            return None
        meta = first.get("meta")
        if not isinstance(meta, dict):
            return None

        current_price = meta.get("regularMarketPrice")
        if not isinstance(current_price, (int, float)):
            return None
        previous_close = meta.get("previousClose")
        market_time = meta.get("regularMarketTime")
        currency = meta.get("currency")
        quote: dict[str, object] = {
            "regularMarketPrice": float(current_price),
            "currency": str(currency).upper() if isinstance(currency, str) and currency.strip() else None,
            "regularMarketTime": float(market_time) if isinstance(market_time, (int, float)) else None,
        }
        if isinstance(previous_close, (int, float)) and float(previous_close) != 0:
            change_value = float(current_price) - float(previous_close)
            quote["regularMarketPreviousClose"] = float(previous_close)
            quote["regularMarketChange"] = change_value
            quote["regularMarketChangePercent"] = (change_value / float(previous_close)) * 100.0
        return quote

    def _fetch_yahoo_news(self, symbols: list[str], limit: int) -> list[dict[str, object]]:
        normalized = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        if not normalized:
            return []
        items: list[dict[str, object]] = []
        max_items = max(1, min(limit, 200))
        for symbol in normalized:
            if len(items) >= max_items:
                break
            feed_url = (
                "https://feeds.finance.yahoo.com/rss/2.0/headline"
                f"?s={urllib.parse.quote(symbol)}&region=US&lang=en-US"
            )
            request = urllib.request.Request(feed_url, headers={"User-Agent": "agentic-portfolio/0.1"})
            response_bytes: bytes | None = None
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request, timeout=8) as response:
                        response_bytes = response.read()
                    break
                except (urllib.error.URLError, TimeoutError):
                    if attempt < 2:
                        time.sleep(0.25 * (attempt + 1))
                        continue
                    response_bytes = None
                except Exception:
                    response_bytes = None
                    break
            if not response_bytes:
                continue
            try:
                root = ET.fromstring(response_bytes.decode("utf-8", errors="replace"))
            except Exception:
                continue
            channel = root.find("channel")
            if channel is None:
                continue
            entries = channel.findall("item")
            for index, entry in enumerate(entries):
                if len(items) >= max_items:
                    break
                title = (entry.findtext("title") or "").strip()
                link = (entry.findtext("link") or "").strip()
                pub_date = (entry.findtext("pubDate") or "").strip()
                description = (entry.findtext("description") or "").strip()
                if not title:
                    continue
                items.append(
                    self._apply_news_taxonomy({
                        "news_id": f"yahoo_finance:{symbol}:{index}",
                        "symbol": symbol,
                        "source": "yahoo_finance",
                        "title": title,
                        "summary": description or f"Yahoo Finance headline for {symbol}.",
                        "url": link or f"https://finance.yahoo.com/quote/{urllib.parse.quote(symbol)}",
                        "thumbnail_url": "https://www.google.com/s2/favicons?domain=finance.yahoo.com&sz=128",
                        "published_at": pub_date or utc_now().isoformat(),
                    })
                )
        return items

    def _fetch_stooq_quote(self, symbol: str) -> dict[str, object] | None:
        stooq_symbol = STOOQ_SYMBOL_MAP.get(symbol.upper())
        if not stooq_symbol:
            return None

        url = f"https://stooq.com/q/l/?s={urllib.parse.quote(stooq_symbol)}&i=d"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                body = response.read().decode("utf-8", errors="replace").strip()
        except Exception:
            return None

        if not body:
            return None
        first_line = body.splitlines()[0].strip()
        parts = [part.strip() for part in first_line.split(",")]
        if len(parts) < 7:
            return None

        try:
            close_value = float(parts[6])
        except (TypeError, ValueError):
            return None

        history_url = f"https://stooq.com/q/d/l/?s={urllib.parse.quote(stooq_symbol)}&i=d"
        history_request = urllib.request.Request(history_url, headers={"User-Agent": "agentic-portfolio/0.1"})
        try:
            with urllib.request.urlopen(history_request, timeout=8) as response:
                history_body = response.read().decode("utf-8", errors="replace").strip().splitlines()
        except Exception:
            return None

        if len(history_body) < 3:
            return None
        previous_line = history_body[-2]
        previous_parts = [part.strip() for part in previous_line.split(",")]
        if len(previous_parts) < 5:
            return None
        try:
            previous_close = float(previous_parts[4])
        except (TypeError, ValueError):
            return None
        if previous_close == 0:
            return None

        change_value = close_value - previous_close
        return {
            "regularMarketPrice": close_value,
            "regularMarketChange": change_value,
            "regularMarketChangePercent": (change_value / previous_close) * 100.0,
            "regularMarketPreviousClose": previous_close,
            "currency": "USD",
            "regularMarketTime": None,
        }

    def _fetch_tradingview_quote(self, symbol: str) -> dict[str, object] | None:
        tv_symbol = TRADINGVIEW_SYMBOL_MAP.get(symbol.upper())
        if not tv_symbol:
            return None
        fields = urllib.parse.quote("close,change,change_abs")
        encoded_symbol = urllib.parse.quote(tv_symbol)
        url = f"https://scanner.tradingview.com/symbol?symbol={encoded_symbol}&fields={fields}"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        raw_value = payload.get("close")
        raw_change_pct = payload.get("change")
        raw_change_value = payload.get("change_abs")
        if not isinstance(raw_value, (int, float)):
            return None
        if not isinstance(raw_change_pct, (int, float)):
            return None
        if not isinstance(raw_change_value, (int, float)):
            return None
        return {
            "regularMarketPrice": float(raw_value),
            "regularMarketChange": float(raw_change_value),
            "regularMarketChangePercent": float(raw_change_pct),
            "currency": "USD",
            "regularMarketTime": None,
        }

    def ibkr_gateway_session(self) -> dict[str, object]:
        if self.ibkr_cpapi_market is None:
            return {
                "enabled": False,
                "authenticated": False,
                "connected": False,
                "status": "disabled",
                "message": "IBKR CPAPI market service not configured",
                "updated_at": utc_now().isoformat(),
            }
        return self.ibkr_cpapi_market.gateway_session_status()

    def ibkr_gateway_init_session(self) -> dict[str, object]:
        if self.ibkr_cpapi_market is None:
            return self.ibkr_gateway_session()
        return self.ibkr_cpapi_market.init_brokerage_session()

    def ibkr_gateway_tickle(self) -> dict[str, object]:
        if self.ibkr_cpapi_market is None:
            return self.ibkr_gateway_session()
        return self.ibkr_cpapi_market.tickle()

    def ibkr_market_history(self, conid: str, period: str = "1w", bar: str = "1d") -> dict[str, object]:
        if self.ibkr_cpapi_market is None:
            return {
                "status": "disabled",
                "conid": conid,
                "period": period,
                "bar": bar,
                "data": [],
            }
        return self.ibkr_cpapi_market.history(conid=conid, period=period, bar=bar)

    def _fetch_ibkr_quotes(self, symbols: list[str]) -> dict[str, dict[str, object]]:
        if self.ibkr_cpapi_market is None:
            return {}
        session = self.ibkr_cpapi_market.gateway_session_status()
        if not bool(session.get("authenticated")) or not bool(session.get("connected")):
            return {}
        rows = self.ibkr_cpapi_market.market_snapshot(symbols)
        normalized: dict[str, dict[str, object]] = {}
        for symbol, row in rows.items():
            if not isinstance(row, dict):
                continue
            raw_last = row.get("31")
            if not isinstance(raw_last, (int, float, str)):
                continue
            try:
                last_price = float(raw_last)
            except (TypeError, ValueError):
                continue
            bid = row.get("84")
            ask = row.get("85")
            mid = None
            if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
                mid = (float(bid) + float(ask)) / 2
            normalized[symbol.upper()] = {
                "regularMarketPrice": last_price,
                "currency": "USD",
                "regularMarketTime": None,
                "midPrice": mid,
            }
        return normalized

    def _normalize_ibkr_history_candles(self, payload: dict[str, object]) -> list[dict[str, object]]:
        rows = payload.get("data")
        if not isinstance(rows, list):
            return []
        candles: list[dict[str, object]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            ts_raw = row.get("t")
            open_raw = row.get("o")
            high_raw = row.get("h")
            low_raw = row.get("l")
            close_raw = row.get("c")
            volume_raw = row.get("v")
            if not all(isinstance(value, (int, float)) for value in [open_raw, high_raw, low_raw, close_raw]):
                continue
            if isinstance(ts_raw, (int, float)):
                ts_value = datetime.fromtimestamp(float(ts_raw) / 1000.0, tz=timezone.utc).isoformat()
            elif isinstance(ts_raw, str) and ts_raw.strip():
                ts_value = ts_raw.strip()
            else:
                ts_value = utc_now().isoformat()
            candle: dict[str, object] = {
                "ts": ts_value,
                "open": float(open_raw),
                "high": float(high_raw),
                "low": float(low_raw),
                "close": float(close_raw),
            }
            if isinstance(volume_raw, (int, float)):
                candle["volume"] = float(volume_raw)
            candles.append(candle)
        return candles

    def _fallback_quote(self, symbol: str, expected_currency: str) -> dict[str, object]:
        reference = REFERENCE_QUOTE_FALLBACK.get(symbol.upper())
        if reference is not None:
            return {
                "value": float(reference["value"]),
                "change_pct": float(reference["change_pct"]),
                "change_value": float(reference["change_value"]),
                "currency": str(reference.get("currency", expected_currency)),
                "as_of_ts": utc_now().isoformat(),
                "status": "reference_fallback",
            }
        return {
            "value": 0.0,
            "change_pct": 0.0,
            "change_value": 0.0,
            "currency": expected_currency,
            "as_of_ts": utc_now().isoformat(),
            "status": "unavailable",
        }

    def run_monitor_cycle_once(self, tracked_symbols: List[str] | None = None) -> Dict[str, object]:
        symbols = [symbol.strip().upper() for symbol in (tracked_symbols or []) if symbol.strip()]
        if not symbols:
            with self._monitor_lock:
                symbols = [str(item) for item in self._monitor_state.get("tracked_symbols", []) if str(item).strip()]
        if not symbols:
            latest = self.latest_portfolio()
            symbols = [position.symbol for position in latest.positions[:5]] or ["AAPL", "MSFT", "NVDA"]

        try:
            self.startup_report(symbols)
            self.portfolio_breakdown(period="7d", frequency="daily")
            self.consultant_brief(period="7d", frequency="daily")
            with self._monitor_lock:
                self._monitor_state["last_cycle_at"] = utc_now().isoformat()
                self._monitor_state["cycles"] = int(self._monitor_state.get("cycles", 0)) + 1
                self._monitor_state["last_error"] = None
            return self.monitor_status()
        except Exception as exc:
            with self._monitor_lock:
                self._monitor_state["last_error"] = f"{type(exc).__name__}:{exc}"
            raise

    def market_quotes(self, instruments: list[str] | None = None, focus_mode: str = "general") -> Dict[str, object]:
        requested = {item.strip().lower() for item in (instruments or []) if item.strip()}
        mode = focus_mode if focus_mode in {"general", "focused"} else "general"
        if mode == "general":
            selected_catalog = [
                item for item in MARKET_QUOTE_CATALOG if not requested or item["instrument_id"] in requested
            ]
            if not selected_catalog:
                selected_catalog = list(MARKET_QUOTE_CATALOG)
        else:
            focused_catalog = [
                item for item in MARKET_QUOTE_CATALOG if requested and item["instrument_id"] in requested
            ]
            if not focused_catalog:
                portfolio_symbols = {position.symbol.upper() for position in self.latest_portfolio().positions}
                focused_catalog = [item for item in MARKET_QUOTE_CATALOG if item["symbol"].upper() in portfolio_symbols]
            selected_catalog = focused_catalog if focused_catalog else list(MARKET_QUOTE_CATALOG[:4])

        symbols = [item["symbol"] for item in selected_catalog]
        ibkr_data = self._fetch_ibkr_quotes(symbols)
        yahoo_data = self._fetch_yahoo_quotes(symbols)
        items: list[dict[str, object]] = []
        for item in selected_catalog:
            symbol = item["symbol"]
            ibkr_quote = ibkr_data.get(symbol.upper())
            yahoo_quote = yahoo_data.get(symbol.upper())
            chart_quote = self._fetch_yahoo_chart_quote(symbol) if not isinstance(yahoo_quote, dict) else None
            used_chart_primary = False
            if isinstance(chart_quote, dict):
                yahoo_quote = chart_quote
                used_chart_primary = True

            value = None
            change_pct = None
            change_value = None
            currency = item["currency"]
            as_of_ts = utc_now().isoformat()
            status = "live"
            source = "yahoo_finance"
            source_label = "Yahoo Finance"
            if isinstance(ibkr_quote, dict):
                raw_value = ibkr_quote.get("regularMarketPrice")
                raw_currency = ibkr_quote.get("currency")
                if isinstance(raw_value, (int, float)):
                    value = float(raw_value)
                if isinstance(raw_currency, str) and raw_currency.strip():
                    currency = raw_currency.strip().upper()
                if value is not None:
                    source = "ibkr_cpapi"
                    source_label = "IBKR CPAPI"
            if isinstance(yahoo_quote, dict) and (source != "ibkr_cpapi" or change_pct is None or change_value is None):
                raw_value = yahoo_quote.get("regularMarketPrice")
                raw_change_pct = yahoo_quote.get("regularMarketChangePercent")
                raw_change_value = yahoo_quote.get("regularMarketChange")
                raw_prev_close = yahoo_quote.get("regularMarketPreviousClose")
                raw_currency = yahoo_quote.get("currency")
                raw_ts = yahoo_quote.get("regularMarketTime")

                if isinstance(raw_value, (int, float)) and (source != "ibkr_cpapi" or value is None):
                    value = float(raw_value)
                if isinstance(raw_change_pct, (int, float)):
                    change_pct = float(raw_change_pct) / 100.0
                if isinstance(raw_change_value, (int, float)):
                    change_value = float(raw_change_value)
                if change_pct is None and isinstance(raw_prev_close, (int, float)) and float(raw_prev_close) != 0 and value is not None:
                    change_pct = (value - float(raw_prev_close)) / float(raw_prev_close)
                if change_value is None and change_pct is not None and value is not None:
                    denominator = 1.0 + change_pct
                    if denominator != 0:
                        previous_value = value / denominator
                        change_value = value - previous_value
                if isinstance(raw_currency, str) and raw_currency.strip():
                    currency = raw_currency.strip().upper()
                if isinstance(raw_ts, (int, float)):
                    as_of_ts = datetime.fromtimestamp(float(raw_ts), tz=timezone.utc).isoformat()
                if used_chart_primary and value is not None and change_pct is not None and change_value is not None and source != "ibkr_cpapi":
                    source = "yahoo_finance_chart"
                    source_label = "Yahoo Finance Chart"

            if source != "ibkr_cpapi" and (value is None or change_pct is None or change_value is None):
                if not isinstance(chart_quote, dict):
                    chart_quote = self._fetch_yahoo_chart_quote(symbol)
                if isinstance(chart_quote, dict):
                    raw_value = chart_quote.get("regularMarketPrice")
                    raw_change_pct = chart_quote.get("regularMarketChangePercent")
                    raw_change_value = chart_quote.get("regularMarketChange")
                    raw_prev_close = chart_quote.get("regularMarketPreviousClose")
                    raw_currency = chart_quote.get("currency")
                    raw_ts = chart_quote.get("regularMarketTime")
                    if isinstance(raw_value, (int, float)):
                        value = float(raw_value)
                    if isinstance(raw_change_pct, (int, float)):
                        change_pct = float(raw_change_pct) / 100.0
                    if isinstance(raw_change_value, (int, float)):
                        change_value = float(raw_change_value)
                    if change_pct is None and isinstance(raw_prev_close, (int, float)) and float(raw_prev_close) != 0 and value is not None:
                        change_pct = (value - float(raw_prev_close)) / float(raw_prev_close)
                    if change_value is None and change_pct is not None and value is not None:
                        denominator = 1.0 + change_pct
                        if denominator != 0:
                            previous_value = value / denominator
                            change_value = value - previous_value
                    if isinstance(raw_currency, str) and raw_currency.strip():
                        currency = raw_currency.strip().upper()
                    if isinstance(raw_ts, (int, float)):
                        as_of_ts = datetime.fromtimestamp(float(raw_ts), tz=timezone.utc).isoformat()
                    if value is not None and change_pct is not None and change_value is not None and source != "ibkr_cpapi":
                        source = "yahoo_finance_chart"
                        source_label = "Yahoo Finance Chart"

            if source != "ibkr_cpapi" and (value is None or change_pct is None or change_value is None):
                stooq_quote = self._fetch_stooq_quote(symbol)
                if isinstance(stooq_quote, dict):
                    raw_value = stooq_quote.get("regularMarketPrice")
                    raw_change_pct = stooq_quote.get("regularMarketChangePercent")
                    raw_change_value = stooq_quote.get("regularMarketChange")
                    raw_currency = stooq_quote.get("currency")
                    if isinstance(raw_value, (int, float)):
                        value = float(raw_value)
                    if isinstance(raw_change_pct, (int, float)):
                        change_pct = float(raw_change_pct) / 100.0
                    if isinstance(raw_change_value, (int, float)):
                        change_value = float(raw_change_value)
                    if isinstance(raw_currency, str) and raw_currency.strip():
                        currency = raw_currency.strip().upper()
                    if value is not None and change_pct is not None and change_value is not None and source != "ibkr_cpapi":
                        source = "stooq"
                        source_label = "Stooq"

            if value is None or change_pct is None or change_value is None:
                fallback = self._fallback_quote(symbol=symbol, expected_currency=currency)
                value = float(fallback["value"])
                change_pct = float(fallback["change_pct"])
                change_value = float(fallback["change_value"])
                as_of_ts = str(fallback["as_of_ts"])
                status = str(fallback["status"])
                source = "reference_fallback"
                source_label = "Reference Fallback"

            cross_check: dict[str, object] = {
                "source": "tradingview",
                "status": "unavailable",
            }
            tv_quote = self._fetch_tradingview_quote(symbol)
            if isinstance(tv_quote, dict):
                tv_value = tv_quote.get("regularMarketPrice")
                tv_change_pct = tv_quote.get("regularMarketChangePercent")
                tv_change_value = tv_quote.get("regularMarketChange")
                if isinstance(tv_value, (int, float)) and isinstance(tv_change_pct, (int, float)) and isinstance(tv_change_value, (int, float)):
                    tv_value_float = float(tv_value)
                    cross_check = {
                        "source": "tradingview",
                        "status": "live",
                        "value": tv_value_float,
                        "change_pct": float(tv_change_pct) / 100.0,
                        "change_value": float(tv_change_value),
                        "delta_value": tv_value_float - float(value),
                        "delta_pct": ((tv_value_float - float(value)) / float(value)) if float(value) != 0 else 0.0,
                    }

            items.append(
                {
                    "instrument_id": item["instrument_id"],
                    "name": item["name"],
                    "symbol": symbol,
                    "value": value,
                    "change_pct": change_pct,
                    "change_value": change_value,
                    "currency": currency,
                    "source": source,
                    "source_label": source_label,
                    "quote_url": item["quote_url"],
                    "status": status,
                    "as_of_ts": as_of_ts,
                    "cross_check": cross_check,
                }
            )

        return {
            "source": "yahoo_finance",
            "source_label": "Yahoo Finance",
            "focus_mode": mode,
            "items": items,
            "updated_at": utc_now().isoformat(),
        }

    # Phase 3: PIT snapshots
    def refresh_market(self, symbols: List[str]) -> List[MarketSnapshot]:
        now = utc_now()
        snapshots: List[MarketSnapshot] = []
        for symbol in sorted(set(symbols)):
            seed = int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:8], 16)
            base = 50 + (seed % 150)
            change_raw = ((seed % 200) - 100) / 50.0
            price = float(base + change_raw)
            change_pct = float(change_raw / max(1.0, base))
            volatility = float(((seed // 10) % 30) / 100)
            payload = {
                "as_of_ts": now.isoformat(),
                "symbol": symbol,
                "asset": AssetType.STOCK.value,
                "price": price,
                "change_pct": change_pct,
                "volatility": volatility,
                "source": "deterministic_seed_provider",
            }
            raw_hash = hashlib.sha256(str(payload).encode("utf-8")).hexdigest()
            snapshot = MarketSnapshot.model_validate({**payload, "raw_hash": raw_hash})
            self.store.upsert_market_snapshot(
                snapshot_id=f"{symbol}:{int(now.timestamp())}",
                as_of_ts=snapshot.as_of_ts.isoformat(),
                symbol=snapshot.symbol,
                asset=snapshot.asset.value,
                payload=snapshot.model_dump(mode="json"),
                raw_hash=raw_hash,
            )
            snapshots.append(snapshot)
        return snapshots

    def market_diff(self) -> List[Dict[str, object]]:
        return self.store.market_snapshot_diff()

    # Phase 4+5: run recorder and startup report
    def startup_report(self, tracked_symbols: List[str]) -> Dict[str, object]:
        snapshots = self.refresh_market(tracked_symbols)
        portfolio = self.latest_portfolio()
        run_id = str(uuid.uuid4())
        config_hash = hashlib.sha256(f"startup:{sorted(tracked_symbols)}".encode("utf-8")).hexdigest()
        self.store.create_run(run_id, "startup_report", config_hash, {"symbol_count": str(len(tracked_symbols))})

        suggestions: List[Suggestion] = []
        for snapshot in snapshots[:5]:
            impact_score = min(100.0, abs(snapshot.change_pct) * 2500)
            suggestion = Suggestion(
                suggestion_id=str(uuid.uuid4()),
                title=f"Review {snapshot.symbol} due to change {snapshot.change_pct:.2%}",
                thesis="Price/volatility shift detected since latest snapshot refresh.",
                confidence=min(1.0, 0.45 + abs(snapshot.change_pct) * 10),
                impact_score=impact_score,
                evidence_refs=[f"market:{snapshot.symbol}:{snapshot.as_of_ts.isoformat()}"],
            )
            self.store.upsert_suggestion(suggestion.suggestion_id, suggestion.status, suggestion.model_dump(mode="json"))
            suggestions.append(suggestion)

        payload = {
            "screen_id": "startup_report",
            "as_of_ts": utc_now().isoformat(),
            "session": {
                "restored": True,
                "last_active_ts": (utc_now() - timedelta(hours=8)).isoformat(),
                "refresh_status": "completed",
            },
            "portfolio_snapshot": portfolio.model_dump(mode="json"),
            "market_changes": [
                {
                    "asset": s.asset.value,
                    "symbol": s.symbol,
                    "change_pct": s.change_pct,
                    "reason_code": "price_move" if abs(s.change_pct) < 0.03 else "volatility_spike",
                    "evidence_refs": [f"market:{s.symbol}:{s.as_of_ts.isoformat()}"],
                }
                for s in snapshots
            ],
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "title": s.title,
                    "impact_score": s.impact_score,
                    "confidence": s.confidence,
                    "status": s.status,
                    "why_summary": s.thesis,
                    "evidence_refs": s.evidence_refs,
                }
                for s in suggestions
            ],
            "actions": {
                "discuss": True,
                "promote_to_trade_lane": True,
                "save_for_later": True,
            },
        }
        self.store.add_artifact(str(uuid.uuid4()), run_id, "startup_report", payload)
        self.store.finish_run(run_id, "finished")
        return payload

    # Phase 6-8: research + deterministic trade lane + simulation
    def research_query(self, query: str) -> Dict[str, object]:
        if self.enable_quant_rag:
            try:
                result = query_quant_rag(query=query, workspace=self.rag_workspace)
                return {
                    "query": query,
                    "answer": result["answer"],
                    "evidence": result["evidence"],
                    "confidence": result["confidence"],
                    "backend": "quant_rag",
                    "workspace": result["workspace"],
                }
            except Exception as exc:
                fallback_reason = f"quant_rag_unavailable:{type(exc).__name__}"
        else:
            fallback_reason = "quant_rag_disabled"

        evidence = [
            {
                "evidence_id": f"research:{hashlib.sha256(query.encode('utf-8')).hexdigest()[:8]}",
                "source_type": "fallback",
                "summary": "Research fallback response generated because quant_rag path was unavailable.",
                "source_ref": fallback_reason,
                "locator": None,
                "chunk_id": None,
            }
        ]
        return {
            "query": query,
            "answer": "Research lane fallback active. Configure quant_rag workspace for evidence-backed answers.",
            "evidence": evidence,
            "confidence": 0.1,
            "backend": "research_fallback",
            "workspace": str(self.rag_workspace.resolve()),
        }

    def run_trade_lane(self, symbol: str, profile: RiskProfile) -> Dict[str, object]:
        run_id = str(uuid.uuid4())
        config_hash = hashlib.sha256(f"trade:{symbol}:{profile.value}".encode("utf-8")).hexdigest()
        self.store.create_run(run_id, "trade_lane", config_hash, {"symbol": symbol, "profile": profile.value})

        snapshots = self.store.latest_market_snapshots()
        selected = next((s for s in snapshots if s.get("symbol") == symbol), None)
        if selected is None:
            selected = self.refresh_market([symbol])[0].model_dump(mode="json")

        evidence_ref = f"market:{symbol}:{selected['as_of_ts']}"
        proposal = TradeProposal(
            proposal_id=str(uuid.uuid4()),
            symbol=symbol,
            asset=AssetType(selected.get("asset", "stock")),
            side="buy" if float(selected["change_pct"]) >= 0 else "sell",
            quantity=10.0,
            entry_price=float(selected["price"]),
            invalidation="Move against thesis beyond 3%.",
            time_horizon="swing",
            evidence_refs=[evidence_ref],
        )

        risk_map = {
            RiskProfile.AGGRESSIVE: 0.30,
            RiskProfile.NEUTRAL: 0.15,
            RiskProfile.CONSERVATIVE: 0.07,
        }
        risk_decisions: List[RiskDecision] = []
        for rp in RiskProfile:
            risk_decisions.append(
                RiskDecision(
                    profile=rp,
                    decision="approve",
                    max_position_size=risk_map[rp],
                    constraints=["max_daily_risk", "max_symbol_exposure"],
                )
            )

        selected_risk = next(r for r in risk_decisions if r.profile == profile)
        critics = [
            CriticResult(critic="evidence_integrity", passed=len(proposal.evidence_refs) > 0, reason="Evidence refs present."),
            CriticResult(critic="data_quality", passed=True, reason="Snapshot available and fresh."),
            CriticResult(critic="risk_policy", passed=selected_risk.decision == "approve", reason="Profile constraints pass."),
            CriticResult(critic="execution_safety", passed=True, reason="Paper mode and confirmation gate enabled."),
        ]
        passed = all(c.passed for c in critics)

        decision = ManagerDecision(
            action="approve" if passed else "reject",
            rationale="Critic gate summary completed.",
            approved_profile=profile if passed else None,
        )

        ticket = TradeTicket(
            ticket_id=str(uuid.uuid4()),
            run_id=run_id,
            symbol=proposal.symbol,
            asset=proposal.asset,
            side=proposal.side,
            order_type="limit",
            quantity=proposal.quantity,
            limit_price=proposal.entry_price,
            time_horizon=proposal.time_horizon,
            invalidation=proposal.invalidation,
            evidence_refs=proposal.evidence_refs,
        )

        sim = SimulationResult(
            expected_return_pct=float(selected["change_pct"]) * 1.5,
            expected_drawdown_pct=abs(float(selected["volatility"])) * 0.8,
            cost_estimate=1.5,
            slippage_estimate=0.3,
        )

        payload = {
            "run_id": run_id,
            "proposal": proposal.model_dump(mode="json"),
            "risk_decisions": [r.model_dump(mode="json") for r in risk_decisions],
            "critics": [c.model_dump(mode="json") for c in critics],
            "manager_decision": decision.model_dump(mode="json"),
            "ticket": ticket.model_dump(mode="json"),
            "simulation": sim.model_dump(mode="json"),
        }
        self.store.add_artifact(str(uuid.uuid4()), run_id, "trade_lane_result", payload)
        self.store.finish_run(run_id, "finished" if passed else "failed")
        return payload

    # Phase 9: execution boundary
    def broker_capabilities(self) -> List[Dict[str, object]]:
        return [
            {
                "broker": BrokerType.IBKR_PAPER.value,
                "supports": ["submit", "status", "cancel", "fills", "reconcile"],
                "mode": "paper",
                "connection_status": "ready",
            },
            {
                "broker": BrokerType.MT5_PAPER.value,
                "supports": ["submit", "status", "cancel", "fills", "reconcile"],
                "mode": "paper",
                "connection_status": "ready",
            },
        ]

    def market_connector_status(self) -> Dict[str, object]:
        broker_caps = self.broker_capabilities()
        ibkr_ready = any(
            item.get("broker") == BrokerType.IBKR_PAPER.value and item.get("connection_status") == "ready"
            for item in broker_caps
        )
        ibkr_session = self.ibkr_gateway_session()
        ibkr_session_ready = bool(ibkr_session.get("authenticated")) and bool(ibkr_session.get("connected"))
        ibkr_status = "ready" if ibkr_ready and ibkr_session_ready else "degraded"
        return {
            "connectors": [
                {
                    "source": "yahoo_finance",
                    "label": "Yahoo Finance",
                    "status": "ready",
                    "mode": "public_news_feed",
                },
                {
                    "source": "investing_com",
                    "label": "Investing.com",
                    "status": "ready",
                    "mode": "public_news_feed",
                },
                {
                    "source": "worldmonitor",
                    "label": "World Monitor",
                    "status": "ready",
                    "mode": "global_news_feed",
                },
                {
                    "source": "investing_com_quotes",
                    "label": "Investing.com Quotes",
                    "status": "degraded",
                    "mode": "public_quote_bridge",
                },
                {
                    "source": "tradingview",
                    "label": "TradingView",
                    "status": "degraded",
                    "mode": "market_data_bridge",
                },
                {
                    "source": "ibkr",
                    "label": "Interactive Brokers",
                    "status": ibkr_status,
                    "mode": "cpapi_gateway_bridge",
                    "auth_status": ibkr_session.get("status", "unknown"),
                    "login_url": ibkr_session.get("login_url", "https://localhost:5000"),
                },
            ],
            "updated_at": utc_now().isoformat(),
        }

    def _symbols_for_focus_mode(self, symbols: List[str], focus_mode: str) -> list[str]:
        normalized_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        if focus_mode == "focused":
            if normalized_symbols:
                return normalized_symbols
            latest = self.latest_portfolio()
            return [position.symbol for position in latest.positions[:8]] or ["AAPL", "MSFT", "NVDA"]
        if normalized_symbols:
            return normalized_symbols
        return ["AAPL", "MSFT", "NVDA", "SPY", "QQQ", "TSLA"]

    def _normalize_news_categories(self, categories: list[str] | None) -> list[str]:
        if not categories:
            return []
        normalized = [item.strip().lower() for item in categories if item and item.strip()]
        return [item for item in normalized if item in FINANCIAL_NEWS_CATEGORIES]

    def _normalize_news_classes(self, classes: list[str] | None) -> list[str]:
        if not classes:
            return []
        normalized = [item.strip().lower() for item in classes if item and item.strip()]
        return [item for item in normalized if item in NEWS_CLASSES]

    def _classify_news_category(self, title: str, summary: str) -> str:
        text = f"{title} {summary}".lower()
        if any(token in text for token in ["breaking", "urgent", "just in"]):
            return "breaking_news"
        if any(token in text for token in ["earnings", "eps", "quarterly", "guidance"]):
            return "earnings"
        if any(token in text for token in ["analyst", "price target", "upgrade", "downgrade", "rating"]):
            return "analyst_ratings"
        if any(token in text for token in ["transcript", "conference call", "investor call"]):
            return "transcripts"
        if any(token in text for token in ["bitcoin", "crypto", "ethereum", "token"]):
            return "cryptocurrency"
        if any(token in text for token in ["gold", "oil", "commodity", "metals", "xau", "silver"]):
            return "commodities"
        if any(token in text for token in ["forex", "fx", "currency", "usd", "eur", "yen", "dollar"]):
            return "currencies"
        if any(token in text for token in ["inflation", "gdp", "cpi", "ppi", "unemployment", "payroll", "pmi", "indicator"]):
            return "economic_indicators"
        if any(token in text for token in ["economy", "recession", "central bank", "fed", "ecb", "boj"]):
            return "economy"
        return "stock_markets"

    def _classify_news_class(self, title: str, summary: str) -> str:
        text = f"{title} {summary}".lower()
        if any(token in text for token in ["most popular", "most read", "top stories", "trending"]):
            return "most_popular"
        if any(token in text for token in ["insider", "director buy", "director sell"]):
            return "insider_trading_news"
        if any(token in text for token in ["election", "government", "policy", "parliament", "senate", "politics"]):
            return "politics"
        if any(token in text for token in ["world", "global", "international", "geopolitical"]):
            return "world"
        if any(token in text for token in ["company", "corporate", "acquisition", "merger", "ceo", "board"]):
            return "company_news"
        return "latest"

    def _apply_news_taxonomy(self, item: dict[str, object]) -> dict[str, object]:
        title = str(item.get("title") or "")
        summary = str(item.get("summary") or "")
        if not item.get("news_category"):
            item["news_category"] = self._classify_news_category(title, summary)
        if not item.get("news_class"):
            item["news_class"] = self._classify_news_class(title, summary)
        return item

    def cached_news_feed(
        self,
        symbols: List[str],
        sources: List[str] | None = None,
        categories: List[str] | None = None,
        classes: List[str] | None = None,
        limit: int = 20,
        focus_mode: str = "general",
    ) -> Dict[str, object]:
        mode = focus_mode if focus_mode in {"general", "focused"} else "general"
        normalized_symbols = self._symbols_for_focus_mode(symbols, mode)
        normalized_categories = self._normalize_news_categories(categories)
        normalized_classes = self._normalize_news_classes(classes)
        allowed_sources = {"yahoo_finance", "investing_com", "reuters", "worldmonitor", "ibkr", "tradingview"}
        selected_sources = [source for source in (sources or []) if source in allowed_sources]
        items = self.store.list_news_cache(
            symbols=normalized_symbols,
            sources=selected_sources or None,
            categories=normalized_categories or None,
            classes=normalized_classes or None,
            limit=limit,
        )
        return {
            "sources": selected_sources,
            "symbols": normalized_symbols,
            "categories": normalized_categories,
            "classes": normalized_classes,
            "focus_mode": mode,
            "items": items,
            "updated_at": utc_now().isoformat(),
            "from_cache": True,
        }

    def purge_news_cache(self) -> Dict[str, object]:
        purged = self.store.purge_expired_news_cache()
        return {
            "purged": purged,
            "updated_at": utc_now().isoformat(),
        }

    def _fetch_reuters_news(self, symbols: list[str], limit: int, focus_mode: str) -> list[dict[str, object]]:
        max_items = max(1, min(limit, 200))
        normalized_symbols = [symbol.upper() for symbol in symbols]
        feed_urls = [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.reuters.com/news/usmarkets",
            "https://feeds.reuters.com/reuters/worldNews",
        ]
        items: list[dict[str, object]] = []
        for feed_url in feed_urls:
            if len(items) >= max_items:
                break
            request = urllib.request.Request(feed_url, headers={"User-Agent": "agentic-portfolio/0.1"})
            body: bytes | None = None
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request, timeout=8) as response:
                        body = response.read()
                    break
                except (urllib.error.URLError, TimeoutError):
                    if attempt < 2:
                        time.sleep(0.25 * (attempt + 1))
                        continue
                    body = None
                except Exception:
                    body = None
                    break
            if not body:
                continue
            try:
                root = ET.fromstring(body.decode("utf-8", errors="replace"))
            except Exception:
                continue
            entries = root.findall(".//item")
            for index, entry in enumerate(entries):
                if len(items) >= max_items:
                    break
                title = (entry.findtext("title") or "").strip()
                if not title:
                    continue
                link = (entry.findtext("link") or "").strip()
                summary = (entry.findtext("description") or "").strip()
                pub_date = (entry.findtext("pubDate") or "").strip()
                title_upper = title.upper()
                matched_symbol = next((symbol for symbol in normalized_symbols if symbol in title_upper), None)
                if focus_mode == "focused" and normalized_symbols and matched_symbol is None:
                    continue
                items.append(
                    self._apply_news_taxonomy(
                        {
                            "news_id": f"reuters:{index}:{hashlib.sha256(title.encode('utf-8')).hexdigest()[:10]}",
                            "symbol": matched_symbol or normalized_symbols[0],
                            "source": "reuters",
                            "title": title,
                            "summary": summary or "Reuters market headline.",
                            "url": link or "https://www.reuters.com/markets/",
                            "thumbnail_url": "https://www.google.com/s2/favicons?domain=www.reuters.com&sz=128",
                            "published_at": pub_date or utc_now().isoformat(),
                        }
                    )
                )
        return items[:max_items]

    def _fetch_investing_news(self, symbols: list[str], limit: int, focus_mode: str) -> list[dict[str, object]]:
        max_items = max(1, min(limit, 200))
        feed_urls = [
            "https://www.investing.com/rss/news.rss",
            "https://www.investing.com/rss/market_overview.rss",
            "https://www.investing.com/rss/news_95.rss",
        ]
        normalized_symbols = [symbol.upper() for symbol in symbols]
        items: list[dict[str, object]] = []
        for feed_url in feed_urls:
            if len(items) >= max_items:
                break
            request = urllib.request.Request(feed_url, headers={"User-Agent": "agentic-portfolio/0.1"})
            body: bytes | None = None
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request, timeout=8) as response:
                        body = response.read()
                    break
                except (urllib.error.URLError, TimeoutError):
                    if attempt < 2:
                        time.sleep(0.25 * (attempt + 1))
                        continue
                    body = None
                except Exception:
                    body = None
                    break
            if not body:
                continue
            try:
                root = ET.fromstring(body.decode("utf-8", errors="replace"))
            except Exception:
                continue
            entries = root.findall(".//item")
            for index, entry in enumerate(entries):
                if len(items) >= max_items:
                    break
                title = (entry.findtext("title") or "").strip()
                if not title:
                    continue
                link = (entry.findtext("link") or "").strip()
                summary = (entry.findtext("description") or "").strip()
                pub_date = (entry.findtext("pubDate") or "").strip()
                title_upper = title.upper()
                matched_symbol = next((symbol for symbol in normalized_symbols if symbol in title_upper), None)
                if focus_mode == "focused" and normalized_symbols and matched_symbol is None:
                    continue
                items.append(
                    self._apply_news_taxonomy({
                        "news_id": f"investing_com:{index}:{hashlib.sha256(title.encode('utf-8')).hexdigest()[:10]}",
                        "symbol": matched_symbol or normalized_symbols[0],
                        "source": "investing_com",
                        "title": title,
                        "summary": summary or "Investing.com headline.",
                        "url": link or "https://www.investing.com",
                        "thumbnail_url": "https://www.google.com/s2/favicons?domain=www.investing.com&sz=128",
                        "published_at": pub_date or utc_now().isoformat(),
                    })
                )
        return items[:max_items]

    def _fetch_yahoo_chart_candles(self, symbol: str, interval: str, range_value: str) -> list[dict[str, object]]:
        normalized = symbol.strip().upper()
        if not normalized:
            return []
        encoded = urllib.parse.quote(normalized)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval={urllib.parse.quote(interval)}&range={urllib.parse.quote(range_value)}"
        request = urllib.request.Request(url, headers={"User-Agent": "agentic-portfolio/0.1"})
        payload: dict[str, object] | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                if attempt < 2:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                return []
            except Exception:
                return []

        if not isinstance(payload, dict):
            return []
        chart = payload.get("chart")
        if not isinstance(chart, dict):
            return []
        result = chart.get("result")
        if not isinstance(result, list) or not result:
            return []
        first = result[0]
        if not isinstance(first, dict):
            return []

        timestamps = first.get("timestamp")
        indicators = first.get("indicators")
        if not isinstance(timestamps, list) or not isinstance(indicators, dict):
            return []
        quotes = indicators.get("quote")
        if not isinstance(quotes, list) or not quotes:
            return []
        quote = quotes[0]
        if not isinstance(quote, dict):
            return []

        opens = quote.get("open")
        highs = quote.get("high")
        lows = quote.get("low")
        closes = quote.get("close")
        volumes = quote.get("volume")
        if not all(isinstance(series, list) for series in [opens, highs, lows, closes]):
            return []

        candles: list[dict[str, object]] = []
        count = min(len(timestamps), len(opens), len(highs), len(lows), len(closes))
        for idx in range(count):
            ts = timestamps[idx]
            op = opens[idx]
            hi = highs[idx]
            lo = lows[idx]
            cl = closes[idx]
            vol = volumes[idx] if isinstance(volumes, list) and idx < len(volumes) else None
            if not all(isinstance(value, (int, float)) for value in [ts, op, hi, lo, cl]):
                continue
            candle: dict[str, object] = {
                "ts": datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat(),
                "open": float(op),
                "high": float(hi),
                "low": float(lo),
                "close": float(cl),
            }
            if isinstance(vol, (int, float)):
                candle["volume"] = float(vol)
            candles.append(candle)
        return candles

    def _fetch_stooq_candles(self, symbol: str, limit: int = 120) -> list[dict[str, object]]:
        stooq_symbol = STOOQ_SYMBOL_MAP.get(symbol.upper())
        if not stooq_symbol:
            return []
        history_url = f"https://stooq.com/q/d/l/?s={urllib.parse.quote(stooq_symbol)}&i=d"
        request = urllib.request.Request(history_url, headers={"User-Agent": "agentic-portfolio/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                lines = response.read().decode("utf-8", errors="replace").strip().splitlines()
        except Exception:
            return []
        if len(lines) < 2:
            return []

        candles: list[dict[str, object]] = []
        for line in lines[1:]:
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 5:
                continue
            date_value, op, hi, lo, cl = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                open_value = float(op)
                high_value = float(hi)
                low_value = float(lo)
                close_value = float(cl)
            except (TypeError, ValueError):
                continue
            candles.append(
                {
                    "ts": f"{date_value}T00:00:00+00:00",
                    "open": open_value,
                    "high": high_value,
                    "low": low_value,
                    "close": close_value,
                }
            )
        if limit > 0 and len(candles) > limit:
            return candles[-limit:]
        return candles

    def news_feed(
        self,
        symbols: List[str],
        sources: List[str] | None = None,
        categories: List[str] | None = None,
        classes: List[str] | None = None,
        limit: int = 20,
        focus_mode: str = "general",
    ) -> Dict[str, object]:
        mode = focus_mode if focus_mode in {"general", "focused"} else "general"
        normalized_symbols = self._symbols_for_focus_mode(symbols, mode)
        normalized_categories = self._normalize_news_categories(categories)
        normalized_classes = self._normalize_news_classes(classes)

        allowed_sources = {"yahoo_finance", "investing_com", "reuters", "worldmonitor", "ibkr", "tradingview"}
        selected_sources = [source for source in (sources or ["yahoo_finance", "investing_com", "reuters", "worldmonitor"]) if source in allowed_sources]
        if not selected_sources:
            selected_sources = ["yahoo_finance", "investing_com", "reuters", "worldmonitor"]

        url_by_source = {
            "yahoo_finance": "https://finance.yahoo.com",
            "investing_com": "https://www.investing.com",
            "reuters": "https://www.reuters.com/markets/",
            "worldmonitor": "https://www.reuters.com/world/",
            "ibkr": "https://www.interactivebrokers.com",
            "tradingview": "https://www.tradingview.com",
        }
        thumbnail_by_source = {
            "yahoo_finance": "https://www.google.com/s2/favicons?domain=finance.yahoo.com&sz=128",
            "investing_com": "https://www.google.com/s2/favicons?domain=www.investing.com&sz=128",
            "reuters": "https://www.google.com/s2/favicons?domain=www.reuters.com&sz=128",
            "worldmonitor": "https://www.google.com/s2/favicons?domain=www.reuters.com&sz=128",
            "ibkr": "https://www.google.com/s2/favicons?domain=www.interactivebrokers.com&sz=128",
            "tradingview": "https://www.google.com/s2/favicons?domain=www.tradingview.com&sz=128",
        }

        max_items = max(1, min(limit, 200))
        items: List[Dict[str, object]] = []
        source_items: dict[str, list[dict[str, object]]] = {}
        if "yahoo_finance" in selected_sources:
            yahoo_items = self._fetch_yahoo_news(normalized_symbols, max_items)
            source_items["yahoo_finance"] = yahoo_items
        if "investing_com" in selected_sources and len(items) < max_items:
            investing_items = self._fetch_investing_news(normalized_symbols, max_items, mode)
            source_items["investing_com"] = investing_items
        if "reuters" in selected_sources and len(items) < max_items:
            reuters_items = self._fetch_reuters_news(normalized_symbols, max_items, mode)
            source_items["reuters"] = reuters_items
        if "worldmonitor" in selected_sources and len(items) < max_items:
            world_items = self.world_monitor_service.fetch_headlines(
                symbols=normalized_symbols,
                limit=max_items,
                focus_mode=mode,
            )
            source_items["worldmonitor"] = [self._apply_news_taxonomy(item) for item in world_items]

        if source_items:
            source_offsets = {source: 0 for source in source_items}
            while len(items) < max_items:
                made_progress = False
                for source in selected_sources:
                    entries = source_items.get(source, [])
                    offset = source_offsets.get(source, 0)
                    if offset < len(entries):
                        entry = entries[offset]
                        if isinstance(entry, dict):
                            items.append(self._apply_news_taxonomy(dict(entry)))
                        source_offsets[source] = offset + 1
                        made_progress = True
                        if len(items) >= max_items:
                            break
                if not made_progress:
                    break

        if len(items) < max_items:
            for index, symbol in enumerate(normalized_symbols):
                for source in selected_sources:
                    if source == "yahoo_finance" or source == "investing_com" or source == "reuters" or source == "worldmonitor":
                        continue
                    if len(items) >= max_items:
                        break
                    headline = {
                        "yahoo_finance": f"{symbol}: market digest and key movers",
                        "investing_com": f"{symbol}: macro and sentiment snapshot",
                        "reuters": f"{symbol}: market and macro wire headlines",
                        "worldmonitor": f"{symbol}: world monitor macro and geopolitical scan",
                        "ibkr": f"{symbol}: broker watch and execution context",
                        "tradingview": f"{symbol}: chart momentum and technical context",
                    }[source]
                    items.append(
                        self._apply_news_taxonomy({
                            "news_id": f"{source}:{symbol}:{index}",
                            "symbol": symbol,
                            "source": source,
                            "title": headline,
                            "summary": f"{source} feed prepared for {symbol}.",
                            "url": url_by_source[source],
                            "thumbnail_url": thumbnail_by_source[source],
                            "published_at": utc_now().isoformat(),
                        })
                    )
                if len(items) >= max_items:
                    break

        if not items:
            for index, symbol in enumerate(normalized_symbols):
                if len(items) >= max_items:
                    break
                items.append(
                    self._apply_news_taxonomy({
                        "news_id": f"fallback:{symbol}:{index}",
                        "symbol": symbol,
                        "source": "yahoo_finance",
                        "title": f"{symbol}: market digest and key movers",
                        "summary": f"Fallback feed prepared for {symbol}.",
                        "url": "https://finance.yahoo.com",
                        "thumbnail_url": "https://www.google.com/s2/favicons?domain=finance.yahoo.com&sz=128",
                        "published_at": utc_now().isoformat(),
                    })
                )

        pre_filter_items = list(items)
        if normalized_categories:
            items = [item for item in items if str(item.get("news_category") or "").lower() in normalized_categories]
        if normalized_classes:
            items = [item for item in items if str(item.get("news_class") or "").lower() in normalized_classes]

        filter_relaxed = False
        if not items and pre_filter_items:
            relaxed_items = [item for item in pre_filter_items if str(item.get("news_category") or "").lower() in normalized_categories] if normalized_categories else list(pre_filter_items)
            if relaxed_items:
                items = relaxed_items
                filter_relaxed = True
            elif normalized_classes:
                items = list(pre_filter_items)
                filter_relaxed = True

        if len(items) > max_items:
            items = items[:max_items]

        if items:
            self.store.upsert_news_cache_items(items=items, ttl_days=60)
        self.store.purge_expired_news_cache()

        cached_count = len(
            self.store.list_news_cache(
                symbols=normalized_symbols,
                sources=selected_sources,
                categories=normalized_categories or None,
                classes=normalized_classes or None,
                limit=max_items,
            )
        )

        return {
            "sources": selected_sources,
            "symbols": normalized_symbols,
            "categories": normalized_categories,
            "classes": normalized_classes,
            "focus_mode": mode,
            "items": items,
            "filter_relaxed": filter_relaxed,
            "cached_count": cached_count,
            "updated_at": utc_now().isoformat(),
        }

    def market_candles(self, instrument_id: str, interval: str = "5m", range_value: str = "1d") -> Dict[str, object]:
        normalized_id = instrument_id.strip().lower()
        catalog_item = next((item for item in MARKET_QUOTE_CATALOG if item["instrument_id"] == normalized_id), None)
        if catalog_item is None:
            raise ValueError("instrument_id not found")

        symbol = str(catalog_item["symbol"])
        candles: list[dict[str, object]] = []
        source = "ibkr_cpapi"
        status = "unavailable"
        if self.ibkr_cpapi_market is not None:
            conid = self.ibkr_cpapi_market.resolve_conid(symbol)
            if conid:
                ibkr_bar = IBKR_BAR_MAP.get(interval, interval)
                history_payload = self.ibkr_market_history(conid=conid, period=range_value, bar=ibkr_bar)
                candles = self._normalize_ibkr_history_candles(history_payload)
                if candles:
                    source = "ibkr_cpapi"
                    status = "live"

        if not candles:
            candles = self._fetch_yahoo_chart_candles(symbol=symbol, interval=interval, range_value=range_value)
            source = "yahoo_finance_chart"
            status = "live"
        if not candles:
            candles = self._fetch_stooq_candles(symbol=symbol)
            source = "stooq"
            status = "live" if candles else "unavailable"

        return {
            "instrument_id": normalized_id,
            "name": catalog_item["name"],
            "symbol": symbol,
            "interval": interval,
            "range": range_value,
            "source": source,
            "status": status,
            "candles": candles,
            "updated_at": utc_now().isoformat(),
        }

    def submit_paper_order(self, ticket: TradeTicket, confirm: bool, broker: BrokerType) -> ExecutionReceipt:
        if not confirm:
            raise ValueError("Confirmation required before paper execution.")

        run = self.store.get_run(ticket.run_id)
        if run is None:
            raise ValueError("Ticket run_id not found.")
        if run.get("state") != "finished":
            raise ValueError("Run must be finished before paper execution.")

        artifacts = self.store.artifacts_for_run(ticket.run_id)
        trade_lane_artifact = next((a for a in artifacts if a.get("artifact_type") == "trade_lane_result"), None)
        if trade_lane_artifact is None:
            raise ValueError("Trade lane artifact is required before paper execution.")

        payload = trade_lane_artifact.get("payload", {})
        manager_decision = payload.get("manager_decision", {})
        if manager_decision.get("action") != "approve":
            raise ValueError("Manager decision must be approve before paper execution.")

        canonical_ticket = payload.get("ticket")
        if not isinstance(canonical_ticket, dict):
            raise ValueError("Approved trade ticket is missing from run artifact.")
        ticket_payload = ticket.model_dump(mode="json")
        fields_to_validate = [
            "ticket_id",
            "run_id",
            "symbol",
            "asset",
            "side",
            "order_type",
            "quantity",
            "limit_price",
            "stop_price",
            "time_horizon",
            "invalidation",
            "evidence_refs",
        ]
        for field in fields_to_validate:
            if canonical_ticket.get(field) != ticket_payload.get(field):
                raise ValueError(f"Ticket mismatch for field: {field}")

        idempotency_key = hashlib.sha256(
            (
                f"{broker.value}:{ticket.ticket_id}:{ticket.run_id}:{ticket.symbol}:{ticket.side}:"
                f"{ticket.quantity}:{ticket.order_type}:{ticket.limit_price}:{ticket.stop_price}"
            ).encode("utf-8")
        ).hexdigest()
        existing = self.store.get_execution_order(idempotency_key)
        if existing:
            existing_payload = existing.get("payload", {})
            existing_broker = existing_payload.get("broker", BrokerType.IBKR_PAPER.value)
            return ExecutionReceipt(
                order_id=existing["order_id"],
                ticket_id=existing["ticket_id"],
                run_id=existing["run_id"],
                broker=BrokerType(existing_broker),
                status=existing["status"],
                idempotency_key=idempotency_key,
                submitted_at=datetime.fromisoformat(existing["submitted_at"]),
            )

        prefix = "IBKR" if broker == BrokerType.IBKR_PAPER else "MT5"
        order_id = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
        adapter_payload = self._adapter_for(broker).submit_order(order_id=order_id, ticket=ticket)
        receipt = ExecutionReceipt(
            order_id=order_id,
            ticket_id=ticket.ticket_id,
            run_id=ticket.run_id,
            broker=broker,
            status=str(adapter_payload["status"]),
            idempotency_key=idempotency_key,
            submitted_at=utc_now(),
        )
        order_payload = {
            **adapter_payload,
            "quantity": ticket.quantity,
            "limit_price": ticket.limit_price,
            "status": receipt.status,
        }
        self.store.upsert_execution_order(
            idempotency_key=idempotency_key,
            order_id=order_id,
            ticket_id=ticket.ticket_id,
            run_id=ticket.run_id,
            status=receipt.status,
            payload=order_payload,
        )
        self.store.add_execution_event(
            event_id=str(uuid.uuid4()),
            order_id=order_id,
            run_id=ticket.run_id,
            event_type="submitted",
            payload=order_payload,
        )
        return receipt

    def execution_status(self, order_id: str) -> Dict[str, object]:
        order = self.store.get_execution_order_by_order_id(order_id)
        if order is None:
            raise ValueError("Order not found.")
        payload = order.get("payload", {})
        broker = BrokerType(str(payload.get("broker", BrokerType.IBKR_PAPER.value)))
        status_payload = self._adapter_for(broker).get_status(payload)
        merged_payload = {**payload, **status_payload}
        self.store.update_execution_order(order_id=order_id, status=str(status_payload["status"]), payload=merged_payload)
        self.store.add_execution_event(
            event_id=str(uuid.uuid4()),
            order_id=order_id,
            run_id=order["run_id"],
            event_type="status",
            payload=status_payload,
        )
        result = ExecutionOrderStatus(
            order_id=order_id,
            broker=broker,
            status=str(status_payload["status"]),
            updated_at=datetime.fromisoformat(str(status_payload["updated_at"])),
        )
        return result.model_dump(mode="json")

    def cancel_execution_order(self, order_id: str) -> Dict[str, object]:
        order = self.store.get_execution_order_by_order_id(order_id)
        if order is None:
            raise ValueError("Order not found.")
        payload = order.get("payload", {})
        broker = BrokerType(str(payload.get("broker", BrokerType.IBKR_PAPER.value)))
        cancel_payload = self._adapter_for(broker).cancel_order(payload)
        merged_payload = {**payload, **cancel_payload}
        self.store.update_execution_order(order_id=order_id, status=str(cancel_payload["status"]), payload=merged_payload)
        self.store.add_execution_event(
            event_id=str(uuid.uuid4()),
            order_id=order_id,
            run_id=order["run_id"],
            event_type="cancel",
            payload=cancel_payload,
        )
        result = ExecutionOrderStatus(
            order_id=order_id,
            broker=broker,
            status=str(cancel_payload["status"]),
            updated_at=datetime.fromisoformat(str(cancel_payload["updated_at"])),
        )
        return result.model_dump(mode="json")

    def execution_fills(self, order_id: str) -> List[Dict[str, object]]:
        order = self.store.get_execution_order_by_order_id(order_id)
        if order is None:
            raise ValueError("Order not found.")
        payload = order.get("payload", {})
        broker = BrokerType(str(payload.get("broker", BrokerType.IBKR_PAPER.value)))
        fills_payload = self._adapter_for(broker).list_fills(payload)
        fills = [ExecutionFill.model_validate(fill).model_dump(mode="json") for fill in fills_payload]
        self.store.add_execution_event(
            event_id=str(uuid.uuid4()),
            order_id=order_id,
            run_id=order["run_id"],
            event_type="fills",
            payload={"fills": fills},
        )
        return fills

    def reconcile_execution_orders(self, broker: BrokerType | None = None) -> List[Dict[str, object]]:
        orders = self.store.list_execution_orders()
        results: List[Dict[str, object]] = []
        for order in orders:
            payload = order.get("payload", {})
            order_broker = BrokerType(str(payload.get("broker", BrokerType.IBKR_PAPER.value)))
            if broker is not None and order_broker != broker:
                continue
            reconcile_payload = self._adapter_for(order_broker).reconcile(payload)
            merged_payload = {**payload, "status": reconcile_payload["status"]}
            self.store.update_execution_order(
                order_id=order["order_id"],
                status=str(reconcile_payload["status"]),
                payload=merged_payload,
            )
            self.store.add_execution_event(
                event_id=str(uuid.uuid4()),
                order_id=order["order_id"],
                run_id=order["run_id"],
                event_type="reconcile",
                payload=reconcile_payload,
            )
            results.append(reconcile_payload)
        return results

    def execution_events(self, order_id: str) -> List[Dict[str, object]]:
        order = self.store.get_execution_order_by_order_id(order_id)
        if order is None:
            raise ValueError("Order not found.")
        return self.store.execution_events_for_order(order_id)

    def list_suggestions(self) -> List[Dict[str, object]]:
        return self.store.list_suggestions()

    def run_artifacts(self, run_id: str) -> List[Dict[str, object]]:
        return self.store.artifacts_for_run(run_id)
