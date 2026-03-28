from __future__ import annotations


class ReportServiceV21:
    def __init__(self, v21_store, platform_service) -> None:
        self.v21_store = v21_store
        self.platform_service = platform_service

    def build_startup_report(self, account_id: str | None = None) -> dict[str, object]:
        payload = self.platform_service.startup_report(["AAPL", "MSFT", "NVDA"])
        body_md = "\n".join(
            [
                "# Startup Report",
                f"- as_of_ts: {payload.get('as_of_ts')}",
                f"- suggestion_count: {len(payload.get('suggestions', []))}",
            ]
        )
        return self.v21_store.create_report(
            report_type="startup",
            title="Startup Report",
            body_md=body_md,
            summary={
                "as_of_ts": payload.get("as_of_ts"),
                "suggestions": payload.get("suggestions", []),
                "market_changes": payload.get("market_changes", []),
            },
            account_id=account_id,
            run_id=None,
        )
