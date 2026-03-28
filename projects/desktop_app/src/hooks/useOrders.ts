import { useEffect, useState } from "react";

import { apiCall } from "../api/client";
import { defaultOrderStoreState, type OrderStoreState } from "../store/orderStore";

export function useOrders(): OrderStoreState {
  const [state, setState] = useState<OrderStoreState>(defaultOrderStoreState);

  useEffect(() => {
    void apiCall<{ orders: { order_id: string; status: string; broker: string }[] }>("/orders", "GET")
      .then((payload) => setState({ orders: payload.orders }))
      .catch(() => setState(defaultOrderStoreState));
  }, []);

  return state;
}
