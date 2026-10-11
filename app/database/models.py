"""SQLAlchemy database models (one class = one table)."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Article(Base):
    """One piece of content from any source: a YouTube video or a blog post."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), index=True)  # "youtube", "openai" or "anthropic"
    guid: Mapped[str] = mapped_column(String(500))  # the source's own ID (video ID or feed guid)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1000), unique=True)  # unique, so the same item is never saved twice
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)  # transcript or full article text
    summary: Mapped[str | None] = mapped_column(Text)  # filled in later by the LLM
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
