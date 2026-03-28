import { useEffect, useState } from "react";

import { apiCall } from "../api/client";
import { type CapabilityState, defaultCapabilityState } from "../store/capabilityStore";

export function useCapabilities(sessionId: string): CapabilityState {
  const [state, setState] = useState<CapabilityState>(defaultCapabilityState);

  useEffect(() => {
    if (!sessionId) {
      return;
    }
    void apiCall<Record<string, unknown>>(`/capabilities?session_id=${encodeURIComponent(sessionId)}`, "GET")
      .then((payload) => {
        const chat = payload.chat as Record<string, unknown> | undefined;
        const connection = payload.connection as Record<string, unknown> | undefined;
        setState({
          canSend: Boolean(chat?.can_send),
          sendBlockReason: typeof chat?.send_block_reason === "string" ? chat.send_block_reason : null,
          canBindSession: Boolean(connection?.can_bind_session),
          bindBlockReason: typeof connection?.bind_block_reason === "string" ? connection.bind_block_reason : null,
        });
      })
      .catch(() => setState(defaultCapabilityState));
  }, [sessionId]);

  return state;
}
