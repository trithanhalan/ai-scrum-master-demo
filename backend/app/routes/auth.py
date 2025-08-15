import secrets
import base64
import hashlib
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Cookie, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.token import Connection
from app.services.auth_service import auth_service
from app.services.jira_client import jira_client, get_jira_boards, get_jira_projects
from app.config import settings
from app.logging_config import logger

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory storage for OAuth state (in production, use Redis)
oauth_states = {}

def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    code_verifier = code_verifier.rstrip('=')
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8')
    code_challenge = code_challenge.rstrip('=')
    
    return code_verifier, code_challenge

@router.get("/jira/login")
async def start_jira_auth(db: Session = Depends(get_db)):
    """Start Jira OAuth PKCE flow"""
    try:
        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce_pair()
        state = secrets.token_urlsafe(32)
        
        # Store PKCE parameters (in production, use Redis with expiration)
        oauth_states[state] = {
            "code_verifier": code_verifier,
            "provider": "jira"
        }
        
        # Generate authorization URL
        auth_url = await jira_client.get_authorization_url(state, code_challenge)
        
        logger.info("Started Jira OAuth flow", state=state)
        
        return {
            "authorization_url": auth_url,
            "state": state
        }
        
    except Exception as e:
        logger.error("Failed to start Jira OAuth", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth flow"
        )

@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Jira and persist identity"""
    try:
        # Validate state parameter
        if state not in oauth_states:
            logger.warning("Invalid OAuth state", state=state)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        oauth_data = oauth_states[state]
        code_verifier = oauth_data["code_verifier"]
        
        # Exchange code for tokens
        token_data = await jira_client.exchange_code_for_token(code, code_verifier)
        
        # Get user info from Atlassian
        user_info = await auth_service.get_user_info(token_data["access_token"])
        account_id = user_info["account_id"]
        display_name = user_info.get("name")
        email = user_info.get("email")
        
        # Get accessible resources (Jira sites)
        resources = await auth_service.get_accessible_resources(token_data["access_token"])
        
        if not resources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No accessible Jira sites found"
            )
        
        # Use the first accessible resource (or let user choose in future)
        resource = resources[0]
        cloud_id = resource["id"]
        site_name = resource["name"]
        
        # Calculate expiry time
        from datetime import datetime, timezone, timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
        
        # Persist connection identity
        connection = auth_service.upsert_connection(
            db,
            account_id=account_id,
            cloud_id=cloud_id,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_at=expires_at,
            display_name=display_name,
            email=email,
            scopes=token_data.get("scope"),
            raw={
                "token_data": token_data,
                "user_info": user_info,
                "resources": resources
            }
        )
        
        # Set secure cookie to tie browser session to connection
        response.set_cookie(
            key="asm_conn",
            value=str(connection.id),
            httponly=True,
            samesite="lax",
            secure=False,  # Set to True in production with HTTPS
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        # Clean up state
        del oauth_states[state]
        
        logger.info("OAuth flow completed successfully", 
                   connection_id=connection.id,
                   account_id=account_id,
                   cloud_id=cloud_id)
        
        # Redirect to frontend with success
        frontend_url = f"{settings.FRONTEND_ORIGIN}?auth=success&cloud_id={cloud_id}&account_id={account_id}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        # Redirect to frontend with error
        error_msg = str(e).replace("&", "%26").replace("=", "%3D")
        frontend_url = f"{settings.FRONTEND_ORIGIN}?auth=error&message={error_msg}"
        return RedirectResponse(url=frontend_url)

@router.get("/connection")
async def get_current_connection(
    db: Session = Depends(get_db),
    asm_conn: Optional[str] = Cookie(default=None)
):
    """Get the current connection identity for the authenticated user"""
    try:
        connection = None
        
        # Try to get connection from cookie
        if asm_conn:
            try:
                connection_id = int(asm_conn)
                connection = auth_service.get_connection_by_id(db, connection_id)
            except (ValueError, TypeError):
                logger.warning("Invalid connection cookie", cookie_value=asm_conn)
        
        # Fallback to most recent active connection (MVP behavior)
        if not connection:
            connection = auth_service.get_latest_active_connection(db)
        
        if not connection:
            return {
                "authenticated": False,
                "message": "No active connection found. Please authenticate with Jira first."
            }
        
        # Refresh tokens if needed
        try:
            connection = await auth_service.refresh_connection_if_needed(db, connection)
        except Exception as e:
            logger.error("Failed to refresh connection", error=str(e))
            return {
                "authenticated": False,
                "message": "Connection expired and refresh failed. Please re-authenticate."
            }
        
        return {
            "authenticated": True,
            "connection_id": connection.id,
            "account_id": connection.account_id,
            "cloud_id": connection.cloud_id,
            "display_name": connection.display_name,
            "email": connection.email,
            "expires_at": connection.expires_at.isoformat()
        }
        
    except Exception as e:
        logger.error("Connection check failed", error=str(e))
        return {
            "authenticated": False,
            "message": f"Connection check failed: {str(e)}"
        }

@router.get("/status")
async def auth_status(
    db: Session = Depends(get_db),
    cloud_id: Optional[str] = None,
    account_id: Optional[str] = None,
    asm_conn: Optional[str] = Cookie(default=None)
):
    """Check authentication status (legacy endpoint - use /auth/connection instead)"""
    try:
        connection = None
        
        # Try specific account/cloud lookup first
        if account_id and cloud_id:
            connection = auth_service.get_connection_by_account(db, account_id, cloud_id)
        
        # Try cookie lookup
        elif asm_conn:
            try:
                connection_id = int(asm_conn)
                connection = auth_service.get_connection_by_id(db, connection_id)
            except (ValueError, TypeError):
                pass
        
        # Fallback to latest connection
        if not connection:
            connection = auth_service.get_latest_active_connection(db)
        
        if not connection:
            return {"authenticated": False, "message": "No active connection found"}
        
        if connection.is_expired():
            return {"authenticated": False, "message": "Connection expired"}
        
        return {
            "authenticated": True,
            "connection_id": connection.id,
            "account_id": connection.account_id,
            "cloud_id": connection.cloud_id,
            "expires_at": connection.expires_at.isoformat()
        }
        
    except Exception as e:
        logger.error("Auth status check failed", error=str(e))
        return {"authenticated": False, "message": str(e)}

@router.post("/logout")
async def logout(
    response: Response,
    db: Session = Depends(get_db),
    asm_conn: Optional[str] = Cookie(default=None)
):
    """Logout and deactivate connection"""
    try:
        if asm_conn:
            try:
                connection_id = int(asm_conn)
                connection = auth_service.get_connection_by_id(db, connection_id)
                if connection:
                    connection.is_active = False
                    db.commit()
                    logger.info("Connection deactivated", connection_id=connection_id)
            except (ValueError, TypeError):
                pass
        
        # Clear cookie
        response.delete_cookie("asm_conn")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )