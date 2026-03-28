# Agentic Portfolio Desktop App

`projects/desktop_app` is the Tauri + React operator cockpit for Portfolio Agent. It connects to the local backend API and exposes runtime chat, provider connection flow, market/news monitors, OpenClaw-inspired panels, portfolio workflows, and execution actions.

Integrated reference-style GUI areas in the Research workspace:

- World Monitor panel (symbols/focus/limit + live sources)
- Open Data panel (dataset search, overview, and historical series preview)
- Open Stock panel (search, catalog browser, snapshot, reference inspect card, and candlestick view)
- OpenClaw-style runtime settings panel (router settings, heartbeat, cron jobs, cron runs)

## Prerequisite

Run backend first at `http://127.0.0.1:8000` from `projects/agentic_portfolio`.

## Frontend Dev Mode

```bash
cd projects/desktop_app
npm install
npm run dev
```

## Tauri Desktop Mode

```bash
cd projects/desktop_app
npm install
npm run tauri dev
```

## Build

```bash
cd projects/desktop_app
npm run build
```

## Quick Verification

- Provider connection flow opens and loads models.
- Research tab loads market/news/gateway panels.
- OpenClaw-related panels (flat router, world monitor, open data, open stock) return data when backend is running.
