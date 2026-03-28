from __future__ import annotations

import uuid
from typing import Dict, Optional

from app.storage.sqlite_store import SQLiteStore


class MemorySummaryService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def summarize_session(self, session_id: str) -> Dict[str, object]:
        messages = self.store.list_chat_messages(session_id=session_id)
        message_count = len(messages)
        char_count = sum(len(str(item.get("content", ""))) for item in messages)
        token_estimate = max(0, char_count // 4)
        latest_roles = [str(item.get("role", "")) for item in messages[-5:]]
        latest_routes = [str(item.get("route", "")) for item in messages[-5:] if item.get("route")]
        summary_payload = {
            "latest_roles": latest_roles,
            "latest_routes": latest_routes,
            "char_count": char_count,
        }
        summary_id = str(uuid.uuid4())
        self.store.add_runtime_memory_summary(
            summary_id=summary_id,
            session_id=session_id,
            message_count=message_count,
            token_estimate=token_estimate,
            summary=summary_payload,
        )
        return {
            "summary_id": summary_id,
            "session_id": session_id,
            "message_count": message_count,
            "token_estimate": token_estimate,
            "summary": summary_payload,
        }

    def latest_for_session(self, session_id: str) -> Optional[Dict[str, object]]:
        return self.store.latest_runtime_memory_summary(session_id=session_id)
