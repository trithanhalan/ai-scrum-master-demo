from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import create_tables
from app.routes.auth import router as auth_router
from app.routes.webhooks import router as webhooks_router
from app.routes.insights import router as insights_router
from app.routes.summarize import router as summarize_router
from app.telemetry.metrics import get_metrics, MetricsMiddleware
from app.logging_config import logger
import os

from app.models import *  # Ensures all models are registered

if settings.DEBUG:
    create_tables()

# ✅ App initialization (KEEP ONLY THIS ONE)
app = FastAPI(
    title="AI Scrum Master – Jira", 
    version="0.1.0",
    description="Intelligent Agile Automation Platform with Jira, Slack, and GitHub integrations"
)

# ✅ Middleware: Metrics
app.add_middleware(MetricsMiddleware)

# ✅ Middleware: CORS
frontend_origin = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Health Endpoints
@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "AI Scrum Master API is running."}

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/version")
def version():
    return {"version": "0.1.0", "environment": settings.APP_ENV}

@app.get("/metrics")
def metrics():
    return get_metrics()

# ✅ Include Routers
app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(insights_router)
app.include_router(summarize_router)

logger.info("AI Scrum Master API started", environment=settings.APP_ENV)