from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.token import Connection
from app.services.auth_service import auth_service
from app.services.jira_client import jira_search_issues as async_jira_search_issues
from app.services.openai_client import openai_service
from app.telemetry.metrics import record_ai_request, record_jira_api_call
from app.logging_config import logger

router = APIRouter(prefix="/summarize", tags=["summarize"])

async def _get_connection(
    db: Session, 
    account_id: Optional[str] = None, 
    cloud_id: Optional[str] = None,
    asm_conn: Optional[str] = None
) -> Connection:
    """Get connection by explicit IDs or from session cookie"""
    
    connection = None
    
    # Try explicit account/cloud lookup first
    if account_id and cloud_id:
        connection = auth_service.get_connection_by_account(db, account_id, cloud_id)
        if connection:
            logger.info("Found connection by account/cloud", account_id=account_id, cloud_id=cloud_id)
    
    # Try session cookie lookup
    elif asm_conn:
        try:
            connection_id = int(asm_conn)
            connection = auth_service.get_connection_by_id(db, connection_id)
            if connection:
                logger.info("Found connection by cookie", connection_id=connection_id)
        except (ValueError, TypeError):
            logger.warning("Invalid connection cookie", cookie_value=asm_conn)
    
    # Fallback to latest active connection (MVP behavior)
    if not connection:
        connection = auth_service.get_latest_active_connection(db)
        if connection:
            logger.info("Using latest active connection", connection_id=connection.id)
    
    if not connection:
        raise HTTPException(404, "No active Jira connection found. Please authenticate with Jira first.")
    
    # Refresh tokens if needed
    try:
        connection = await auth_service.refresh_connection_if_needed(db, connection)
    except Exception as e:
        logger.error("Failed to refresh connection", error=str(e))
        raise HTTPException(401, "Connection expired and refresh failed. Please re-authenticate with Jira.")
    
    return connection

