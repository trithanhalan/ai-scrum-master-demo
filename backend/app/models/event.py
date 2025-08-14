from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dedup_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)  # jira_issue, github_pr, slack_message
    source: Mapped[str] = mapped_column(String(50), index=True)       # jira, github, slack
    
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # For tracking processing status
    status: Mapped[str] = mapped_column(String(50), default="processed")  # processed, failed, retrying
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

class JiraIssueEvent(Base):
    __tablename__ = "jira_issue_events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    issue_key: Mapped[str] = mapped_column(String(50), index=True)         # PROJ-123
    issue_id: Mapped[str] = mapped_column(String(50), index=True)          # Jira internal ID
    cloud_id: Mapped[str] = mapped_column(String(255), index=True)         # Jira cloud instance
    
    event_type: Mapped[str] = mapped_column(String(100), index=True)       # issue_created, issue_updated, etc.
    user_account_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    
    # Issue data snapshot
    issue_summary: Mapped[str] = mapped_column(String(500), nullable=True)
    issue_status: Mapped[str] = mapped_column(String(100), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=True)
    assignee_account_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Full webhook payload for debugging
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # Index for efficient queries
    __table_args__ = (
        Index('ix_jira_events_tenant_issue', 'tenant_id', 'issue_key'),
        Index('ix_jira_events_created_at', 'created_at'),
    )