export interface AuthSecretState {
  apiKey: string;
  token: string;
  baseUrl: string;
}

export const emptyAuthSecretState: AuthSecretState = {
  apiKey: "",
  token: "",
  baseUrl: "",
};

export function redactSecret(_value: string): string {
  return "***";
}
