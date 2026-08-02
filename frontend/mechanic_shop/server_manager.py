"""Manages the local backend server's process lifecycle.

Spawns ``uvicorn`` (via the backend's own entrypoint) as a subprocess bound
to a loopback host, polls its health endpoint until ready, and terminates it
on app exit. If ``FrontendSettings.backend_url`` is set (env var
``MSM_BACKEND_URL``), spawning is skipped entirely and the frontend connects
to an already-running backend instead -- this is the same code path that
will point a technician's client at a shop server's LAN address once
multiple-technician support is added.
"""

from __future__ import annotations

import logging
import socket
import subprocess
import sys
import time
from typing import IO

import httpx

from frontend.mechanic_shop.config import FrontendSettings, data_dir
from shared.mechanic_shop_shared.constants import API_V1_PREFIX

logger = logging.getLogger(__name__)


class BackendStartupError(RuntimeError):
    """Raised when the backend process fails to start or become healthy in time."""


class ServerManager:
    def __init__(self, settings: FrontendSettings | None = None) -> None:
        self._settings = settings or FrontendSettings.from_env()
        self._process: subprocess.Popen | None = None
        self._base_url: str = ""
        self._log_file: IO[str] | None = None

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def api_base_url(self) -> str:
        return f"{self._base_url}{API_V1_PREFIX}"

    def start(self) -> None:
        if self._settings.backend_url:
            self._base_url = self._settings.backend_url.rstrip("/")
            logger.info("Connecting to externally-managed backend at %s", self._base_url)
            self._wait_until_healthy()
            return

        port = _find_available_port(self._settings.host, self._settings.preferred_port)
        self._base_url = f"http://{self._settings.host}:{port}"

        log_path = data_dir() / "backend.log"
        self._log_file = open(log_path, "a")  # noqa: SIM115 -- lives for the process's duration
        logger.info("Starting backend on %s (log: %s)", self._base_url, log_path)

        self._process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "backend.app.main",
                "--host",
                self._settings.host,
                "--port",
                str(port),
            ],
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
        )
        self._wait_until_healthy()

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            self._process = None
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None

    def _wait_until_healthy(self) -> None:
        deadline = time.monotonic() + self._settings.startup_timeout_seconds
        last_error: Exception | None = None

        while time.monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                raise BackendStartupError(
                    f"Backend process exited early (code {self._process.returncode}). "
                    f"Check the log at {data_dir() / 'backend.log'}"
                )
            try:
                response = httpx.get(f"{self.api_base_url}/health", timeout=1.0)
                if response.status_code == 200:
                    logger.info("Backend is healthy at %s", self._base_url)
                    return
            except httpx.RequestError as exc:
                last_error = exc
            time.sleep(0.2)

        timeout = self._settings.startup_timeout_seconds
        raise BackendStartupError(f"Backend did not become healthy within {timeout}s: {last_error}")


def _find_available_port(host: str, preferred_port: int) -> int:
    """Tries the preferred port first; falls back to an OS-assigned free
    port if it's taken. Small TOCTOU race between this check and the child
    process binding is acceptable for a local single-user dev/desktop tool."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, preferred_port))
            return preferred_port
        except OSError:
            probe.bind((host, 0))
            return probe.getsockname()[1]
