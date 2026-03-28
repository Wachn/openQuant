export type ConnectionState =
  | "idle"
  | "selecting_provider"
  | "awaiting_auth"
  | "auth_valid"
  | "loading_models"
  | "model_selected"
  | "binding_session"
  | "connected"
  | "error"
  | "auth_failed"
  | "model_load_failed"
  | "session_bind_failed"
  | "provider_reset_required"
  | "engine_unreachable";

export interface ConnectionSnapshot {
  state: ConnectionState;
  providerId: string;
  authMethod: string;
  modelId: string;
  sessionBound: boolean;
}

export const idleConnectionSnapshot: ConnectionSnapshot = {
  state: "idle",
  providerId: "",
  authMethod: "",
  modelId: "",
  sessionBound: false,
};
