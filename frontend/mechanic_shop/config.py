"""Frontend configuration: data/log directory and backend connection settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from shared.mechanic_shop_shared.constants import DEFAULT_API_HOST, DEFAULT_API_PORT


def data_dir() -> Path:
    """Same XDG data directory the backend uses -- keeps logs/config together."""
    path = Path.home() / ".local" / "share" / "mechanic-shop-manager"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class FrontendSettings:
    backend_url: str | None = None  # if set, skip spawning and connect to this URL directly
    preferred_port: int = DEFAULT_API_PORT
    host: str = DEFAULT_API_HOST
    startup_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> FrontendSettings:
        return cls(
            backend_url=os.environ.get("MSM_BACKEND_URL") or None,
            preferred_port=int(os.environ.get("MSM_API_PORT", DEFAULT_API_PORT)),
            host=os.environ.get("MSM_API_HOST", DEFAULT_API_HOST),
        )
