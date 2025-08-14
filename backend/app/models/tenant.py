from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    workspaces: Mapped[list["Workspace"]] = relationship("Workspace", back_populates="tenant")
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")
    oauth_tokens: Mapped[list["OAuthToken"]] = relationship("OAuthToken", back_populates="tenant")

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jira_cloud_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships  
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="workspaces")
    users: Mapped[list["User"]] = relationship("User", back_populates="workspace")

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True) 
    workspace_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    account_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # Jira account ID
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="users")