@router.get("/standup")
async def summarize_standup(
    db: Session = Depends(get_db),
    accountId: Optional[str] = None,  # Keep for backward compatibility
    cloudId: Optional[str] = None,   # Keep for backward compatibility
    account_id: Optional[str] = None,
    cloud_id: Optional[str] = None,
    asm_conn: Optional[str] = Cookie(default=None)
):
    """Generate AI-powered standup summary from recent Jira activity"""
    try:
        # Use new parameter names if provided, fall back to old ones
        final_account_id = account_id or accountId
        final_cloud_id = cloud_id or cloudId
        
        connection = await _get_connection(db, final_account_id, final_cloud_id, asm_conn)
        
        # Search for issues updated in the last 24 hours
        jql = "updated >= -1d ORDER BY updated DESC"
        res = await async_jira_search_issues(connection, jql)
        
        record_jira_api_call("search", "success" if "error" not in res else "error")
        
        issues = res.get("issues", [])
        if not issues:
            return {
                "summary": "No recent Jira activity to summarize.",
                "raw_issues": [],
                "issue_count": 0,
                "connection": {
                    "account_id": connection.account_id,
                    "cloud_id": connection.cloud_id,
                    "display_name": connection.display_name
                }
            }

        # Format issues for AI processing
        bullets = []
        for issue in issues[:20]:  # Limit to 20 most recent
            key = issue.get('key', '?')
            fields = issue.get('fields', {})
            summary = fields.get('summary', '')
            status = fields.get('status', {}).get('name', 'Unknown')
            bullets.append(f"- {key}: {summary} (Status: {status})")
        
        issues_text = "\n".join(bullets)
        
        # Generate AI summary
        record_ai_request("gpt-4o-mini", "standup_summary")
        ai_summary = openai_service.summarize_standup(issues_text)
        
        logger.info("Generated standup summary", 
                   connection_id=connection.id,
                   issue_count=len(issues))
        
        return {
            "summary": ai_summary,
            "raw_issues": bullets,
            "issue_count": len(issues),
            "connection": {
                "account_id": connection.account_id,
                "cloud_id": connection.cloud_id,
                "display_name": connection.display_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Standup summary failed", error=str(e))
        raise HTTPException(500, f"Failed to generate standup summary: {str(e)}")

@router.get("/blockers")
async def summarize_blockers(
    db: Session = Depends(get_db),
    accountId: Optional[str] = None,  # Keep for backward compatibility
    cloudId: Optional[str] = None,   # Keep for backward compatibility  
    account_id: Optional[str] = None,
    cloud_id: Optional[str] = None,
    asm_conn: Optional[str] = Cookie(default=None)
):
    """Identify and summarize potential blockers from Jira issues"""
    try:
        # Use new parameter names if provided, fall back to old ones
        final_account_id = account_id or accountId
        final_cloud_id = cloud_id or cloudId
        
        connection = await _get_connection(db, final_account_id, final_cloud_id, asm_conn)
        
        # Search for potentially blocked issues
        blocked_jql = 'status in ("Blocked", "Stuck", "On Hold", "Waiting") OR summary ~ "blocked" OR summary ~ "blocker" ORDER BY updated DESC'
        res = await async_jira_search_issues(connection, blocked_jql)
        
        record_jira_api_call("search_blockers", "success" if "error" not in res else "error")
        
        issues = res.get("issues", [])
        if not issues:
            return {
                "summary": "No obvious blockers found in recent Jira activity.",
                "raw_issues": [],
                "blocker_count": 0,
                "connection": {
                    "account_id": connection.account_id,
                    "cloud_id": connection.cloud_id,
                    "display_name": connection.display_name
                }
            }

        # Format issues for AI processing
        bullets = []
        for issue in issues[:15]:  # Limit to 15 most relevant
            key = issue.get('key', '?')
            fields = issue.get('fields', {})
            summary = fields.get('summary', '')
            status = fields.get('status', {}).get('name', 'Unknown')
            assignee = fields.get('assignee')
            assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
            bullets.append(f"- {key}: {summary} (Status: {status}, Assignee: {assignee_name})")
        
        issues_text = "\n".join(bullets)
        
        # Generate AI analysis
        record_ai_request("gpt-4o-mini", "blocker_analysis")
        ai_analysis = openai_service.identify_blockers(issues_text)
        
        logger.info("Generated blocker analysis", 
                   connection_id=connection.id,
                   blocker_count=len(issues))
        
        return {
            "summary": ai_analysis,
            "raw_issues": bullets,
            "blocker_count": len(issues),
            "connection": {
                "account_id": connection.account_id,
                "cloud_id": connection.cloud_id,
                "display_name": connection.display_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Blocker analysis failed", error=str(e))
        raise HTTPException(500, f"Failed to analyze blockers: {str(e)}")

@router.get("/retrospective")
async def generate_retrospective(
    boardId: str,
    db: Session = Depends(get_db),
    sprintId: Optional[str] = None,
    accountId: Optional[str] = None,  # Keep for backward compatibility
    cloudId: Optional[str] = None,   # Keep for backward compatibility
    account_id: Optional[str] = None,
    cloud_id: Optional[str] = None,
    asm_conn: Optional[str] = Cookie(default=None)
):
    """Generate AI-powered sprint retrospective"""
    try:
        # Use new parameter names if provided, fall back to old ones
        final_account_id = account_id or accountId
        final_cloud_id = cloud_id or cloudId
        
        # Try to get connection, but allow anonymous retrospectives for demo purposes
        connection = None
        try:
            connection = await _get_connection(db, final_account_id, final_cloud_id, asm_conn)
        except HTTPException:
            logger.info("No connection found for retrospective, using demo mode")
        
        if connection:
            # Search for sprint-related issues with real Jira data
            if sprintId:
                jql = f'sprint = {sprintId} ORDER BY updated DESC'
            else:
                jql = f'project in boardProjects({boardId}) AND sprint in openSprints() ORDER BY updated DESC'
                
            res = await async_jira_search_issues(connection, jql)
            record_jira_api_call("search_sprint", "success" if "error" not in res else "error")
            
            issues = res.get("issues", [])
            
            # Format sprint data for AI processing
            sprint_summary = f"Sprint Analysis for Board {boardId}"
            if sprintId:
                sprint_summary += f" (Sprint {sprintId})"
            
            issue_details = []
            completed_count = 0
            in_progress_count = 0
            
            for issue in issues[:25]:  # Limit to 25 issues
                key = issue.get('key', '?')
                fields = issue.get('fields', {})
                summary = fields.get('summary', '')
                status = fields.get('status', {}).get('name', 'Unknown')
                
                if status.lower() in ['done', 'closed', 'resolved']:
                    completed_count += 1
                elif status.lower() in ['in progress', 'in review', 'testing']:
                    in_progress_count += 1
                
                issue_details.append(f"- {key}: {summary} (Status: {status})")
            
            sprint_data = f"""
{sprint_summary}

Connected Account: {connection.display_name or connection.account_id}
Cloud: {connection.cloud_id}

Total Issues: {len(issues)}
Completed: {completed_count}
In Progress: {in_progress_count}
Remaining: {len(issues) - completed_count - in_progress_count}

Issue Details:
{chr(10).join(issue_details)}
"""
        else:
            # Fallback to mock data for demo purposes
            issues = []
            sprint_data = f"""
Sprint Retrospective Analysis (Demo Mode)

Board: {boardId}
Sprint: {sprintId or 'Current Sprint'}

Note: This is a demonstration using sample data. 
Connect to Jira to get real sprint insights for your team.

Sample Sprint Metrics:
- Total Issues: 15
- Completed: 12
- In Progress: 2  
- Remaining: 1
- Velocity: 24 story points
- Team Satisfaction: 8/10
"""
        
        # Generate AI retrospective
        record_ai_request("gpt-4o-mini", "retrospective")
        ai_retrospective = openai_service.generate_retrospective(sprint_data)
        
        logger.info("Generated retrospective", 
                   board_id=boardId,
                   sprint_id=sprintId,
                   connection_id=connection.id if connection else None)
        
        result = {
            "retrospective": ai_retrospective,
            "board_id": boardId,
            "sprint_id": sprintId,
            "issue_count": len(issues),
            "demo_mode": connection is None
        }
        
        if connection:
            result["connection"] = {
                "account_id": connection.account_id,
                "cloud_id": connection.cloud_id,
                "display_name": connection.display_name
            }
        
        return result
        
    except HTTPException as he:
        # Let specific HTTP exceptions through
        raise
    except Exception as e:
        logger.error("Retrospective generation failed", error=str(e))
        raise HTTPException(500, f"Failed to generate retrospective: {str(e)}")