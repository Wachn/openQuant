from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Protocol

from app.domain.core_models import BrokerType, TradeTicket


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BrokerAdapter(Protocol):
    broker: BrokerType

    def submit_order(self, order_id: str, ticket: TradeTicket) -> Dict[str, object]:
        ...

    def get_status(self, payload: Dict[str, object]) -> Dict[str, object]:
        ...

    def cancel_order(self, payload: Dict[str, object]) -> Dict[str, object]:
        ...

    def list_fills(self, payload: Dict[str, object]) -> List[Dict[str, object]]:
        ...

    def reconcile(self, payload: Dict[str, object]) -> Dict[str, object]:
        ...


@dataclass
class PaperBrokerAdapter:
    broker: BrokerType

    def submit_order(self, order_id: str, ticket: TradeTicket) -> Dict[str, object]:
        return {
            "broker": self.broker.value,
            "order_id": order_id,
            "ticket_id": ticket.ticket_id,
            "run_id": ticket.run_id,
            "symbol": ticket.symbol,
            "status": "submitted",
            "submitted_at": utc_now_iso(),
        }

    def get_status(self, payload: Dict[str, object]) -> Dict[str, object]:
        return {
            "broker": self.broker.value,
            "order_id": payload["order_id"],
            "status": payload.get("status", "submitted"),
            "updated_at": utc_now_iso(),
        }

    def cancel_order(self, payload: Dict[str, object]) -> Dict[str, object]:
        status = str(payload.get("status", "submitted"))
        if status == "filled":
            return {
                "broker": self.broker.value,
                "order_id": payload["order_id"],
                "status": "filled",
                "updated_at": utc_now_iso(),
            }
        return {
            "broker": self.broker.value,
            "order_id": payload["order_id"],
            "status": "cancelled",
            "updated_at": utc_now_iso(),
        }

    def list_fills(self, payload: Dict[str, object]) -> List[Dict[str, object]]:
        if str(payload.get("status")) != "filled":
            return []
        fill_quantity = float(payload.get("quantity", 0.0))
        fill_price = float(payload.get("limit_price", payload.get("entry_price", 0.0)))
        return [
            {
                "fill_id": f"fill:{payload['order_id']}",
                "order_id": payload["order_id"],
                "broker": self.broker.value,
                "quantity": fill_quantity,
                "price": fill_price,
                "filled_at": utc_now_iso(),
            }
        ]

    def reconcile(self, payload: Dict[str, object]) -> Dict[str, object]:
        fills = self.list_fills(payload)
        return {
            "broker": self.broker.value,
            "order_id": payload["order_id"],
            "status": payload.get("status", "submitted"),
            "fill_count": len(fills),
            "reconciled_at": utc_now_iso(),
        }


def build_default_adapters() -> Dict[BrokerType, BrokerAdapter]:
    return {
        BrokerType.IBKR_PAPER: PaperBrokerAdapter(BrokerType.IBKR_PAPER),
        BrokerType.MT5_PAPER: PaperBrokerAdapter(BrokerType.MT5_PAPER),
    }
