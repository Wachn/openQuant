import { useMemo } from "react";

import { defaultBrokerStatusState } from "../store/brokerStore";

export function useBrokerStatus() {
  return useMemo(() => defaultBrokerStatusState, []);
}
