"""
Database configuration.
Uses SQLite for local/demo purposes (easy to run with zero setup).
To move to PostgreSQL later: just change SQLALCHEMY_DATABASE_URL below to:
  postgresql://user:password@localhost/dbname
and add 'psycopg2-binary' to requirements.txt. No other code changes needed
since SQLAlchemy abstracts the underlying database.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./banking_assistant.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
