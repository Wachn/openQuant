from __future__ import annotations

import uuid
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NotificationServiceV21:
    def __init__(self, v21_store) -> None:
        self.v21_store = v21_store

    def enqueue(self, channel: str, to: str, payload: dict[str, object]) -> dict[str, object]:
        return {
            "notification_id": str(uuid.uuid4()),
            "channel": channel,
            "to": to,
            "payload": payload,
            "status": "queued",
            "created_at": utc_now_iso(),
        }
