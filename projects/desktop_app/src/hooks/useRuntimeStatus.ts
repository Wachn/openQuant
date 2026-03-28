import { useEffect, useState } from "react";

import { apiCall } from "../api/client";

export interface RuntimeStatusSnapshot {
  provider: string;
  model: string;
  bindState: string;
}

const idle: RuntimeStatusSnapshot = {
  provider: "",
  model: "",
  bindState: "idle",
};

export function useRuntimeStatus(sessionId: string): RuntimeStatusSnapshot {
  const [state, setState] = useState<RuntimeStatusSnapshot>(idle);

  useEffect(() => {
    if (!sessionId) {
      return;
    }
    void apiCall<Record<string, unknown>>(`/runtime_status?session_id=${encodeURIComponent(sessionId)}`, "GET")
      .then((payload) => {
        const connection = payload.connection as Record<string, unknown> | undefined;
        setState({
          provider: typeof connection?.provider === "string" ? connection.provider : "",
          model: typeof connection?.model === "string" ? connection.model : "",
          bindState: typeof connection?.bind_state === "string" ? connection.bind_state : "idle",
        });
      })
      .catch(() => setState(idle));
  }, [sessionId]);

  return state;
}
