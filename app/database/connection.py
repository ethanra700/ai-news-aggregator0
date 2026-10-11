"""Database connection: the engine (connection pool) and a session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL

# pool_pre_ping checks a connection still works before using it (hosted databases close idle ones).
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)
