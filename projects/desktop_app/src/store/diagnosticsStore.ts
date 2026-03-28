export interface DiagnosticsState {
  status: string;
  error: string | null;
}

export const defaultDiagnosticsState: DiagnosticsState = {
  status: "unknown",
  error: null,
};
