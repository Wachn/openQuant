from __future__ import annotations

from fastapi import APIRouter, Request

from app.domain.routing.models import RouteRequest
from app.schemas import RouteDecisionResponse, RouteRequestModel

router = APIRouter()


@router.post("/route", response_model=RouteDecisionResponse)
def route_message(payload: RouteRequestModel, request: Request) -> RouteDecisionResponse:
    router_service = request.app.state.dynamic_router
    decision = router_service.route(
        RouteRequest(
            message=payload.message,
            source=payload.source,
            automation_enabled=payload.automation_enabled,
            include_internal_plan=payload.include_internal_plan,
        )
    )
    return RouteDecisionResponse(
        lane=decision.lane,
        workflow=decision.workflow,
        reason=decision.reason,
        requires_dag=decision.requires_dag,
        requires_market_refresh=decision.requires_market_refresh,
        requires_user_confirmation=decision.requires_user_confirmation,
        internal_builder_plan=decision.internal_builder_plan,
    )
