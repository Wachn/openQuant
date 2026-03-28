import type { JSX } from "react";

interface AuthModalProps {
  open: boolean;
  providerLabel: string;
  authMethod: string;
  error: string | null;
  onClose: () => void;
  children: JSX.Element;
}

export function AuthModal(props: AuthModalProps): JSX.Element | null {
  if (!props.open) {
    return null;
  }
  return (
    <div className="runtime-modal">
      <article className="panel runtime-modal-card">
        <h3>Authentication</h3>
        <p className="muted">Provider: {props.providerLabel || "-"}</p>
        <p className="muted">Method: {props.authMethod || "-"}</p>
        {props.error ? <p><strong>Error:</strong> {props.error}</p> : null}
        {props.children}
        <div className="action-row">
          <button type="button" onClick={props.onClose}>Close</button>
        </div>
      </article>
    </div>
  );
}
