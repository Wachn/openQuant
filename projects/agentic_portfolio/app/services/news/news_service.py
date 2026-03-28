from __future__ import annotations

import uuid


class NewsServiceV21:
    def __init__(self, v21_store) -> None:
        self.v21_store = v21_store

    def ingest(self, symbols: list[str], session_id: str | None = None) -> list[str]:
        finding_ids: list[str] = []
        for symbol in symbols:
            finding = self.v21_store.create_finding(
                severity="info",
                finding_type="news_event",
                title=f"News update for {symbol}",
                summary=f"No critical events detected for {symbol}.",
                session_id=session_id,
                evidence_artifact_id=str(uuid.uuid4()),
            )
            finding_ids.append(str(finding["finding_id"]))
        return finding_ids
