from __future__ import annotations


class EngineService:
    def health(self, provider_id: str, base_url: str | None = None) -> dict[str, object]:
        if provider_id == "ollama":
            return {
                "provider_id": provider_id,
                "base_url": base_url or "http://127.0.0.1:11434",
                "healthy": True,
                "message": "Local engine connected",
            }
        return {
            "provider_id": provider_id,
            "base_url": base_url,
            "healthy": True,
            "message": "Engine reachable",
        }

    def models(self, provider_id: str) -> dict[str, object]:
        if provider_id == "ollama":
            return {
                "provider_id": provider_id,
                "models": [
                    {"model_id": "ollama/llama3.2", "label": "Llama 3.2"},
                    {"model_id": "ollama/qwen2.5", "label": "Qwen 2.5"},
                ],
                "message": "Models loaded",
            }
        return {
            "provider_id": provider_id,
            "models": [],
            "message": "Models loaded",
        }
