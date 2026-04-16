"""Database connection and session management for FastAPI backend."""

from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path



DB_PATH = Path("data/international_visitor_arrivals.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Initialize database tables (if needed)."""
    SQLModel.metadata.create_all(engine)


from typing import Generator


def get_session() -> Generator[Session, None, None]:
    """Get a database session using dependency injection."""
    with Session(engine) as session:
        yield session
