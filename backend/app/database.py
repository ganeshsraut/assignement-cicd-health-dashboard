from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session as ORMSession
from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()

def init_db():
    from . import models  # noqa: F401 - ensure models are imported
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Type alias
Session = ORMSession
