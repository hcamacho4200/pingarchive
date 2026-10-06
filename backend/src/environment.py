"""Environment Configuration"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env exactly once, at import time
ENV_PATH = ".env"
load_dotenv(ENV_PATH)

@dataclass(frozen=True)
class Settings:
    """Application settings."""

    environment: str
    log_level: str
    version: str

    # Database Credentials
    db_url: str

    sql_echo: bool
    sqlalchemy_pool_size: int

    # API Configuration
    api_host: str | None
    api_port: int | None
    api_reload: bool
    api_workers: int

    # Ping Engine
    ping_engine_host: str
    ping_engine_port: int

    # QuestDB
    questdb_address: str = "localhost:9000"

    @staticmethod
    def convert_bool(value: str | None, default=False) -> bool:
        """Convert string to boolean."""
        if value is None:
            return default
        return value.lower() in ("1", "true", "yes", "on")


def get_settings() -> Settings:
    """Get settings from environment variables"""

    return Settings(
        environment=os.getenv("ENVIRONMENT", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        version=os.getenv("APP_VERSION", "NA"),
        db_url=os.getenv("DATABASE_URL", "sqlite:///data/pingarchive.db"),
        sql_echo=Settings.convert_bool(os.getenv("SQL_ECHO")),
        sqlalchemy_pool_size=int(os.getenv("SQLALCHEMY_POOL_SIZE", str(5))),
        api_host=os.getenv("API_BIND_HOST"),
        api_port=int(os.getenv("API_BIND_PORT")),
        api_reload=Settings.convert_bool(os.getenv("API_RELOAD")),
        api_workers=int(os.getenv("API_WORKERS", str(1))),
        ping_engine_host=os.getenv("PING_ENGINE_HOST", "0.0.0.0"),
        ping_engine_port=int(os.getenv("PING_ENGINE_PORT", str(8100))),
        questdb_address=os.getenv("QWEST_DB_ADDRESS", "localhost:9000"),
    )
