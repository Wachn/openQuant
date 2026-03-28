from __future__ import annotations


class ReportQueryService:
    def __init__(self, v21_store, report_service_v21) -> None:
        self.v21_store = v21_store
        self.report_service_v21 = report_service_v21

    def list_reports(self) -> dict[str, object]:
        reports = self.v21_store.list_reports()
        if not reports:
            self.report_service_v21.build_startup_report(account_id="paper-default")
            reports = self.v21_store.list_reports()
        return {"reports": reports}
