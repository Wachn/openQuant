export interface SessionBinding {
  sessionId: string;
  providerId: string;
  authMethod: string;
  modelId: string;
  connected: boolean;
}

export const idleSessionBinding: SessionBinding = {
  sessionId: "",
  providerId: "",
  authMethod: "",
  modelId: "",
  connected: false,
};
