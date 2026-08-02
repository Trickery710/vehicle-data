"""FastAPI application factory and standalone server entrypoint."""

from __future__ import annotations

import argparse
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.config import get_settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.db.init_db import run_migrations
from backend.app.logging_config import configure_logging
from shared.mechanic_shop_shared.constants import API_V1_PREFIX

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    run_migrations()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Mechanic Shop Manager API", version="0.1.0", lifespan=lifespan)

    # Loopback-only by design (see server_manager.py), but the frontend's
    # httpx client and any local dev tooling still cross an "origin" from
    # CORS's point of view -- permissive is safe here since this never
    # listens on a public interface.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=API_V1_PREFIX)
    return app


def run_server() -> None:
    """Console-script entrypoint (``mechanic-shop-server``) and the target
    the frontend's ``ServerManager`` spawns as a subprocess."""
    parser = argparse.ArgumentParser(description="Run the Mechanic Shop Manager backend")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    host = args.host or settings.api_host
    port = args.port or settings.api_port

    uvicorn.run(create_app(), host=host, port=port, log_config=None)


if __name__ == "__main__":
    run_server()
