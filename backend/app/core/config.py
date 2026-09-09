from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    Application Settings powered by pydantic-settings.
    Reads environment variables from environment or backend/.env file.
    None of the external services (Database, Redis, JWT) are required for foundation startup.
    """
    # Application metadata
    PROJECT_NAME: str = "SIH26103 Backend"
    API_V1_STR: str = "/api/v1"

    # Server configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database settings (Optional during Phase 1 foundation)
    DATABASE_URL: Optional[str] = None

    # Redis settings (Optional during Phase 1 foundation)
    REDIS_URL: Optional[str] = None

    # Security settings (Optional during Phase 1 foundation)
    JWT_SECRET: Optional[str] = None

    # CORS settings (configurable via environment variable CORS_ORIGINS)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
