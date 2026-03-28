from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas import ModelProfileUpsertRequest, ProviderProfileUpsertRequest

router = APIRouter()


@router.get("/providers")
def providers(request: Request) -> dict[str, object]:
    registry = request.app.state.provider_registry
    return {"providers": registry.list_providers()}


@router.get("/providers/{provider_id}/models")
def provider_models(provider_id: str, request: Request) -> dict[str, object]:
    model_service = request.app.state.model_service
    models = model_service.models_for_provider(provider_id)
    if not models:
        raise HTTPException(status_code=404, detail="models not found for provider")
    return {"provider_id": provider_id, "models": models}


@router.get("/runtime/providers/models")
def runtime_provider_models(provider_id: str, request: Request) -> dict[str, object]:
    return provider_models(provider_id=provider_id, request=request)


@router.get("/runtime/providers/profiles")
def runtime_provider_profiles(request: Request) -> dict[str, object]:
    store = request.app.state.v21_store
    return {"provider_profiles": store.list_provider_profiles()}


@router.post("/runtime/providers/profiles")
def runtime_provider_profiles_upsert(payload: ProviderProfileUpsertRequest, request: Request) -> dict[str, object]:
    store = request.app.state.v21_store
    profile = store.upsert_provider_profile(
        provider_profile_id=payload.provider_profile_id,
        provider_id=payload.provider_id,
        display_name=payload.display_name,
        auth_type=payload.auth_type,
        base_url=payload.base_url,
        options=payload.options,
        status=payload.status,
        last_health_at=payload.last_health_at,
    )
    return {"provider_profile": profile}


@router.get("/runtime/models/profiles")
def runtime_model_profiles(request: Request) -> dict[str, object]:
    store = request.app.state.v21_store
    return {"model_profiles": store.list_model_profiles()}


@router.post("/runtime/models/profiles")
def runtime_model_profiles_upsert(payload: ModelProfileUpsertRequest, request: Request) -> dict[str, object]:
    store = request.app.state.v21_store
    profile = store.upsert_model_profile(
        model_profile_id=payload.model_profile_id,
        provider_profile_id=payload.provider_profile_id,
        model_id=payload.model_id,
        display_name=payload.display_name,
        capabilities=payload.capabilities,
        default_temperature=payload.default_temperature,
        max_output_tokens=payload.max_output_tokens,
        enabled=payload.enabled,
    )
    return {"model_profile": profile}
