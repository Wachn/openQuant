from __future__ import annotations

from app.services.brokers.base import BrokerAdapterBase


class IbkrTwsAdapter(BrokerAdapterBase):
    broker_id = "ibkr_tws"

    async def connect(self) -> dict[str, object]:
        return {
            "broker_id": self.broker_id,
            "paper_port_default": 7497,
            "gateway_paper_port_default": 4002,
            "read_only_must_be_disabled": True,
            "status": "connected",
        }
