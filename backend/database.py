"""
Database Configuration Module
SQLAlchemy engine setup with SQLite for development.
Swap SQLALCHEMY_DATABASE_URL to PostgreSQL for production.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Development: SQLite ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./campus.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    pool_pre_ping=True,
)

# Enable WAL mode for better concurrent read performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

# --- Production: PostgreSQL ---
# SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@localhost:5432/campus_db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=20, max_overflow=30)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
