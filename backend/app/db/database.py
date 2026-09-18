"""Database connection and session management."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


def _fix_database_url(url: str) -> str:
    """
    Fix the database URL for SQLAlchemy 2.0 compatibility.

    Render's managed PostgreSQL provides URLs starting with 'postgres://',
    but SQLAlchemy 2.0 requires 'postgresql://'. This function normalises
    the URL at runtime so the deployment works without manual configuration.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        logger.info("Database URL normalised: postgres:// → postgresql://")
    return url


_database_url = _fix_database_url(settings.database_url)

# SQLAlchemy engine
# pool_size and max_overflow are kept small for Render's free PostgreSQL tier
# which allows a maximum of ~5 concurrent connections.
engine = create_engine(
    _database_url,
    pool_pre_ping=True,  # Verify connection before use
    pool_size=2,
    max_overflow=3,
    pool_timeout=30,
    echo=settings.environment == "development",
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a database session and ensure cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
