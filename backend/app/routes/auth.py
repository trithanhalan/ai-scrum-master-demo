import secrets
import base64
import hashlib
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.token import OAuthToken
from app.services.jira_client import jira_client
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
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Jira"""
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
        
        # Get accessible resources (Jira sites)
        resources = await jira_client.get_accessible_resources(token_data["access_token"])
        
        if not resources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No accessible Jira sites found"
            )
        
        # Use the first accessible resource
        resource = resources[0]
        cloud_id = resource["id"]
        site_name = resource["name"]
        
        # Get or create tenant
        tenant = db.query(Tenant).filter_by(domain=site_name).first()
        if not tenant:
            tenant = Tenant(name=site_name, domain=site_name)
            db.add(tenant)
            db.flush()
        
        # Calculate expiry time
        from datetime import datetime, timezone, timedelta
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
        
        # Store or update OAuth token
        existing_token = db.query(OAuthToken).filter_by(
            cloud_id=cloud_id,
            provider="jira"
        ).first()
        
        if existing_token:
            # Update existing token
            existing_token.access_token = token_data["access_token"]
            existing_token.refresh_token = token_data.get("refresh_token")
            existing_token.expires_at = expires_at
            existing_token.scope = token_data.get("scope")
            existing_token.raw_response = token_data
            existing_token.updated_at = datetime.now(timezone.utc)
            token = existing_token
        else:
            # Create new token
            token = OAuthToken(
                tenant_id=tenant.id,
                account_id=token_data.get("account_id", "unknown"),
                cloud_id=cloud_id,
                provider="jira",
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=expires_at,
                scope=token_data.get("scope"),
                raw_response=token_data
            )
            db.add(token)
        
        db.commit()
        
        # Clean up state
        del oauth_states[state]
        
        logger.info("OAuth flow completed successfully", 
                   cloud_id=cloud_id, 
                   tenant_id=tenant.id)
        
        # Redirect to frontend with success
        frontend_url = f"{settings.FRONTEND_ORIGIN}?auth=success&cloud_id={cloud_id}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        # Redirect to frontend with error
        frontend_url = f"{settings.FRONTEND_ORIGIN}?auth=error&message={str(e)}"
        return RedirectResponse(url=frontend_url)

@router.get("/status")
async def auth_status(cloud_id: str = None, db: Session = Depends(get_db)):
    """Check authentication status for a cloud ID"""
    try:
        if not cloud_id:
            return {"authenticated": False, "message": "No cloud_id provided"}
        
        token = db.query(OAuthToken).filter_by(
            cloud_id=cloud_id,
            provider="jira"
        ).first()
        
        if not token:
            return {"authenticated": False, "message": "No token found"}
        
        if token.is_expired():
            return {"authenticated": False, "message": "Token expired"}
        
        return {
            "authenticated": True,
            "cloud_id": token.cloud_id,
            "account_id": token.account_id,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None
        }
        
    except Exception as e:
        logger.error("Auth status check failed", error=str(e))
        return {"authenticated": False, "message": str(e)}

@router.post("/logout")
async def logout(cloud_id: str, db: Session = Depends(get_db)):
    """Logout and revoke OAuth token"""
    try:
        token = db.query(OAuthToken).filter_by(
            cloud_id=cloud_id,
            provider="jira"
        ).first()
        
        if token:
            db.delete(token)
            db.commit()
            logger.info("Token revoked", cloud_id=cloud_id)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )