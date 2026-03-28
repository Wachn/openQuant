from __future__ import annotations


class ModelService:
    def __init__(self, provider_gateway) -> None:
        self.provider_gateway = provider_gateway
        self._cache: dict[str, list[dict[str, str]]] = {}

    def invalidate_cache(self, provider_id: str | None = None) -> None:
        if provider_id is None:
            self._cache.clear()
            return
        self._cache.pop(provider_id, None)

    def models_for_provider(self, provider_id: str) -> list[dict[str, str]]:
        if provider_id == "ollama":
            return [
                {"model_id": "ollama/llama3.2", "label": "Llama 3.2", "provider_qualified": "ollama/llama3.2"},
                {"model_id": "ollama/qwen2.5", "label": "Qwen 2.5", "provider_qualified": "ollama/qwen2.5"},
            ]
        if provider_id == "huggingface":
            return [
                {
                    "model_id": "huggingface/HuggingFaceH4/zephyr-7b-beta",
                    "label": "Zephyr 7B Beta",
                    "provider_qualified": "huggingface/HuggingFaceH4/zephyr-7b-beta",
                }
            ]
        if provider_id == "openai_compatible":
            return [
                {
                    "model_id": "openai_compatible/gpt-4o-mini",
                    "label": "OpenAI-compatible GPT-4o Mini",
                    "provider_qualified": "openai_compatible/gpt-4o-mini",
                }
            ]
        if provider_id in self._cache:
            return self._cache[provider_id]
        catalog = self.provider_gateway.catalog()
        providers = catalog.get("all", []) if isinstance(catalog, dict) else []
        matched = next((item for item in providers if item.get("id") == provider_id), None)
        if isinstance(matched, dict):
            models = matched.get("models", [])
            normalized = [
                {
                    "model_id": str(model.get("id")),
                    "label": str(model.get("name") or model.get("id")),
                    "provider_qualified": str(model.get("id")),
                }
                for model in models
                if isinstance(model, dict)
            ]
        else:
            normalized = []
        self._cache[provider_id] = normalized
        return normalized
