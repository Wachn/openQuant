import { useState } from "react";

import { apiCall } from "../api/client";
import { type ConnectionSnapshot, type ConnectionState, idleConnectionSnapshot } from "../store/connectionStore";

export function useConnectionFlow(sessionId: string) {
  const [connection, setConnection] = useState<ConnectionSnapshot>(idleConnectionSnapshot);
  const [isSending, setIsSending] = useState(false);

  const setState = (state: ConnectionState): void => {
    setConnection((prev) => ({ ...prev, state }));
  };

  const disconnectCurrentConnection = async (): Promise<void> => {
    await apiCall("/session/unbind", "POST", { session_id: sessionId });
    setConnection(idleConnectionSnapshot);
  };

  const resetConnectionUI = (): void => {
    setConnection(idleConnectionSnapshot);
  };

  const forgetStoredCredentials = async (providerId: string): Promise<void> => {
    await apiCall("/auth/logout", "POST", { provider_id: providerId, session_id: sessionId });
  };

  const teardownBackendBinding = async (): Promise<void> => {
    await apiCall("/session/unbind", "POST", { session_id: sessionId });
  };

  const cancelActiveStreamsAndJobs = (): void => {
    setIsSending(false);
  };

  const clearSecrets = (): void => {
    setConnection((prev) => ({
      ...prev,
      authMethod: prev.authMethod,
    }));
  };

  return {
    connection,
    isSending,
    setState,
    disconnectCurrentConnection,
    resetConnectionUI,
    forgetStoredCredentials,
    teardownBackendBinding,
    cancelActiveStreamsAndJobs,
    clearSecrets,
  };
}
