# Agentic Portfolio Desktop (Phase 10 Shell)

This desktop project provides a Tauri + React shell wired to the backend APIs.

## Run frontend only

```bash
cd projects/desktop_app
npm install
npm run dev
```

## Run Tauri desktop app

```bash
cd projects/desktop_app
npm install
npm run tauri dev
```

The app expects backend API at `http://127.0.0.1:8000`.

## Primary flow in UI

1. Run Startup Report
2. Run Trade Lane
3. Submit Paper Order

This aligns with backend APIs in `projects/agentic_portfolio`.
