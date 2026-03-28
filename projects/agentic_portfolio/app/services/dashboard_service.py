from __future__ import annotations


class DashboardService:
    def __init__(self, platform_service, v21_store) -> None:
        self.platform_service = platform_service
        self.v21_store = v21_store

    def snapshot(self) -> dict[str, object]:
        portfolio = self.platform_service.latest_portfolio().model_dump(mode="json")
        findings = self.v21_store.list_findings(status="open")
        reports = self.v21_store.list_reports()
        return {
            "portfolio_summary": {
                "equity": portfolio.get("equity"),
                "cash": portfolio.get("cash"),
                "daily_pnl": portfolio.get("daily_pnl"),
                "drawdown": portfolio.get("drawdown"),
            },
            "pending_findings": len(findings),
            "latest_reports": reports[:5],
            "warnings": [],
        }
