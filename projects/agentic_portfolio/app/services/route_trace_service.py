from __future__ import annotations

import uuid
from typing import Dict, List

from app.storage.sqlite_store import SQLiteStore


class RouteTraceService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def record(
        self,
        session_id: str,
        route: str,
        connector_id: str | None,
        status: str,
        metadata: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        trace_id = str(uuid.uuid4())
        payload = metadata or {}
        self.store.add_runtime_route_trace(
            trace_id=trace_id,
            session_id=session_id,
            route=route,
            connector_id=connector_id,
            status=status,
            metadata=payload,
        )
        return {
            "trace_id": trace_id,
            "session_id": session_id,
            "route": route,
            "connector_id": connector_id,
            "status": status,
            "metadata": payload,
        }

    def list_for_session(self, session_id: str, limit: int = 20) -> List[Dict[str, object]]:
        return self.store.list_runtime_route_traces(session_id=session_id, limit=limit)
