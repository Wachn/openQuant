from __future__ import annotations

from app.services.brokers.base import BrokerAdapterBase


class Mt5Adapter(BrokerAdapterBase):
    broker_id = "mt5"

    async def submit_order(self, ticket: dict[str, object], idempotency_key: str) -> dict[str, object]:
        return {
            "broker_id": self.broker_id,
            "status": "submitted",
            "method": "order_send",
            "idempotency_key": idempotency_key,
            "ticket": ticket,
        }

    async def positions(self) -> dict[str, object]:
        return {
            "broker_id": self.broker_id,
            "method": "positions_get",
            "positions": [],
            "last_error": None,
        }
