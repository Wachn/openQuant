import type { JSX } from "react";

interface ResetConnectionButtonProps {
  onReset: () => void;
  onForget: () => void;
}

export function ResetConnectionButton(props: ResetConnectionButtonProps): JSX.Element {
  return (
    <div className="action-row">
      <button type="button" onClick={props.onReset}>Reset connection</button>
      <button type="button" onClick={props.onForget}>Forget credentials</button>
    </div>
  );
}
