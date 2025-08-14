from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.base import Base

# Create database engine with PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use
    pool_recycle=300      # Recycle connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False, 
    future=True
)

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables (for development only)"""
    Base.metadata.create_all(bind=engine)