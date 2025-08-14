from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import Base, engine
from app.routes.auth import router as auth_router
from app.routes.webhooks import router as webhooks_router
from app.routes.insights import router as insights_router
from app.routes.summarize import router as summarize_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Scrum Master – Jira", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "AI Scrum Master API is running."}

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/version")
def version(): return {"version": "0.1.0"}

app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(insights_router)
app.include_router(summarize_router)