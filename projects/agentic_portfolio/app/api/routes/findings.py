from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/findings")
def findings(request: Request, session_id: str | None = None) -> dict[str, object]:
    service = request.app.state.finding_query_service
    return service.list_findings(session_id=session_id)


@router.post("/findings/{finding_id}/resolve")
def resolve_finding(finding_id: str, request: Request) -> dict[str, object]:
    store = request.app.state.v21_store
    ok = store.resolve_finding(finding_id)
    if not ok:
        raise HTTPException(status_code=404, detail="finding not found")
    return {"ok": True}
