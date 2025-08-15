import secrets
import base64
import hashlib
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Cookie, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.token import Connection
from app.services.auth_service import auth_service
from app.services.jira_client import jira_client, get_jira_boards, get_jira_projects
from app.config import settings
from app.logging_config import logger

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory (dev); replace with Redis in prod
oauth_states: Dict[str, Dict[str, str]] = {}

def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge

@router.get("/jira/login")
async def start_jira_auth(redirect: bool = Query(default=True),
                          db: Session = Depends(get_db)):
    """Start Jira OAuth PKCE flow with direct redirect to Atlassian"""
    try:
        code_verifier, code_challenge = generate_pkce_pair()
        state = secrets.token_urlsafe(32)
        oauth_states[state] = {"code_verifier": code_verifier, "provider": "jira"}

        auth_url = await jira_client.get_authorization_url(state, code_challenge)
        logger.info("Started Jira OAuth flow", state=state, auth_url_masked=auth_url.split("?")[0])

        if redirect:
            # Send the browser straight to Atlassian
            return RedirectResponse(url=auth_url, status_code=302)

        # Fallback for programmatic usage
        return {"authorization_url": auth_url, "state": state}

    except Exception as e:
        logger.error("Failed to start Jira OAuth", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")

@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Jira and persist identity"""
    try:
        logger.info("OAuth callback received", state=state, code_present=bool(code))
        
        if state not in oauth_states:
            logger.warning("Invalid OAuth state", state=state)
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        code_verifier = oauth_states[state]["code_verifier"]

        # Exchange code for tokens
        token_data = await jira_client.exchange_code_for_token(code, code_verifier)

        # Get user info & resources
        user_info = await auth_service.get_user_info(token_data["access_token"])
        account_id = user_info["account_id"]
        display_name = user_info.get("name")
        email = user_info.get("email")

        resources = await auth_service.get_accessible_resources(token_data["access_token"])
        if not resources:
            raise HTTPException(status_code=400, detail="No accessible Jira sites found")

        resource = resources[0]
        cloud_id = resource["id"]

        # Calculate expiry
        from datetime import datetime, timezone, timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))

        # Persist connection
        connection = auth_service.upsert_connection(
            db,
            account_id=account_id,
            cloud_id=cloud_id,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            expires_at=expires_at,
            display_name=display_name,
            email=email,
            scopes=token_data.get("scope"),
            raw={"token_data": token_data, "user_info": user_info, "resources": resources},
        )

        # Set secure cookie
        response.set_cookie(
            key="asm_conn",
            value=str(connection.id),
            httponly=True,
            samesite="lax",
            secure=False,  # Set to True in HTTPS production
            max_age=30 * 24 * 60 * 60,
        )

        # Cleanup state
        try:
            del oauth_states[state]
        except KeyError:
            pass

        logger.info("OAuth success", connection_id=connection.id, account_id=account_id, cloud_id=cloud_id)

        # Redirect back to frontend with success
        frontend_url = f"{settings.frontend_origin}?auth=success&cloud_id={cloud_id}&account_id={account_id}"
        return RedirectResponse(url=frontend_url, status_code=302)

    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        error_msg = str(e).replace("&", "%26").replace("=", "%3D")
        frontend_url = f"{settings.frontend_origin}?auth=error&message={error_msg}"
        return RedirectResponse(url=frontend_url, status_code=302)

@router.get("/connection")
async def get_current_connection(
    db: Session = Depends(get_db),
    asm_conn: Optional[str] = Cookie(default=None)
):
    """Get the current connection identity for the authenticated user"""
    try:
        connection = None
        if asm_conn:
            try:
                connection = auth_service.get_connection_by_id(db, int(asm_conn))
            except Exception:
                pass
        if not connection:
            connection = auth_service.get_latest_active_connection(db)
        if not connection:
            return {"authenticated": False, "message": "No active connection. Authenticate with Jira."}

        try:
            connection = await auth_service.refresh_connection_if_needed(db, connection)
        except Exception as e:
            logger.error("Refresh failed", error=str(e))
            return {"authenticated": False, "message": "Connection expired. Re-authenticate."}

        return {
            "authenticated": True,
            "connection_id": connection.id,
            "account_id": connection.account_id,
            "cloud_id": connection.cloud_id,
            "display_name": connection.display_name,
            "email": connection.email,
            "expires_at": connection.expires_at.isoformat(),
        }
    except Exception as e:
        logger.error("Connection check failed", error=str(e))
        return {"authenticated": False, "message": f"Connection check failed: {str(e)}"}

@router.get("/jira/boards")
async def get_boards(db: Session = Depends(get_db), asm_conn: Optional[str] = Cookie(default=None)):
    """Get Jira boards for the authenticated user"""
    try:
        connection = None
        if asm_conn:
            try: 
                connection = auth_service.get_connection_by_id(db, int(asm_conn))
            except Exception: 
                pass
        if not connection: 
            connection = auth_service.get_latest_active_connection(db)
        if not connection:
            raise HTTPException(status_code=401, detail="Authenticate with Jira first.")

        try:
            connection = await auth_service.refresh_connection_if_needed(db, connection)
        except Exception:
            raise HTTPException(status_code=401, detail="Refresh failed. Re-authenticate.")

        boards = await get_jira_boards(connection)
        return {"success": True, "boards": boards.get("values", []), "total": boards.get("total", 0)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get boards failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch boards: {str(e)}")

@router.get("/jira/projects")
async def get_projects(db: Session = Depends(get_db), asm_conn: Optional[str] = Cookie(default=None)):
    """Get Jira projects for the authenticated user"""
    try:
        connection = None
        if asm_conn:
            try: 
                connection = auth_service.get_connection_by_id(db, int(asm_conn))
            except Exception: 
                pass
        if not connection: 
            connection = auth_service.get_latest_active_connection(db)
        if not connection:
            raise HTTPException(status_code=401, detail="Authenticate with Jira first.")

        try:
            connection = await auth_service.refresh_connection_if_needed(db, connection)
        except Exception:
            raise HTTPException(status_code=401, detail="Refresh failed. Re-authenticate.")

        projects = await get_jira_projects(connection)
        return {"success": True, "projects": projects, "total": (len(projects) if isinstance(projects, list) else 0)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get projects failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

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