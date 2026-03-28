# AGENTS.md

This repository is organized around agent-assisted development for a portfolio management product.

Current implemented code:
- `projects/quant_rag/` (Python local-first RAG scaffold)
- `projects/agentic_portfolio/` (FastAPI backend with end-to-end operator and trade-lane scaffold)
- `projects/desktop_app/` (Tauri + React desktop shell)

Planned product:
- Agentic portfolio manager with deterministic trade DAG, IBKR paper execution, and plugin extensions (openclaw).

## Start Here

- Read `.opencode/README.md` first.
- Then read `.opencode/PROJECT.md`, `.opencode/AGENT_CATALOG.md`, and `.opencode/SKILLS_CATALOG.md`.
- Use `.opencode/COMMANDS.md` for canonical run/test commands.

## Repository Rules For Coding Agents

- Keep changes scoped and minimal.
- Prefer explicit, typed interfaces over implicit dictionaries.
- Preserve evidence and auditability in any trade-related flow.
- Never commit secrets or tokens.
- Do not add broker live-trading paths unless explicitly requested.

## Cursor / Copilot Rules

No repo-specific Cursor rules were found:
- `.cursorrules`
- `.cursor/rules/`

No repo-specific Copilot instructions were found:
- `.github/copilot-instructions.md`

If these files are later added, treat them as higher-priority supplements and sync key points into `.opencode/` docs.

## Build, Lint, Test (Current Project: quant_rag)

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
python -m app.cli ingest --input ./my_data --workspace ./workspace
python -m app.cli query --workspace ./workspace "What are the main risks?"
python -m app.cli query --workspace ./workspace --llm openai "Summarize with citations"
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

## Build, Lint, Test (Current Project: agentic_portfolio)

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

## Build, Lint, Test (Current Project: desktop_app)

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

## Planned Multi-Agent System Guidance

For the planned portfolio product:
- Use deterministic DAG for any run that can lead to order execution.
- Allow free-form research outside DAG, but require promotion into DAG before trading.
- Store every run with correlation IDs, evidence, and policy decisions.
- Keep IBKR paper mode as the default execution target.

See `.opencode/OPEN_ITEMS.md` for additional architecture and delivery considerations.
