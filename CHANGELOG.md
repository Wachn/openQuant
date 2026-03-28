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
