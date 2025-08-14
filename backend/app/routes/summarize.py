from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.token import OAuthToken
from app.jira_client import refresh_if_needed, jira_search_issues
from app.services.ai import summarize_list

router = APIRouter(prefix="/summarize", tags=["summarize"])

def _get_token(db: Session, account_id: str) -> OAuthToken:
    tk = db.query(OAuthToken).filter_by(account_id=account_id).order_by(OAuthToken.id.desc()).first()
    if not tk:
        raise HTTPException(404, "No token for account")
    return tk

@router.get("/standup")
def summarize_standup(accountId: str, db: Session = Depends(get_db)):
    tk = _get_token(db, accountId)
    tk = refresh_if_needed(db, tk)
    res = jira_search_issues(tk, "updated >= -1d ORDER BY updated DESC")

    issues = res.get("issues", [])
    if not issues:
        return {"summary": "No recent Jira activity to summarize.", "raw_issues": []}

    bullets = [f"- {i.get('key','?')}: {i.get('fields',{}).get('summary','')}" for i in issues]
    md = "\n".join(bullets)
    return {"summary": summarize_list(md), "raw_issues": bullets}