from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mc_user:mc_pass@localhost:5432/mission_control"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me"
    api_key_header: str = "X-MC-API-Key"
    agent_api_keys: str = "agent-key-1"
    operator_username: str = "admin"
    operator_password: str = "changeme"
    environment: str = "development"
    # Comma-separated list of allowed CORS origins in production.
    # Example: "https://mc.example.com,https://admin.example.com"
    allowed_origins: str = ""

    @property
    def agent_keys_list(self) -> List[str]:
        return [k.strip() for k in self.agent_api_keys.split(",")]

    @property
    def cors_origins(self) -> List[str]:
        if self.environment == "development":
            return ["*"]
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",")]
        return []

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
