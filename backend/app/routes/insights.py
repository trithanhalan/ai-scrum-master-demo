from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.insights import make_sprint_insights

router = APIRouter(prefix="/insights", tags=["insights"])

@router.get("/sprint")
def sprint_insights(boardId: str, accountId: str, db: Session = Depends(get_db)):
    # TODO: fetch Jira issues by board & active sprint
    insights = make_sprint_insights([])
    return insights