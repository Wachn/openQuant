# Portfolio Agent

This repo is building a Windows-first agentic portfolio management system:

- monitor markets + portfolio state
- generate evidence-linked suggestions and reports
- promote decisions into a deterministic trade lane when execution is requested
- connect to brokers (paper-first) behind safety gates

Key idea: two lanes

- Research lane: flexible, exploratory analysis (advisory).
- Trade lane: deterministic, typed DAG with critic gates (execution-capable).

## Repo layout

- `projects/desktop_app/`: Tauri + React desktop app.
- `projects/agentic_portfolio/`: FastAPI backend (operator loop, artifacts, broker boundaries).
- `projects/quant_rag/`: local-first RAG scaffold (evidence-backed research).

## Where to read next

- Main docs hub: `docs/README.md`
- Product proposal and workflows: `docs/proposals/agentic_portfolio_mvp_proposal.md`
- Latest plan snapshot list: `docs/plans/PLAN_VERSION_LOG.md`
- Recent change log index: `docs/changes/INDEX.md`

If you're working with coding agents (OpenCode), start with:

- `.opencode/README.md`
