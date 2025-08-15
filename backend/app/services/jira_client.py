import httpx
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from app.config import settings
from app.telemetry.metrics import record_jira_api_call

class JiraOAuthClient:
    """Async Jira client with OAuth 2.0 PKCE support"""
    
    def __init__(self):
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
    
    async def get_accessible_resources(self, access_token: str) -> List[Dict]:
        """Get list of Jira sites user has access to"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def search_issues(self, connection, jql: str, max_results: int = 50) -> Dict:
        """Search Jira issues using JQL with Connection object"""
        if connection.is_expired():
            raise Exception("Connection is expired")
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.atlassian.com/ex/jira/{connection.cloud_id}/rest/api/3/search"
                params = {
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,assignee,created,updated,issuetype"
                }
                
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {connection.access_token}"}
                )
                response.raise_for_status()
                record_jira_api_call("search", "success")
                return response.json()
                
        except Exception as e:
            record_jira_api_call("search", "error")
            raise Exception(f"Jira API call failed: {str(e)}")

# Global instance
jira_client = JiraOAuthClient()

async def jira_search_issues(connection, jql: str) -> Dict:
    """Search Jira issues with the given JQL using Connection object"""
    try:
        return await jira_client.search_issues(connection, jql)
    except Exception as e:
        # Return empty result with error info if API call fails
        return {"issues": [], "error": str(e)}