from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.capabilities import router as capabilities_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.engine import router as engine_router
from app.api.routes.findings import router as findings_router
from app.api.routes.gateway import router as gateway_router
from app.api.routes.health import router as health_router
from app.api.routes.instruments import router as instruments_router
from app.api.routes.openclaw_features import router as openclaw_features_router
from app.api.routes.orders import router as orders_router
from app.api.routes.platform import router as platform_router
from app.api.routes.portfolio_workspace import router as portfolio_workspace_router
from app.api.routes.providers import router as providers_router
from app.api.routes.reports import router as reports_router
from app.api.routes.runtime import router as runtime_router
from app.api.routes.runtime_orchestrator import router as runtime_orchestrator_router
from app.api.routes.runtime_status import router as runtime_status_router
from app.api.routes.routing import router as routing_router
from app.api.routes.session import router as session_router
from app.api.routes.settings import router as settings_router
from app.api.routes.watchlists import router as watchlists_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(openclaw_features_router, tags=["openclaw-features"])
api_router.include_router(settings_router, tags=["settings"])
api_router.include_router(routing_router, tags=["routing"])
api_router.include_router(runtime_router, tags=["runtime"])
api_router.include_router(runtime_orchestrator_router, tags=["runtime-orchestrator"])
api_router.include_router(platform_router, tags=["platform"])
api_router.include_router(providers_router, tags=["providers"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(session_router, tags=["session"])
api_router.include_router(engine_router, tags=["engine"])
api_router.include_router(capabilities_router, tags=["capabilities"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(portfolio_workspace_router, tags=["portfolio-workspace"])
api_router.include_router(watchlists_router, tags=["watchlists"])
api_router.include_router(instruments_router, tags=["instruments"])
api_router.include_router(reports_router, tags=["reports"])
api_router.include_router(findings_router, tags=["findings"])
api_router.include_router(gateway_router, tags=["gateway"])
api_router.include_router(orders_router, tags=["orders"])
api_router.include_router(diagnostics_router, tags=["diagnostics"])
api_router.include_router(runtime_status_router, tags=["runtime-status"])
