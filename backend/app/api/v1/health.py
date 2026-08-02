"""Health check -- polled by the frontend's ``ServerManager`` to know when the
locally-spawned backend is ready to accept requests."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
