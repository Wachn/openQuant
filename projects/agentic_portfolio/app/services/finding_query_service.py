from __future__ import annotations


class FindingQueryService:
    def __init__(self, v21_store) -> None:
        self.v21_store = v21_store

    def list_findings(self, session_id: str | None = None) -> dict[str, object]:
        return {"findings": self.v21_store.list_findings(session_id=session_id)}
