# app/services/legacy_sync.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.token import OAuthToken

REFRESH_SKEW = timedelta(seconds=90)  # refresh a bit before expiry


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def refresh_if_needed(db: Session, tk: OAuthToken) -> OAuthToken:
    """
    Ensure the OAuth access token is valid.
    If expiring soon (or missing expiry), try refresh_token flow and persist changes.
    """
    needs_refresh = False
    if getattr(tk, "expires_at", None) is None:
        needs_refresh = bool(getattr(tk, "refresh_token", None))
    else:
        exp: datetime = tk.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        needs_refresh = exp <= _now_utc() + REFRESH_SKEW

    if not needs_refresh:
        return tk

    if not tk.refresh_token:
        # No way to refresh; just return as-is.
        return tk

    data = {
        "grant_type": "refresh_token",
        "client_id": settings.OAUTH_CLIENT_ID,
        "client_secret": settings.OAUTH_CLIENT_SECRET,
        "refresh_token": tk.refresh_token,
    }

    try:
        # form-encoded by default with `data=`, as Atlassian expects
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(settings.OAUTH_TOKEN_URL, data=data)
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPError:
        # On any refresh failure, just return the original token (caller may handle 401)
        return tk

    # Expected fields: access_token, expires_in, token_type, scope, (optional) refresh_token
    new_access = payload.get("access_token")
    if not new_access:
        return tk  # unexpected shape

    tk.access_token = new_access
    if payload.get("refresh_token"):
        tk.refresh_token = payload["refresh_token"]

    try:
        expires_in = int(payload.get("expires_in") or 0)
    except (TypeError, ValueError):
        expires_in = 0
    tk.expires_at = _now_utc() + timedelta(seconds=expires_in)

    tk.token_type = payload.get("token_type") or tk.token_type
    tk.scope = payload.get("scope") or tk.scope
    tk.raw_response = payload  # store for debugging/audit

    db.add(tk)
    db.commit()
    db.refresh(tk)
    return tk


def jira_search_issues(
    tk: OAuthToken,
    jql: str,
    max_results: int = 50,
    start_at: int = 0,
) -> Dict:
    """
    Run a Jira JQL search using the user's Cloud access token.

    Requires tk.cloud_id (the Jira site Cloud ID).
    Docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get
    """
    if not tk.cloud_id:
        return {"error": "missing_cloud_id", "issues": []}

    base = f"https://api.atlassian.com/ex/jira/{tk.cloud_id}/rest/api/3/search"
    headers = {
        "Authorization": f"Bearer {tk.access_token}",
        "Accept": "application/json",
    }
    params = {
        "jql": jql,
        "maxResults": max_results,
        "startAt": start_at,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(base, headers=headers, params=params)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": "http_status_error",
            "status_code": e.response.status_code,
            "text": e.response.text,
            "issues": [],
        }
    except httpx.HTTPError as e:
        return {"error": "http_error", "detail": str(e), "issues": []}