from __future__ import annotations


class OrderQueryService:
    def __init__(self, platform_service) -> None:
        self.platform_service = platform_service

    def list_orders(self) -> dict[str, object]:
        orders = self.platform_service.store.list_execution_orders()
        return {"orders": orders}
