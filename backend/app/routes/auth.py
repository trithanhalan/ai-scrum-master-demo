from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/start")
def start_auth():
    return {"status": "ok"}  # TODO