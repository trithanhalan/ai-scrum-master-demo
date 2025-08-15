from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# 👇 This line loads environment variables from the .env file at runtime
load_dotenv()

class Settings(BaseSettings):
    # App Config
    APP_ENV: str = "development"
    DEBUG: bool = True
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"  # Legacy support
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    log_level: str = "INFO"
    enable_swagger_ui: bool = True
    enable_cors: bool = True

    # Database & Cache
    DATABASE_URL: str = "sqlite:///./ai_scrum_master.db"
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT Configuration  
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MIN: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI Configuration
    OPENAI_API_KEY: str = "change-me"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.4

    # Jira Configuration
    jira_base_url: str = "https://your-domain.atlassian.net"
    jira_email: str = ""
    jira_api_token: str = ""
    jira_cloud_id: str = ""  # For testing when no OAuth token available
    jira_board_id: str = ""  # For testing when no OAuth token available
    enable_ai_features: bool = True
    enable_real_time_updates: bool = True
    enable_webhooks: bool = True
    enable_oauth: bool = True

    # Jira OAuth (PKCE)
    OAUTH_CLIENT_ID: str
    OAUTH_CLIENT_SECRET: str
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    OAUTH_SCOPES: str = "read:jira-user read:jira-work write:jira-work offline_access"
    OAUTH_AUTHORIZE_URL: str = "https://auth.atlassian.com/authorize"
    OAUTH_TOKEN_URL: str = "https://auth.atlassian.com/oauth/token"
    OAUTH_AUDIENCE: str = "api.atlassian.com"

    # Webhook Configuration
    WEBHOOK_SHARED_SECRET: str = "change-me"

    @property
    def is_oauth_configured(self) -> bool:
        """Check if OAuth is properly configured"""
        return bool(self.OAUTH_CLIENT_ID and self.OAUTH_CLIENT_SECRET)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"  # Allow extra fields from .env file
    )

    @property
    def is_oauth_configured(self) -> bool:
        """Check if OAuth is properly configured"""
        return bool(self.OAUTH_CLIENT_ID and self.OAUTH_CLIENT_SECRET)

    # Slack/GitHub placeholders
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY_BASE64: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# ✅ Make sure to call Settings directly without comma
settings = Settings()