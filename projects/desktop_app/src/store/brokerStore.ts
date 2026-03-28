export interface BrokerStatusState {
  brokerId: string;
  freshnessTs: string;
  stale: boolean;
}

export const defaultBrokerStatusState: BrokerStatusState = {
  brokerId: "",
  freshnessTs: "",
  stale: true,
};
