"""Application configuration.

Settings are sourced from environment variables (prefixed ``MSM_``) with
sensible local-first defaults, so the app runs out of the box with no
configuration file required.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    """XDG-compliant data directory, matching where a packaged .deb would write."""
    xdg_data_home = Path.home() / ".local" / "share"
    return xdg_data_home / "mechanic-shop-manager"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MSM_", env_file=".env", extra="ignore")

    data_dir: Path = _default_data_dir()
    database_url: str | None = None
    api_host: str = "127.0.0.1"
    api_port: int = 8756
    log_level: str = "INFO"
    vin_online_lookup_enabled: bool = True
    vpic_timeout_seconds: float = 3.0

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        self.data_dir.mkdir(parents=True, exist_ok=True)
        db_path = self.data_dir / "mechanic_shop.db"
        return f"sqlite:///{db_path}"

    def log_file_path(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "backend.log"


@lru_cache
def get_settings() -> Settings:
    return Settings()
