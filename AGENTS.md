# AGENTS.md

This repository is organized around agent-assisted development for a portfolio management product.

Current implemented code:
- `projects/quant_rag/` (Python local-first RAG scaffold)
- `projects/agentic_portfolio/` (FastAPI backend with end-to-end operator and trade-lane scaffold)
- `projects/desktop_app/` (Tauri + React desktop shell)

Planned product:
- Agentic portfolio manager with deterministic trade DAG, IBKR paper execution, and plugin extensions (OpenClaw-style runtime host).

## Start Here

- Read `README.md` for top-level project entry.
- Backend setup/run: `projects/agentic_portfolio/README.md`.
- Desktop setup/run: `projects/desktop_app/README.md`.
- Runtime agent contracts: `runtime_agents/README.md`.

## Repository Rules For Coding Agents

- Keep changes scoped and minimal.
- Prefer explicit, typed interfaces over implicit dictionaries.
- Preserve evidence and auditability in any trade-related flow.
- Never commit secrets or tokens.
- Do not add broker live-trading paths unless explicitly requested.

## Cursor / Copilot Rules

No repo-specific Cursor or Copilot instruction files are currently enforced in this repo.

## Build, Lint, Test (Project: quant_rag)

From repo root:

```bash
cd projects/quant_rag
```

Environment setup (recommended):

```bash
uv venv
uv pip install -r requirements.txt
```

Run ingest/query CLI:

```bash
uv run python -m app.cli ingest --input ./my_data --workspace ./workspace
uv run python -m app.cli query --workspace ./workspace "What are the main risks?"
uv run python -m app.cli query --workspace ./workspace --llm openai "Summarize with citations"
```

There is no committed test suite yet. When tests are added, use:

```bash
pytest
pytest tests/test_file.py
pytest tests/test_file.py -k test_name
pytest -k "pattern" -q
```

If you prefer `uv run`:

```bash
uv run pytest
uv run pytest tests/test_file.py -k test_name
```

## Build, Lint, Test (Project: agentic_portfolio)

From repo root:

```bash
cd projects/agentic_portfolio
```

Environment setup:

```bash
uv venv
uv pip install -e .
```

Run backend:

```bash
uvicorn app.main:app --reload
```

Quick verify endpoints:

```bash
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/settings').read().decode())"
```

Test commands:

```bash
uv run pytest
uv run pytest tests/test_end_to_end.py
```

## Build, Lint, Test (Project: desktop_app)

From repo root:

```bash
cd projects/desktop_app
```

Environment setup:

```bash
npm install
```

Run frontend dev server:

```bash
npm run dev
```

Build frontend:

```bash
npm run build
```

Check tauri CLI:

```bash
npm run tauri -- --version
```

## Code Style Baseline (Current Python Code)

Imports and modules:
- Import order: stdlib, third-party, local.
- Internal modules use package-relative imports in `rag/*`.
- Keep one logical responsibility per module.

Formatting:
- 4-space indentation.
- Keep lines readable (target about 100 chars).
- Avoid noisy comments; add comments only where behavior is non-obvious.

Typing:
- Type all public function signatures.
- Prefer concrete `dataclass` models for structured records.
- Keep return types explicit for tool/agent boundaries.

Naming:
- Files/functions/variables: `snake_case`.
- Classes: `PascalCase`.
- Constants: `SCREAMING_SNAKE_CASE`.

Error handling:
- Fail fast on invalid configuration.
- Wrap external integrations with clear exceptions.
- In CLI paths, return explicit status codes and user-friendly messages.

Data and safety:
- Keep provenance metadata with every evidence artifact.
- Trade execution must remain behind deterministic gates and policy checks.
- Use environment variables for API credentials (`OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, etc.).

## Runtime Agent Guidance

For the runtime product:
- `suzybae` is the primary user-facing agent.
- `runtime_supervisor` routes and delegates to specialist runtime agents.
- Use deterministic DAG for any run that can lead to order execution.
- Keep IBKR paper mode as the default execution target.
- Preserve evidence, run IDs, and policy-gate outcomes for auditable decisions.

See `runtime_agents/` and project READMEs for active implementation details.
