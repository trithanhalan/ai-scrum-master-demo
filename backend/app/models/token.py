from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, JSON, Integer, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from .tenant import Tenant

class Connection(Base):
    """Stores Jira connection identity and tokens for each user"""
    __tablename__ = "connections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Jira Identity
    account_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)  # Atlassian user accountId
    cloud_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)    # Atlassian site cloudId
    display_name: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # OAuth Tokens
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Raw OAuth response for debugging
    raw: Mapped[dict] = mapped_column(JSON, default={})
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    def is_expired(self) -> bool:
        """Check if the access token is expired"""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def __repr__(self):
        return f"<Connection(id={self.id}, account_id={self.account_id}, cloud_id={self.cloud_id})>"

# Keep OAuthToken for backward compatibility if needed
class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(255), index=True)  # Jira account ID
    cloud_id: Mapped[str] = mapped_column(String(255), index=True)    # Jira cloud ID
    provider: Mapped[str] = mapped_column(String(50), default="jira")  # jira, slack, github
    
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    token_type: Mapped[str] = mapped_column(String(50), default="Bearer")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Store raw OAuth response for debugging
    raw_response: Mapped[dict] = mapped_column(JSON, default={})
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="oauth_tokens")
    
    def is_expired(self) -> bool:
        """Check if the access token is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) >= self.expires_at