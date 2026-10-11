"""Create all database tables. Safe to run more than once: existing tables are left alone.

Run:  uv run python -m app.database.create_tables   (or the Run button)
"""

import sys
from pathlib import Path

# Add the project root to Python's import path, so `from app...` works when this file is run directly.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.connection import engine  # noqa: E402
from app.database.models import Base  # noqa: E402


def create_tables() -> None:
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
    print("Tables created:", ", ".join(Base.metadata.tables))
