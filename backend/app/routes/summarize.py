from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.token import OAuthToken
from app.services.jira_client import refresh_if_needed as async_refresh_if_needed, jira_search_issues as async_jira_search_issues
from app.services.openai_client import openai_service
from app.telemetry.metrics import record_ai_request, record_jira_api_call
from app.logging_config import logger

router = APIRouter(prefix="/summarize", tags=["summarize"])

def _get_token(db: Session, cloud_id: str) -> OAuthToken:
    """Get OAuth token for cloud instance"""
    tk = db.query(OAuthToken).filter_by(cloud_id=cloud_id).first()
    if not tk:
        raise HTTPException(404, "No token found for Jira instance")
    return tk

@router.get("/standup")
async def summarize_standup(cloudId: str, db: Session = Depends(get_db)):
    """Generate AI-powered standup summary from recent Jira activity"""
    try:
        tk = _get_token(db, cloudId)
        tk = await async_refresh_if_needed(db, tk)
        
        # Search for issues updated in the last 24 hours
        jql = "updated >= -1d ORDER BY updated DESC"
        res = await async_jira_search_issues(tk, jql)
        
        record_jira_api_call("search", "success" if "error" not in res else "error")
        
        issues = res.get("issues", [])
        if not issues:
            return {
                "summary": "No recent Jira activity to summarize.",
                "raw_issues": [],
                "issue_count": 0
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
                   cloud_id=cloudId, 
                   issue_count=len(issues))
        
        return {
            "summary": ai_summary,
            "raw_issues": bullets,
            "issue_count": len(issues)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Standup summary failed", error=str(e), cloud_id=cloudId)
        raise HTTPException(500, f"Failed to generate standup summary: {str(e)}")

@router.get("/blockers")
async def summarize_blockers(cloudId: str, db: Session = Depends(get_db)):
    """Identify and summarize potential blockers from Jira issues"""
    try:
        tk = _get_token(db, cloudId)
        tk = await async_refresh_if_needed(db, tk)
        
        # Search for potentially blocked issues
        blocked_jql = 'status in ("Blocked", "Stuck", "On Hold", "Waiting") OR summary ~ "blocked" OR summary ~ "blocker" ORDER BY updated DESC'
        res = await async_jira_search_issues(tk, blocked_jql)
        
        record_jira_api_call("search_blockers", "success" if "error" not in res else "error")
        
        issues = res.get("issues", [])
        if not issues:
            return {
                "summary": "No obvious blockers found in recent Jira activity.",
                "raw_issues": [],
                "blocker_count": 0
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
                   cloud_id=cloudId, 
                   blocker_count=len(issues))
        
        return {
            "summary": ai_analysis,
            "raw_issues": bullets,
            "blocker_count": len(issues)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Blocker analysis failed", error=str(e), cloud_id=cloudId)
        raise HTTPException(500, f"Failed to analyze blockers: {str(e)}")

@router.get("/retrospective")
async def generate_retrospective(
    boardId: str,
    sprintId: str = None,
    cloudId: str = None,
    db: Session = Depends(get_db)
):
    """Generate AI-powered sprint retrospective"""
    try:
        if cloudId:
            tk = _get_token(db, cloudId)
            tk = await async_refresh_if_needed(db, tk)
            
            # Search for sprint-related issues
            if sprintId:
                jql = f'sprint = {sprintId} ORDER BY updated DESC'
            else:
                jql = f'project in boardProjects({boardId}) AND sprint in openSprints() ORDER BY updated DESC'
                
            res = await async_jira_search_issues(tk, jql)
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

Total Issues: {len(issues)}
Completed: {completed_count}
In Progress: {in_progress_count}
Remaining: {len(issues) - completed_count - in_progress_count}

Issue Details:
{chr(10).join(issue_details)}
"""
        else:
            # Fallback to mock data if no authentication
            sprint_data = f"Sprint retrospective requested for Board {boardId}" + (f" Sprint {sprintId}" if sprintId else "")
            issues = []
        
        # Generate AI retrospective
        record_ai_request("gpt-4o-mini", "retrospective")
        ai_retrospective = openai_service.generate_retrospective(sprint_data)
        
        logger.info("Generated retrospective", 
                   board_id=boardId,
                   sprint_id=sprintId,
                   account_id=accountId)
        
        return {
            "retrospective": ai_retrospective,
            "board_id": boardId,
            "sprint_id": sprintId,
            "issue_count": len(issues) if cloudId else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Retrospective generation failed", error=str(e))
        raise HTTPException(500, f"Failed to generate retrospective: {str(e)}")