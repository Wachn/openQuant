from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import SettingsResponse, SettingsUpdateRequest

router = APIRouter()


@router.get("/settings", response_model=SettingsResponse)
def get_settings(request: Request) -> SettingsResponse:
    config = request.app.state.config
    store = request.app.state.store

    config_payload = {
        "app_name": config.app_name,
        "app_env": config.app_env,
        "app_version": config.app_version,
        "host": config.host,
        "port": str(config.port),
        "data_dir": str(config.data_dir),
        "sqlite_path": str(config.sqlite_path),
    }

    return SettingsResponse(
        config=config_payload,
        persisted=store.get_settings(),
        meta=store.get_meta(),
    )


@router.put("/settings/{key}", response_model=SettingsResponse)
def update_setting(key: str, payload: SettingsUpdateRequest, request: Request) -> SettingsResponse:
    store = request.app.state.store
    store.set_setting(key=key, value=payload.value)
    return get_settings(request)
