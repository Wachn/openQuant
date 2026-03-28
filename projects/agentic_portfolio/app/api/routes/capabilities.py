from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/capabilities")
def capabilities(session_id: str, request: Request) -> dict[str, object]:
    capability_service = request.app.state.capability_service
    binding = request.app.state.session_binding_service.status(session_id)
    auth_status = request.app.state.auth_service.status(session_id)
    provider_connections = request.app.state.provider_gateway.list_connections()
    return capability_service.get_capabilities(
        session_id=session_id,
        binding=binding,
        auth_status=auth_status,
        provider_connections=provider_connections,
    )


@router.get("/runtime/capabilities")
def runtime_capabilities(session_id: str, request: Request) -> dict[str, object]:
    return capabilities(session_id=session_id, request=request)
