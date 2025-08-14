from typing import Dict
from sqlalchemy.orm import Session
from app.models.token import OAuthToken

def refresh_if_needed(db: Session, tk: OAuthToken) -> OAuthToken:
    # TODO: refresh token via Atlassian if expired (placeholder)
    return tk

def jira_search_issues(tk: OAuthToken, jql: str) -> Dict:
    # TODO: call Jira search API (placeholder result)
    return {"issues": []}