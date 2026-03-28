from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.schemas import (
    AgentConnectionBindingRequest,
    ProviderConnectionRequest,
    RuntimeProviderApiValidateRequest,
    RuntimeProviderOauthAuthorizeRequest,
    RuntimeChangeActionRequest,
    RuntimeSuzyActivateRequest,
    RuntimeSuzySelfEditRequest,
    RuntimeSessionCreateRequest,
    RuntimeSessionRenameRequest,
    RuntimeSessionMessageRequest,
)

router = APIRouter()


@router.get("/runtime/agents")
def runtime_agents(request: Request) -> dict[str, object]:
    registry = request.app.state.runtime_agent_registry
    specs = registry.list_specs()
    return {
        "agents": [
            {
                "agent_id": spec.agent_id,
                "name": spec.name,
                "kind": spec.kind,
                "tags": spec.tags,
                "purpose": spec.purpose,
                "lane_access": spec.lane_access,
                "valid": spec.valid,
                "errors": spec.errors,
            }
            for spec in specs
        ]
    }


@router.get("/runtime/agents/validation")
def runtime_agents_validation(request: Request) -> dict[str, object]:
    registry = request.app.state.runtime_agent_registry
    return registry.validation_summary()


@router.get("/runtime/providers/status")
def runtime_providers_status(request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    return gateway.status()


@router.get("/runtime/providers/catalog")
def runtime_providers_catalog(request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    return gateway.catalog()


@router.get("/runtime/providers/auth")
def runtime_providers_auth(request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    return gateway.auth_methods()


@router.post("/runtime/providers/{provider_id}/oauth/authorize")
def runtime_provider_oauth_authorize(
    provider_id: str,
    payload: RuntimeProviderOauthAuthorizeRequest,
    request: Request,
) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    config = request.app.state.config
    callback_uri = f"http://localhost:{config.oauth_loopback_port}/auth/callback"
    try:
        return gateway.oauth_authorize(
            provider_id=provider_id,
            method_id=payload.method_id,
            connection_id=payload.connection_id,
            redirect_uri=callback_uri,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runtime/providers/{provider_id}/oauth/callback")
def runtime_provider_oauth_callback(
    provider_id: str,
    request: Request,
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> HTMLResponse:
    gateway = request.app.state.provider_gateway
    status_code, html = gateway.oauth_callback(
        provider_id=provider_id,
        state=state,
        code=code,
        error=error,
        error_description=error_description,
    )
    return HTMLResponse(content=html, status_code=status_code)


@router.post("/runtime/providers/api/validate")
def runtime_provider_api_validate(payload: RuntimeProviderApiValidateRequest, request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    return gateway.validate_api_key(provider_id=payload.provider_id, api_key=payload.api_key)


@router.get("/runtime/providers/connections")
def runtime_provider_connections(request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    return {"connections": gateway.list_connections()}


@router.post("/runtime/providers/connections")
def runtime_upsert_provider_connection(payload: ProviderConnectionRequest, request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    connection = gateway.upsert_connection(
        connection_id=payload.connection_id,
        provider=payload.provider,
        model=payload.model,
        enabled=payload.enabled,
        route_class=payload.route_class,
        base_url=payload.base_url,
        api_key_env=payload.api_key_env,
        api_key=payload.api_key,
        auth_method=payload.auth_method,
        display_name=payload.display_name,
    )
    return {"connection": connection}


@router.post("/runtime/chat/sessions")
def runtime_create_session(payload: RuntimeSessionCreateRequest, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    return workspace.create_session(title=payload.title)


@router.get("/runtime/chat/sessions")
def runtime_list_sessions(request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    return workspace.list_sessions()


@router.get("/runtime/chat/sessions/{session_id}")
def runtime_get_session(session_id: str, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    try:
        return workspace.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/runtime/chat/sessions/{session_id}")
def runtime_rename_session(session_id: str, payload: RuntimeSessionRenameRequest, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    try:
        return workspace.rename_session(session_id=session_id, title=payload.title)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/runtime/chat/sessions/{session_id}")
def runtime_delete_session(session_id: str, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    try:
        return workspace.delete_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runtime/chat/sessions/{session_id}/message")
def runtime_send_message(session_id: str, payload: RuntimeSessionMessageRequest, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    dynamic_router = request.app.state.dynamic_router
    try:
        return workspace.process_message(
            session_id=session_id,
            message=payload.message,
            route_source=payload.source,
            automation_enabled=payload.automation_enabled,
            include_internal_plan=payload.include_internal_plan,
            agent_id=payload.agent_id,
            connection_id=payload.connection_id,
            variant=payload.variant,
            dynamic_router=dynamic_router,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runtime/change-requests")
def runtime_change_requests(request: Request, status: str | None = None) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    return {"change_requests": workspace.list_change_requests(status=status)}


@router.post("/runtime/change-requests/{change_id}/action")
def runtime_change_request_action(change_id: str, payload: RuntimeChangeActionRequest, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    try:
        updated = workspace.apply_change_request_action(
            change_id=change_id,
            action=payload.action,
            snooze_minutes=payload.snooze_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"change_request": updated}


@router.get("/runtime/agents/{agent_id}/connection")
def runtime_get_agent_connection(agent_id: str, request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    binding = gateway.get_agent_binding(agent_id)
    return {"binding": binding}


@router.post("/runtime/agents/{agent_id}/connection")
def runtime_bind_agent_connection(agent_id: str, payload: AgentConnectionBindingRequest, request: Request) -> dict[str, object]:
    gateway = request.app.state.provider_gateway
    try:
        binding = gateway.bind_agent_connection(agent_id=agent_id, connection_id=payload.connection_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"binding": binding}


@router.get("/runtime/suzy/status")
def runtime_suzy_status(request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    return workspace.suzy_status()


@router.post("/runtime/suzy/activate")
def runtime_suzy_activate(payload: RuntimeSuzyActivateRequest, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    try:
        return workspace.activate_suzy(command=payload.command)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runtime/suzy/self-edit")
def runtime_suzy_self_edit(payload: RuntimeSuzySelfEditRequest, request: Request) -> dict[str, object]:
    workspace = request.app.state.runtime_workspace
    try:
        return workspace.suzy_self_edit(
            file_path=payload.file_path,
            find_text=payload.find_text,
            replace_text=payload.replace_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
