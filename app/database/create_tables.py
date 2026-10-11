"""Create all database tables. Safe to run more than once: existing tables are left alone.

Run:  uv run python -m app.database.create_tables
"""

from app.database.connection import engine
from app.database.models import Base


def create_tables() -> None:
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
    print("Tables created:", ", ".join(Base.metadata.tables))
