from __future__ import annotations

from app.services.brokers.base import BrokerAdapterBase


class IbkrCpapiAdapter(BrokerAdapterBase):
    broker_id = "ibkr_cpapi"

    def __init__(self) -> None:
        self._pending_reply_by_account: dict[str, str] = {}

    async def submit_order(self, ticket: dict[str, object], idempotency_key: str) -> dict[str, object]:
        account_id = str(ticket.get("account_id", "paper-default"))
        pending = self._pending_reply_by_account.get(account_id)
        if pending:
            return {
                "broker_id": self.broker_id,
                "status": "pending_reply",
                "reply_id": pending,
                "message": "Resolve pending /iserver/reply before new submit",
            }
        reply_id = f"reply-{idempotency_key[:8]}"
        self._pending_reply_by_account[account_id] = reply_id
        return {
            "broker_id": self.broker_id,
            "status": "pending_reply",
            "reply_id": reply_id,
            "message": "Order requires /iserver/reply confirmation",
        }

    async def confirm_reply(self, account_id: str, reply_id: str, confirmed: bool) -> dict[str, object]:
        active = self._pending_reply_by_account.get(account_id)
        if active != reply_id:
            return {"broker_id": self.broker_id, "status": "error", "message": "reply_id not found"}
        self._pending_reply_by_account.pop(account_id, None)
        return {
            "broker_id": self.broker_id,
            "status": "Submitted" if confirmed else "Canceled",
            "reply_id": reply_id,
        }
