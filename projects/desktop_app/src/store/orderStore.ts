export interface OrderItem {
  order_id: string;
  status: string;
  broker: string;
}

export interface OrderStoreState {
  orders: OrderItem[];
}

export const defaultOrderStoreState: OrderStoreState = {
  orders: [],
};
