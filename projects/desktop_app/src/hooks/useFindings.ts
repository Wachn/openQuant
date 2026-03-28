import { useEffect, useState } from "react";

import { apiCall } from "../api/client";
import { defaultFindingStoreState, type FindingStoreState } from "../store/findingStore";

export function useFindings(): FindingStoreState {
  const [state, setState] = useState<FindingStoreState>(defaultFindingStoreState);

  useEffect(() => {
    void apiCall<{ findings: { finding_id: string; severity: string; status: string; title: string }[] }>("/findings", "GET")
      .then((payload) => setState({ findings: payload.findings }))
      .catch(() => setState(defaultFindingStoreState));
  }, []);

  return state;
}
