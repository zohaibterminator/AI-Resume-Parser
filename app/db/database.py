from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from dotenv import load_dotenv
import os
load_dotenv()

# Example for PostgreSQL (e.g. Supabase)
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_metadata():
    return Base.metadata


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()