from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

# Clever Cloud limits this MySQL user to 5 total connections. Keep this
# process well below that cap so restarts and admin bursts do not lock out startup.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=1,
    pool_recycle=1800,
    pool_timeout=15,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
