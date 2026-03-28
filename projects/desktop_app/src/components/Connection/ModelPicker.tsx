import type { JSX } from "react";

export interface ProviderModel {
  model_id: string;
  label: string;
}

interface ModelPickerProps {
  models: ProviderModel[];
  selectedModelId: string;
  onSelect: (modelId: string) => void;
  onLoadModels: () => void;
}

export function ModelPicker(props: ModelPickerProps): JSX.Element {
  return (
    <div>
      <div className="action-row">
        <button type="button" onClick={props.onLoadModels}>Load models</button>
      </div>
      <div className="list-box">
        {props.models.map((model) => (
          <button
            key={model.model_id}
            type="button"
            onClick={() => props.onSelect(model.model_id)}
            className={props.selectedModelId === model.model_id ? "tab active" : "tab"}
          >
            {model.label}
          </button>
        ))}
      </div>
    </div>
  );
}
