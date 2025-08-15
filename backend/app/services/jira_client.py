import httpx
import json
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from app.config import settings
from app.telemetry.metrics import record_jira_api_call
from app.logging_config import logger

class JiraOAuthClient:
    """Enhanced Jira client with OAuth 2.0 PKCE support and API token fallback"""
    
    def __init__(self):
        self.client_id = settings.OAUTH_CLIENT_ID
        self.client_secret = settings.OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.OAUTH_REDIRECT_URI
        self.authorize_url = settings.OAUTH_AUTHORIZE_URL
        self.token_url = settings.OAUTH_TOKEN_URL
        self.audience = settings.OAUTH_AUDIENCE
        self.scopes = settings.OAUTH_SCOPES
        
        # API token fallback
        self.jira_base_url = settings.JIRA_BASE_URL
        self.jira_email = settings.JIRA_EMAIL
        self.jira_api_token = settings.JIRA_API_TOKEN
    
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
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Atlassian API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/me",
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
                    "fields": "summary,status,assignee,created,updated,issuetype,priority,description"
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
            logger.error("Jira API call failed", error=str(e))
            raise Exception(f"Jira API call failed: {str(e)}")
    
    async def search_issues_with_api_token(self, jql: str, max_results: int = 50) -> Dict:
        """Fallback method using API token for direct Jira calls"""
        try:
            # Create basic auth header
            auth_string = f"{self.jira_email}:{self.jira_api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            async with httpx.AsyncClient() as client:
                url = f"{self.jira_base_url}/rest/api/3/search"
                params = {
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,assignee,created,updated,issuetype,priority,description"
                }
                
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Basic {auth_b64}"}
                )
                response.raise_for_status()
                record_jira_api_call("search_api_token", "success")
                return response.json()
                
        except Exception as e:
            record_jira_api_call("search_api_token", "error")
            logger.error("Jira API token call failed", error=str(e))
            raise Exception(f"Jira API token call failed: {str(e)}")
    
    async def get_boards(self, connection) -> Dict:
        """Get all boards accessible to the user"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.atlassian.com/ex/jira/{connection.cloud_id}/rest/agile/1.0/board"
                
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {connection.access_token}"}
                )
                response.raise_for_status()
                record_jira_api_call("get_boards", "success")
                return response.json()
                
        except Exception as e:
            record_jira_api_call("get_boards", "error")
            logger.error("Get boards failed", error=str(e))
            raise Exception(f"Get boards failed: {str(e)}")
    
    async def get_sprints(self, connection, board_id: str) -> Dict:
        """Get sprints for a specific board"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.atlassian.com/ex/jira/{connection.cloud_id}/rest/agile/1.0/board/{board_id}/sprint"
                
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {connection.access_token}"}
                )
                response.raise_for_status()
                record_jira_api_call("get_sprints", "success")
                return response.json()
                
        except Exception as e:
            record_jira_api_call("get_sprints", "error")
            logger.error("Get sprints failed", error=str(e))
            raise Exception(f"Get sprints failed: {str(e)}")

# Global instance
jira_client = JiraOAuthClient()

async def jira_search_issues(connection, jql: str) -> Dict:
    """Search Jira issues with the given JQL using Connection object"""
    try:
        return await jira_client.search_issues(connection, jql)
    except Exception as e:
        # Try fallback with API token if OAuth fails
        try:
            logger.info("OAuth failed, trying API token fallback")
            return await jira_client.search_issues_with_api_token(jql)
        except Exception as fallback_error:
            logger.error("Both OAuth and API token failed", 
                        oauth_error=str(e), 
                        api_token_error=str(fallback_error))
            # Return empty result with error info if both methods fail
            return {"issues": [], "error": f"OAuth: {str(e)}, API Token: {str(fallback_error)}"}

async def get_jira_boards(connection) -> Dict:
    """Get Jira boards for the connected user"""
    try:
        return await jira_client.get_boards(connection)
    except Exception as e:
        return {"values": [], "error": str(e)}

async def get_jira_sprints(connection, board_id: str) -> Dict:
    """Get sprints for a Jira board"""
    try:
        return await jira_client.get_sprints(connection, board_id)
    except Exception as e:
        return {"values": [], "error": str(e)}