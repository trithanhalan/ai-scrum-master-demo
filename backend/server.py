# Compatibility module for supervisor configuration
# This redirects to our main FastAPI app
from app.main import app

# This allows supervisor to load the app as server:app
__all__ = ["app"]