from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/reports")
def reports(request: Request) -> dict[str, object]:
    service = request.app.state.report_query_service
    return service.list_reports()


@router.get("/reports/{report_id}")
def report_by_id(report_id: str, request: Request) -> dict[str, object]:
    store = request.app.state.v21_store
    report = next((item for item in store.list_reports() if item["report_id"] == report_id), None)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return {"report": report}


@router.get("/reports/startup/latest")
def report_startup_latest(request: Request, account_id: str | None = None) -> dict[str, object]:
    store = request.app.state.v21_store
    startup = [item for item in store.list_reports(report_type="startup", account_id=account_id) if item["report_type"] == "startup"]
    if not startup:
        request.app.state.report_service_v21.build_startup_report(account_id=account_id or "paper-default")
        startup = [item for item in store.list_reports(report_type="startup", account_id=account_id) if item["report_type"] == "startup"]
    return {"report": startup[0] if startup else None}
