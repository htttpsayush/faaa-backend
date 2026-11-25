from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import normalize_database_url, settings

database_url = normalize_database_url(settings.DATABASE_URL)

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(database_url, connect_args=connect_args)

# Enable SQLite Write-Ahead Logging (WAL) to avoid concurrency lock errors
if database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency that yields a database session for a single request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
