"""Ping engine control API."""

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.request_context import build_meta, request_meta_context
from api.schema.api_response_schema import ApiResponse
from environment import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ping_engine", tags=["ping_engine"])


class PingEngineStatus(BaseModel):
    """Public ping engine state."""

    online: bool
    message: str
    workers: int | None = None


def _control_url(path: str) -> str:
    settings = get_settings()
    host = "127.0.0.1" if settings.ping_engine_host in {"0.0.0.0", "::"} else settings.ping_engine_host
    return f"http://{host}:{settings.ping_engine_port}{path}"


@router.get("", response_model=ApiResponse[PingEngineStatus], summary="Get ping engine status")
def ping_engine_status():
    """Check the locally bound ping engine control server."""
    with request_meta_context() as meta:
        try:
            response = httpx.get(_control_url("/workers"), timeout=3)
            response.raise_for_status()
            payload = response.json()
            workers = len(payload.get("data") or [])
            data = PingEngineStatus(online=True, message="Ping engine is online", workers=workers)
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Ping engine status unavailable: %s", exc)
            data = PingEngineStatus(online=False, message="Ping engine is unavailable")
    return ApiResponse(meta=build_meta(meta), data=data)


@router.post("/restart", response_model=ApiResponse[PingEngineStatus], summary="Restart ping engine workers")
def restart_ping_engine():
    """Stop ping workers, reload destinations, and start fresh workers."""
    with request_meta_context() as meta:
        try:
            response = httpx.post(_control_url("/restart"), timeout=15)
            response.raise_for_status()
            payload = response.json()
            workers = (payload.get("data") or {}).get("workers")
            data = PingEngineStatus(online=True, message="Ping engine restarted", workers=workers)
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Unable to restart ping engine: %s", exc)
            raise HTTPException(status_code=503, detail="Unable to restart the ping engine") from exc
    return ApiResponse(meta=build_meta(meta), data=data)
