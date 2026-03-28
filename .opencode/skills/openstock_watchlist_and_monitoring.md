# Skill: OpenStock Watchlist and Monitoring

Use when building stock discovery, watchlist monitoring, alerts-style flows, stock detail cards, or chart-driven market views.

## Required capabilities

- searchable stock catalog
- watchlist-centric monitoring surfaces
- candlestick and quote-driven stock detail
- market news tied to watchlist symbols
- portfolio-aware stock inspection

## Product adaptation

In this repo, OpenStock features must support the agentic quantitative portfolio workflow.

That means:

- watchlists should connect to portfolio holdings and demo portfolios
- stock detail should drive research context for SuzyBae and downstream agents
- charts should use backend-backed OHLC series, not frontend-only placeholders
- monitoring surfaces should show signal changes clearly and support inspect actions

## Implementation anchors

- backend stock bridge: `projects/agentic_portfolio/app/services/open_stock_service.py`
- backend open data bridge: `projects/agentic_portfolio/app/services/open_data_service.py`
- desktop workspace integration: `projects/desktop_app/src/App.tsx`

## OpenStock-inspired surfaces to preserve

- command-style stock discovery
- watchlist table and monitor board
- stock reference/detail card
- candlestick chart panel
- market-news grid tied to tracked symbols
