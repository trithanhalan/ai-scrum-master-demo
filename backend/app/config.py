from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Config
    APP_ENV: str = "development"
    DEBUG: bool = True
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Database & Cache - Use mounted volume path for persistence
    DATABASE_URL: str = "sqlite:////data/app.db"  # Use mounted volume for persistence
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT Configuration  
    JWT_SECRET: str = "ai-scrum-master-jwt-secret-key"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MIN: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI Configuration
    OPENAI_API_KEY: str = "change-me"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.4

    # Jira OAuth (PKCE) - Using port 8001 for our backend
    OAUTH_CLIENT_ID: str = "change-me"
    OAUTH_CLIENT_SECRET: str = "change-me"
    OAUTH_REDIRECT_URI: str = "http://localhost:8001/auth/callback"
    OAUTH_SCOPES: str = "read:jira-user read:jira-work write:jira-work offline_access"
    OAUTH_AUTHORIZE_URL: str = "https://auth.atlassian.com/authorize"
    OAUTH_TOKEN_URL: str = "https://auth.atlassian.com/oauth/token"
    OAUTH_AUDIENCE: str = "api.atlassian.com"

    # Jira API Settings (for direct API calls)
    JIRA_BASE_URL: str = "https://trithanhalan.atlassian.net"
    JIRA_EMAIL: str = "trithanhalan@gmail.com"
    JIRA_API_TOKEN: str = "change-me"

    # Webhook Configuration
    WEBHOOK_SHARED_SECRET: str = "change-me"

    # Slack/GitHub placeholders
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY_BASE64: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()