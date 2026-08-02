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

    # Deliberately minimal placeholders for PDF invoice headers -- a real
    # shop-settings table + Settings screen (shop info, labor rate, tax
    # rates, invoice numbering) is Phase 3/4 scope. See backend/app/pdf/
    # shop_info.py, which takes a small value object so swapping in a real
    # settings table later requires no change to the PDF renderer itself.
    shop_name: str = "Mechanic Shop Manager"
    shop_address: str = ""
    shop_phone: str = ""
    shop_email: str = ""

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
