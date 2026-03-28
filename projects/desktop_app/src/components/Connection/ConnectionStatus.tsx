import type { JSX } from "react";

interface ConnectionStatusProps {
  provider: string;
  authentication: string;
  model: string;
  session: string;
  state: string;
}

export function ConnectionStatus(props: ConnectionStatusProps): JSX.Element {
  return (
    <div className="compact-output">
      <p><strong>Provider:</strong> {props.provider || "-"}</p>
      <p><strong>Authentication:</strong> {props.authentication || "-"}</p>
      <p><strong>Model:</strong> {props.model || "-"}</p>
      <p><strong>Session:</strong> {props.session || "-"}</p>
      <p><strong>State:</strong> {props.state}</p>
    </div>
  );
}
