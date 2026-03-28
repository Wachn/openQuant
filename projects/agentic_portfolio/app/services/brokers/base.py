from __future__ import annotations


class BrokerAdapterBase:
    broker_id: str = "unknown"

    async def sync(self, account_id: str) -> dict[str, object]:
        return {"account_id": account_id, "broker_id": self.broker_id, "status": "synced"}

    async def submit_order(self, ticket: dict[str, object], idempotency_key: str) -> dict[str, object]:
        return {
            "broker_id": self.broker_id,
            "idempotency_key": idempotency_key,
            "status": "submitted",
            "ticket": ticket,
        }

    async def cancel_order(self, broker_order_id: str) -> dict[str, object]:
        return {"broker_id": self.broker_id, "broker_order_id": broker_order_id, "status": "canceled"}
