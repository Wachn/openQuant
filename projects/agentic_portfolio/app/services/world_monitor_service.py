from __future__ import annotations

import hashlib
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


class WorldMonitorService:
    """World-monitor style global headline collector.

    This keeps implementation lightweight while mirroring the reference idea of
    multi-feed global monitoring with graceful fallback.
    """

    FEEDS: list[tuple[str, str]] = [
        ("reuters_world", "https://feeds.reuters.com/reuters/worldNews"),
        ("reuters_business", "https://feeds.reuters.com/reuters/businessNews"),
        ("investing_global", "https://www.investing.com/rss/news.rss"),
    ]

    def fetch_headlines(
        self,
        symbols: list[str],
        limit: int = 20,
        focus_mode: str = "general",
    ) -> list[dict[str, object]]:
        max_items = max(1, min(int(limit), 200))
        mode = focus_mode if focus_mode in {"general", "focused"} else "general"
        normalized_symbols = [item.strip().upper() for item in symbols if isinstance(item, str) and item.strip()]
        if not normalized_symbols:
            normalized_symbols = ["AAPL", "MSFT", "NVDA"]

        items: list[dict[str, object]] = []
        for feed_key, feed_url in self.FEEDS:
            if len(items) >= max_items:
                break
            request = urllib.request.Request(feed_url, headers={"User-Agent": "agentic-portfolio/0.1"})
            try:
                with urllib.request.urlopen(request, timeout=8) as response:
                    raw = response.read()
            except Exception:
                continue

            try:
                root = ET.fromstring(raw)
            except Exception:
                continue

            entries = root.findall(".//item")
            for entry in entries:
                if len(items) >= max_items:
                    break

                title = html.unescape((entry.findtext("title") or "").strip())
                if not title:
                    continue
                link = (entry.findtext("link") or "").strip()
                summary = html.unescape(_strip_html(entry.findtext("description") or ""))
                published_at = (entry.findtext("pubDate") or "").strip() or _utc_now_iso()

                title_upper = title.upper()
                symbol = next((candidate for candidate in normalized_symbols if candidate in title_upper), None)
                if mode == "focused" and symbol is None:
                    macro_tokens = ("GLOBAL", "WORLD", "ECONOMY", "CENTRAL BANK", "INFLATION", "GEOPOLITICAL")
                    if not any(token in title_upper for token in macro_tokens):
                        continue

                chosen_symbol = symbol or normalized_symbols[0]
                digest = hashlib.sha256(f"{feed_key}:{title}:{published_at}".encode("utf-8")).hexdigest()[:12]
                items.append(
                    {
                        "news_id": f"worldmonitor:{feed_key}:{digest}",
                        "symbol": chosen_symbol,
                        "source": "worldmonitor",
                        "news_category": "economy",
                        "news_class": "world",
                        "title": title,
                        "summary": summary or "World monitor headline.",
                        "url": link or "https://www.reuters.com/world/",
                        "thumbnail_url": "https://www.google.com/s2/favicons?domain=www.reuters.com&sz=128",
                        "published_at": published_at,
                        "world_source": feed_key,
                    }
                )

        if items:
            return items[:max_items]

        fallback: list[dict[str, object]] = []
        for index, symbol in enumerate(normalized_symbols):
            if len(fallback) >= max_items:
                break
            fallback.append(
                {
                    "news_id": f"worldmonitor:fallback:{symbol}:{index}",
                    "symbol": symbol,
                    "source": "worldmonitor",
                    "news_category": "economy",
                    "news_class": "world",
                    "title": f"Global monitor: {symbol} macro risk scan",
                    "summary": "Fallback world-monitor snapshot pending live feeds.",
                    "url": "https://www.reuters.com/world/",
                    "thumbnail_url": "https://www.google.com/s2/favicons?domain=www.reuters.com&sz=128",
                    "published_at": _utc_now_iso(),
                    "world_source": "fallback",
                }
            )
        return fallback[:max_items]
