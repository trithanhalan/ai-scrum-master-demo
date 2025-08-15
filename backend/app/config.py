# app/config.py
from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Core / App ---
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Swagger / CORS toggles
    ENABLE_SWAGGER_UI: bool = True
    ENABLE_CORS: bool = True

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_ORIGIN: Optional[str] = None

    # --- Security / JWT ---
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Storage / Infra ---
    DATABASE_URL: str = "sqlite:///./ai_scrum_master.db"
    REDIS_URL: str = "redis://localhost:6379"

    # --- Feature Flags ---
    ENABLE_AI_FEATURES: bool = True
    ENABLE_REAL_TIME_UPDATES: bool = True
    ENABLE_WEBHOOKS: bool = True
    ENABLE_OAUTH: bool = True

    # --- OpenAI ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7

    # --- Atlassian / Jira OAuth ---
    OAUTH_CLIENT_ID: str
    OAUTH_CLIENT_SECRET: str

    # Map env REDIRECT_URI -> OAUTH_REDIRECT_URI
    OAUTH_REDIRECT_URI: str = Field(
        default="http://localhost:8000/auth/callback",
        alias="REDIRECT_URI",
    )

    # Atlassian endpoints + audience + scopes
    OAUTH_AUTH_URL: str = "https://auth.atlassian.com/authorize"
    OAUTH_TOKEN_URL: str = "https://auth.atlassian.com/oauth/token"
    OAUTH_AUDIENCE: str = "api.atlassian.com"          # <-- add this
    OAUTH_SCOPES: str = "read:jira-user read:jira-work write:jira-work offline_access"

    # --- Jira REST (optional legacy/basic usage) ---
    JIRA_BASE_URL: Optional[str] = None
    JIRA_EMAIL: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None

    # --- Webhooks ---
    WEBHOOK_SHARED_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # ------------ Convenience helpers ------------
    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

    @property
    def cors_allowed_origins(self) -> List[str]:
        if not self.FRONTEND_URL:
            return []
        return [o.strip() for o in self.FRONTEND_URL.split(",") if o.strip()]

    # --- Back-compat shims used by jira_client.py ---
    @property
    def OAUTH_AUTHORIZE_URL(self) -> str:
        return self.OAUTH_AUTH_URL

    @property
    def OAUTH_ACCESS_TOKEN_URL(self) -> str:
        return self.OAUTH_TOKEN_URL

    @property
    def frontend_origin(self) -> str:
        return (self.FRONTEND_ORIGIN or self.FRONTEND_URL or "http://localhost:3000").rstrip("/")


settings = Settings()