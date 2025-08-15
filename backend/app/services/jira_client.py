import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from app.config import settings
from app.models.token import OAuthToken
from app.logging_config import logger

class JiraOAuthClient:
    """Async Jira client with OAuth 2.0 PKCE support"""
    
    def __init__(self):
        if not settings.is_oauth_configured:
            raise ValueError("OAuth client ID and secret must be configured in environment variables")
            
        self.client_id = settings.OAUTH_CLIENT_ID
        self.client_secret = settings.OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.OAUTH_REDIRECT_URI
        self.authorize_url = settings.OAUTH_AUTHORIZE_URL
        self.token_url = settings.OAUTH_TOKEN_URL
        self.audience = settings.OAUTH_AUDIENCE
        self.scopes = settings.OAUTH_SCOPES
    
    async def get_authorization_url(self, state: str, code_challenge: str) -> str:
        """Generate OAuth authorization URL with PKCE"""
        params = {
            "audience": self.audience,
            "client_id": self.client_id,
            "scope": self.scopes,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, code_verifier: str) -> Dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "code_verifier": code_verifier
            }
            
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token
            }
            
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user info from access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_accessible_resources(self, access_token: str) -> List[Dict]:
        """Get list of Jira sites user has access to"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def search_issues(self, token: OAuthToken, jql: str, max_results: int = 50) -> Dict:
        """Search Jira issues using JQL"""
        if token.is_expired():
            raise Exception("Token is expired")
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.atlassian.com/ex/jira/{token.cloud_id}/rest/api/3/search"
            params = {
                "jql": jql,
                "maxResults": max_results,
                "fields": "summary,status,assignee,created,updated,issuetype,changelog"
            }
            
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token.access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_board_sprints(self, token: OAuthToken, board_id: str, state: Optional[str] = None) -> List[Dict]:
        """Get sprints for a board"""
        if token.is_expired():
            raise Exception("Token is expired")
        
        async with httpx.AsyncClient() as client:
            url = f"https://api.atlassian.com/ex/jira/{token.cloud_id}/rest/agile/1.0/board/{board_id}/sprint"
            params = {"state": state} if state else {}
            
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token.access_token}"}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("values", [])

    async def get_sprint_issues(self, token: OAuthToken, sprint_id: str) -> List[Dict]:
        """Get all issues in a sprint"""
        if token.is_expired():
            raise Exception("Token is expired")
        
        jql = f"sprint = {sprint_id} ORDER BY created DESC"
        result = await self.search_issues(token, jql, max_results=100)
        return result.get("issues", [])

# Global instance
jira_client = JiraOAuthClient()

async def refresh_if_needed(db: Session, token: OAuthToken) -> OAuthToken:
    """Refresh token if needed and update in database"""
    if not token.is_expired():
        return token
    
    if not token.refresh_token:
        raise Exception("Token expired and no refresh token available")
    
    try:
        # Refresh the token
        token_data = await jira_client.refresh_access_token(token.refresh_token)
        
        # Update token in database
        token.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            token.refresh_token = token_data["refresh_token"]
        
        # Calculate expiry time
        expires_in = token_data.get("expires_in", 3600)
        token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        token.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(token)
        
        return token
        
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to refresh token: {str(e)}")

async def jira_search_issues(token: OAuthToken, jql: str) -> Dict:
    """Search Jira issues with the given JQL"""
    try:
        return await jira_client.search_issues(token, jql)
    except Exception as e:
        logger.error("Jira search failed", error=str(e))
        return {"issues": [], "error": str(e)}