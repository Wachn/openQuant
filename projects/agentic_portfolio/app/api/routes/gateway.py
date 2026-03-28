from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.schemas import GatewayTestMessageRequest

router = APIRouter()


@router.get("/gateway/channels")
def gateway_channels(request: Request) -> dict[str, object]:
    svc = request.app.state.channel_gateway_service
    return svc.channels_status()


@router.post("/gateway/telegram/test")
def gateway_telegram_test(payload: GatewayTestMessageRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.channel_gateway_service
    try:
        return svc.send_telegram_test(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}:{exc}") from exc


@router.post("/gateway/whatsapp/test")
def gateway_whatsapp_test(payload: GatewayTestMessageRequest, request: Request) -> dict[str, object]:
    svc = request.app.state.channel_gateway_service
    try:
        return svc.send_whatsapp_test(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}:{exc}") from exc


@router.get("/gateway/whatsapp/webhook")
def gateway_whatsapp_verify(
    request: Request,
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
) -> PlainTextResponse:
    svc = request.app.state.channel_gateway_service
    try:
        challenge = svc.verify_whatsapp_webhook(hub_mode, hub_challenge, hub_verify_token)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return PlainTextResponse(challenge)


@router.post("/gateway/whatsapp/webhook")
async def gateway_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, object]:
    svc = request.app.state.channel_gateway_service
    raw_body = await request.body()
    payload = await request.json()
    try:
        return svc.accept_whatsapp_webhook(raw_body=raw_body, signature_header=x_hub_signature_256, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/gateway/telegram/webhook")
async def gateway_telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, object]:
    svc = request.app.state.channel_gateway_service
    payload = await request.json()
    try:
        return svc.accept_telegram_webhook(payload=payload, secret_token=x_telegram_bot_api_secret_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
