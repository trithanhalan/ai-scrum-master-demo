from typing import Dict
from sqlalchemy.orm import Session
from app.models import Token

def refresh_if_needed(db: Session, tk: Token) -> Token:
    # TODO: refresh token via Atlassian if expired (placeholder)
    return tk

def jira_search_issues(tk: Token, jql: str) -> Dict:
    # TODO: call Jira search API (placeholder result)
    return {"issues": []}