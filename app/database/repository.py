"""Simple CRUD interface for articles. The rest of the app uses this instead of raw SQL.

Usage:
    repo = ArticleRepository()
    repo.save_articles([{"source": "openai", "guid": ..., "title": ..., "url": ..., "published_at": ...}])  # create
    repo.get_recent_articles(hours=24)                                                                      # read
    repo.update_summary(article_id, "Short summary...")                                                     # update
    repo.delete_article(article_id)                                                                         # delete
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from app.database.connection import SessionLocal
from app.database.models import Article


class ArticleRepository:
    # --- Create ---

    def save_articles(self, articles: list[dict]) -> int:
        """Insert articles, skipping any whose URL is already saved. Returns how many were new."""
        if not articles:
            return 0
        statement = insert(Article).values(articles).on_conflict_do_nothing(index_elements=["url"])
        with SessionLocal() as session:
            result = session.execute(statement)
            session.commit()
            return result.rowcount

    # --- Read ---

    def get_article(self, article_id: int) -> Article | None:
        with SessionLocal() as session:
            return session.get(Article, article_id)

    def get_recent_articles(self, hours: int = 24) -> list[Article]:
        """Articles published in the last `hours`, newest first."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        statement = select(Article).where(Article.published_at >= cutoff).order_by(Article.published_at.desc())
        with SessionLocal() as session:
            return list(session.scalars(statement))

    def get_articles_without_summary(self) -> list[Article]:
        """Articles the LLM hasn't summarized yet."""
        statement = select(Article).where(Article.summary.is_(None)).order_by(Article.published_at.desc())
        with SessionLocal() as session:
            return list(session.scalars(statement))

    # --- Update ---

    def update_summary(self, article_id: int, summary: str) -> None:
        with SessionLocal() as session:
            session.execute(update(Article).where(Article.id == article_id).values(summary=summary))
            session.commit()

    # --- Delete ---

    def delete_article(self, article_id: int) -> None:
        with SessionLocal() as session:
            session.execute(delete(Article).where(Article.id == article_id))
            session.commit()
