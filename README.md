# Portfolio Agent

Portfolio Agent is a local-first agentic portfolio platform with a desktop operator cockpit and a FastAPI backend. It combines research workflows, deterministic trade-lane controls, and broker-safe execution boundaries with OpenClaw-style routing, skills/gateway scaffolding, world-monitor news integration, and stock/open-data research surfaces.

Current integrated feature surfaces:

- World monitor feed + source registry APIs with GUI controls for symbols, focus mode, and feed limits.
- Open data APIs for datasets, quote overview, and historical series with GUI dataset/series rendering.
- Open stock APIs for search, snapshots, and reference cards with peer context, connected to GUI inspect actions.

## Repository Structure

- `projects/agentic_portfolio/` - FastAPI backend APIs, runtime orchestration, provider/gateway routing, trade-lane and portfolio services.
- `projects/desktop_app/` - Tauri + React operator UI.
- `projects/quant_rag/` - Local-first RAG scaffold for evidence-backed research.
- `runtime_agents/` - Runtime agent specifications. `suzybae` is the main human-facing gateway agent.

## Quick Start

### 1) Run Backend

```bash
cd projects/agentic_portfolio
uv venv
uv pip install -e .
uvicorn app.main:app --reload
```

Backend endpoints:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/settings`

### 2) Run Desktop UI

```bash
cd projects/desktop_app
npm install
npm run dev
```

Optional desktop shell runtime:

```bash
npm run tauri dev
```

## Verification Commands

```bash
cd projects/agentic_portfolio
uv run pytest tests/test_end_to_end.py

cd ../desktop_app
npm run build
```

## Documentation

- `AGENTS.md` - repository engineering and runtime guidance.
- `projects/agentic_portfolio/README.md` - backend setup, API groups, and operations.
- `projects/desktop_app/README.md` - frontend/desktop run instructions.
- `runtime_agents/README.md` - runtime agent contracts and delegation model.
