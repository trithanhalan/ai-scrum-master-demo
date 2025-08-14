from fastapi import APIRouter, Header, HTTPException
from app.config import settings

router = APIRouter(prefix="/webhook", tags=["webhooks"])

@router.post("/jira")
def webhook_jira(x_shared_secret: str | None = Header(default=None)):
    if x_shared_secret != settings.WEBHOOK_SHARED_SECRET:
        raise HTTPException(401, "Invalid secret")
    # TODO: enqueue into Redis Stream 'scrum:events'
    return {"status": "queued"}