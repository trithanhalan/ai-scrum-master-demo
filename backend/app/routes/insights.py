from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.insights import make_sprint_insights
from app.services.jira_client import jira_client, refresh_if_needed
from app.models import OAuthToken
from app.logging_config import logger

router = APIRouter(prefix="/insights", tags=["insights"])

def _get_token(db: Session, cloud_id: str) -> OAuthToken:
    """Get valid OAuth token for cloud instance"""
    tk = db.query(OAuthToken).filter_by(cloud_id=cloud_id).first()
    if not tk:
        raise HTTPException(404, "No token found for Jira instance")
    return tk

@router.get("/sprint")
async def sprint_insights(
    boardId: str,
    cloudId: str = Query(..., description="The Jira Cloud ID to use"),
    db: Session = Depends(get_db)
):
    """Get insights for the active sprint on a board"""
    try:
        # Get and refresh token if needed
        token = _get_token(db, cloudId)
        token = await refresh_if_needed(db, token)
        
        # First get active sprint
        sprints = await jira_client.get_board_sprints(token, boardId, state="active")
        if not sprints:
            return {
                "completed": 0,
                "remaining": 0,
                "contributors": [],
                "scope_changes": [],
                "burndown": [],
                "message": "No active sprint found"
            }
            
        active_sprint = sprints[0]
        sprint_id = active_sprint["id"]
        
        # Get all issues in the sprint
        issues = await jira_client.get_sprint_issues(token, sprint_id)
        
        # Generate insights
        insights = make_sprint_insights(issues)
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to get sprint insights", error=error_msg)
        
        # Handle common errors with user-friendly messages
        if "Token expired" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Your Jira session has expired. Please reconnect to Jira."
            )
        elif "No token found" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please connect to Jira."
            )
        elif "Failed to refresh token" in error_msg:
            raise HTTPException(
                status_code=401,
                detail="Failed to refresh your Jira session. Please reconnect to Jira."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to get sprint insights. Please try again later."
            )