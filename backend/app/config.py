from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    OPENAI_API_KEY: str = "change-me"

    OAUTH_CLIENT_ID: str = "change-me"
    OAUTH_CLIENT_SECRET: str = "change-me"
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    OAUTH_SCOPES: str = "read:jira-user read:jira-work write:jira-work offline_access"
    OAUTH_AUTHORIZE_URL: str = "https://auth.atlassian.com/authorize"
    OAUTH_TOKEN_URL: str = "https://auth.atlassian.com/oauth/token"
    OAUTH_AUDIENCE: str = "api.atlassian.com"

    WEBHOOK_SHARED_SECRET: str = "change-me"

    DATABASE_URL: str = "sqlite:///./app.db"  # can switch to Postgres in docker-compose
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET: str = "change-me"
    ENV: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()