export interface CapabilityState {
  canSend: boolean;
  sendBlockReason: string | null;
  canBindSession: boolean;
  bindBlockReason: string | null;
}

export const defaultCapabilityState: CapabilityState = {
  canSend: false,
  sendBlockReason: "session_not_bound",
  canBindSession: false,
  bindBlockReason: "auth_not_valid",
};
