# Agentic Portfolio Backend

`projects/agentic_portfolio` is the FastAPI backend for the Portfolio Agent product. It provides runtime chat/session orchestration, portfolio/research/trade APIs, provider and gateway integration, OpenClaw-inspired routing surfaces, and audit-oriented execution boundaries.

## Setup and Run

```bash
cd projects/agentic_portfolio
uv venv
uv pip install -e .
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/settings`

## Core API Groups

- System: `/health`, `/settings`, `/capabilities`
- Runtime workspace: `/runtime/chat/sessions/*`, `/runtime/change-requests/*`, `/runtime/agents/*`
- Provider and model gateway: `/runtime/providers/*`, `/session/*`, `/auth/*`
- Portfolio/trading: `/portfolio`, `/startup-report`, `/trade-lane/run`, `/execution/*`
- Market/news/gateway: `/market/*`, `/news/*`, `/gateway/*`
- OpenClaw-style feature surfaces: `/openclaw/*`, `/agent-router/*`, `/world-monitor/feed`, `/open-data/*`, `/open-stock/*`

Reference-integrated feature endpoints:

- World monitor: `/world-monitor/feed`, `/world-monitor/sources`
- Open data: `/open-data/datasets`, `/open-data/overview`, `/open-data/series`
- Open stock: `/open-stock/search`, `/open-stock/catalog`, `/open-stock/snapshot`, `/open-stock/reference`
- OpenClaw runtime surfaces: `/openclaw/settings`, `/openclaw/heartbeat`, `/openclaw/cron`
- Finnhub and TradingView support: `/finnhub/status`, `/finnhub/search`, `/finnhub/company-news`, `/finnhub/tradingview/widgets`, `/finnhub/webhook`

## Runtime Model

- `suzybae` is the primary human-facing runtime gateway agent.
- `runtime_supervisor` handles route-level orchestration and safe handoffs.
- Execution remains confirmation-gated and paper-first by default.

## Testing

```bash
cd projects/agentic_portfolio
uv run pytest tests/test_end_to_end.py
```

## Environment Variables (Common)

- `AGENTIC_PORTFOLIO_ENV` (default `dev`)
- `AGENTIC_PORTFOLIO_DATA_DIR` (default `./workspace`)
- `AGENTIC_PORTFOLIO_HOST` (default `127.0.0.1`)
- `AGENTIC_PORTFOLIO_PORT` (default `8000`)
- Provider credentials and broker/channel credentials as required by your selected integrations
- `AGENTIC_PORTFOLIO_FINNHUB_API_KEY`
- `AGENTIC_PORTFOLIO_FINNHUB_WEBHOOK_SECRET`
- `AGENTIC_PORTFOLIO_FINNHUB_PUBLIC_WEBHOOK_BASE_URL` or `AGENTIC_PORTFOLIO_FINNHUB_NGROK_URL`

## Finnhub Local Webhook Notes

- Keep Finnhub credentials in local env only; do not commit them.
- Use a public HTTPS tunnel such as ngrok for local webhook testing.
- Configure Finnhub to call `<public-url>/finnhub/webhook`.
- The backend validates the `X-Finnhub-Secret` header and responds with a 2xx acknowledgement payload.
