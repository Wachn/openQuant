from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas import RuntimeOrchestrateRequest

router = APIRouter()


@router.get("/runtime/orchestrator/status")
def runtime_orchestrator_status(request: Request) -> dict[str, object]:
    service = request.app.state.runtime_orchestrator
    return service.status()


@router.post("/runtime/orchestrator/sessions/{session_id}/orchestrate")
def runtime_orchestrator_orchestrate(
    session_id: str,
    payload: RuntimeOrchestrateRequest,
    request: Request,
) -> dict[str, object]:
    service = request.app.state.runtime_orchestrator
    try:
        return service.orchestrate(
            session_id=session_id,
            message=payload.message,
            route_hint=payload.route_hint,
            preferred_connection_id=payload.preferred_connection_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runtime/orchestrator/sessions/{session_id}/traces")
def runtime_orchestrator_traces(session_id: str, request: Request, limit: int = 20) -> dict[str, object]:
    service = request.app.state.runtime_orchestrator
    traces = service.route_trace_service.list_for_session(session_id=session_id, limit=limit)
    return {
        "session_id": session_id,
        "traces": traces,
    }


@router.get("/runtime/orchestrator/sessions/{session_id}/memory")
def runtime_orchestrator_memory(session_id: str, request: Request) -> dict[str, object]:
    service = request.app.state.runtime_orchestrator
    latest = service.memory_summary_service.latest_for_session(session_id=session_id)
    return {
        "session_id": session_id,
        "memory": latest,
    }
