from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/runtime_status")
def runtime_status(session_id: str, request: Request) -> dict[str, object]:
    status_service = request.app.state.runtime_status_service
    binding = request.app.state.session_binding_service.status(session_id)
    auth_status = request.app.state.auth_service.status(session_id)
    return status_service.status(session_binding=binding, auth_status=auth_status)


@router.get("/runtime/status")
def runtime_status_alias(session_id: str, request: Request) -> dict[str, object]:
    return runtime_status(session_id=session_id, request=request)
