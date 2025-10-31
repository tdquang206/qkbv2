from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

DATABASE_URL = "sqlite:///./app/database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import app.models.patient_exam_base as models

    Base.metadata.create_all(bind=engine)

def get_db() -> Generator:
    """
    FastAPI dependency that yields a SQLAlchemy Session.
    Use as: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_session = get_db