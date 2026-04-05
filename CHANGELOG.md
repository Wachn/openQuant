# Changelog

## 2026-03-28 - v0.2.0 WorldMonitor/OpenData/OpenStock/OpenClaw Integration Pass

- Expanded World Monitor backend with source listing endpoint and richer item metadata for UI classification.
- Expanded Open Stock backend with `/open-stock/reference` for detailed symbol cards and peer context.
- Expanded Open Stock backend with `/open-stock/catalog` for filterable stock discovery and browsing.
- Improved Open Data backend series behavior with deterministic fallback points when live upstream data is unavailable.
- Added OpenClaw-style `/openclaw/settings`, `/openclaw/heartbeat`, and `/openclaw/cron` runtime surfaces and connected them to the desktop UI.
- Reworked desktop Research GUI panels so World Monitor, Open Data, and Open Stock are directly usable with visible controls, stock catalog browsing, and candlestick rendering.
- Wired new GUI actions to backend endpoints for inspect/reference workflows, source visibility, and runtime settings monitoring.
- Updated README documentation across root, backend, and desktop projects to reflect implemented feature surfaces.

## 2026-03-28 - Runtime Dashboard and News Cache Recovery

- Fixed duplicate-safe news cache persistence so repeated `/news/feed` refreshes no longer fail on `news_cache.news_id` collisions.
- Fixed ChatGPT-backed OpenAI runtime behavior so SuzyBae retries from `codex-mini-latest` to `gpt-5.3-codex` when the account rejects Codex Mini.
- Expanded the OpenStock monitoring UI with a monitor board, watchlist-linked news grid, and portfolio-linked inspection flow.
- Added Anthropic-inspired skill pattern references to `.opencode/skills/` for reusable OpenCode skill development.

## 2026-03-29 - OpenStock Advancement and Finnhub Integration Layer

- Added an OpenStock feature-advancement report under `docs/changes/2026-03-29_openstock_feature_advancement_report.md`.
- Added a safe env-backed Finnhub service layer with status, symbol lookup, company news, market status, TradingView widget config, and webhook acknowledgement routes.
- Added desktop Finnhub + TradingView workspace surfaces for lookup, status, heatmap, market quotes, advanced chart, and timeline widgets.
- Documented ngrok-style local webhook usage without committing secrets.
