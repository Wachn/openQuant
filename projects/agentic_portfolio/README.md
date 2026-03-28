# Agentic Portfolio (Phase 1 Foundation)

This project contains the Phase 1 backend foundation for the agentic portfolio manager.

Current scope:

- FastAPI service skeleton
- health and settings API endpoints
- local SQLite persistence scaffold
- startup initialization flow

## Quick start

From repository root:

```bash
cd projects/agentic_portfolio
uv venv
uv pip install -e .
uvicorn app.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/settings`
- `http://127.0.0.1:8000/docs`

## Environment variables

- `AGENTIC_PORTFOLIO_ENV` (default: `dev`)
- `AGENTIC_PORTFOLIO_DATA_DIR` (default: `./workspace`)
- `AGENTIC_PORTFOLIO_HOST` (default: `127.0.0.1`)
- `AGENTIC_PORTFOLIO_PORT` (default: `8000`)

## API (Phase 1)

- `GET /health`: service status and startup metadata
- `GET /settings`: app config and persisted app settings
- `PUT /settings/{key}`: persist one setting key/value
- `POST /route`: dynamic lane/workflow routing decision for a user message

## API (End-to-end backend scaffold)

- `PUT /portfolio`: upsert canonical portfolio snapshot input
- `GET /portfolio`: latest portfolio snapshot
- `PUT /risk-profile/{profile}`: set active risk profile
- `POST /startup-report`: run refresh + report + suggestion generation
- `POST /research/query`: research lane query output
- `POST /trade-lane/run`: deterministic L1-L5 style run output + critics + simulation
- `POST /execution/paper-submit`: idempotent paper submission boundary
- `GET /suggestions`: list suggestion queue
- `GET /runs/{run_id}/artifacts`: fetch run artifacts

Example route request:

```json
{
  "message": "propose a rebalance for my portfolio",
  "source": "chat",
  "automation_enabled": false,
  "include_internal_plan": false
}
```

## Notes

This is infrastructure-only scaffolding for Phase 1.
No trading, risk, or deterministic DAG execution is implemented yet.
