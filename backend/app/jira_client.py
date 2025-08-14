# Legacy sync functions for backward compatibility
from typing import Dict
from sqlalchemy.orm import Session
from app.models.token import OAuthToken

def refresh_if_needed(db: Session, tk: OAuthToken) -> OAuthToken:
    """Legacy sync function - refresh token if needed"""
    # For now, just return the token as-is
    # In a full implementation, this would refresh expired tokens
    return tk

def jira_search_issues(tk: OAuthToken, jql: str) -> Dict:
    """Legacy sync function - search Jira issues"""
    # TODO: call Jira search API (placeholder result)
    return {"issues": []}