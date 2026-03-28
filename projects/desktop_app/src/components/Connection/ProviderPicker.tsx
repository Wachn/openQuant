import type { JSX } from "react";

export interface ProviderOption {
  provider_id: string;
  label: string;
  group: string;
}

interface ProviderPickerProps {
  providers: ProviderOption[];
  selectedProviderId: string;
  onSelect: (providerId: string) => void;
}

export function ProviderPicker(props: ProviderPickerProps): JSX.Element {
  return (
    <div className="list-box">
      {props.providers.map((provider) => (
        <button
          key={provider.provider_id}
          type="button"
          onClick={() => props.onSelect(provider.provider_id)}
          className={props.selectedProviderId === provider.provider_id ? "tab active" : "tab"}
        >
          {provider.group}: {provider.label}
        </button>
      ))}
    </div>
  );
}
