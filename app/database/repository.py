"""Simple CRUD interface for the source tables. The rest of the app uses this instead of raw SQL.

Usage:
    repo = ArticleRepository()
    repo.save_youtube_videos(videos)                      # create (takes the scraper models directly)
    repo.get_recent(YouTubeVideo, hours=24)               # read
    repo.update_anthropic_markdown(guid, "# Article...")  # update
    repo.delete(OpenAIArticle, guid)                      # delete
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.database.connection import SessionLocal
from app.database.models import AnthropicArticle, Base, OpenAIArticle, YouTubeVideo

# The scrapers' Pydantic models have the same names as the database models, so import them by module.
from app.scrapers import anthropic_news, openai_news, youtube

SourceTable = type[YouTubeVideo] | type[OpenAIArticle] | type[AnthropicArticle]


class ArticleRepository:
    # --- Create ---

    def save_youtube_videos(self, videos: list[youtube.ChannelVideo]) -> int:
        rows = [
            {
                "video_id": video.video_id,
                "title": video.title,
                "url": video.url,
                "channel_id": video.channel_id,
                "published_at": video.published_at,
                "description": video.description,
                "transcript": video.transcript.text if video.transcript else None,
            }
            for video in videos
        ]
        return self._insert(YouTubeVideo, rows)

    def save_openai_articles(self, articles: list[openai_news.OpenAIArticle]) -> int:
        return self._insert(OpenAIArticle, [article.model_dump() for article in articles])

    def save_anthropic_articles(self, articles: list[anthropic_news.AnthropicArticle]) -> int:
        return self._insert(AnthropicArticle, [article.model_dump() for article in articles])

    def _insert(self, table: type[Base], rows: list[dict]) -> int:
        """Insert rows, skipping any whose primary key is already saved. Returns how many were new."""
        if not rows:
            return 0
        primary_key = [column.name for column in table.__table__.primary_key]
        statement = insert(table).values(rows).on_conflict_do_nothing(index_elements=primary_key)
        with SessionLocal() as session:
            result = session.execute(statement)
            session.commit()
            return result.rowcount

    # --- Read ---

    def get_recent(self, table: SourceTable, hours: int = 24) -> list:
        """Rows from `table` published in the last `hours`, newest first."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        statement = select(table).where(table.published_at >= cutoff).order_by(table.published_at.desc())
        with SessionLocal() as session:
            return list(session.scalars(statement))

    def get_youtube_videos_without_transcript(self) -> list[YouTubeVideo]:
        """Videos whose transcript couldn't be fetched yet (e.g. YouTube blocked the request)."""
        statement = select(YouTubeVideo).where(YouTubeVideo.transcript.is_(None))
        with SessionLocal() as session:
            return list(session.scalars(statement))

    def get_anthropic_articles_without_markdown(self) -> list[AnthropicArticle]:
        """Articles whose full text hasn't been downloaded yet."""
        statement = select(AnthropicArticle).where(AnthropicArticle.markdown.is_(None))
        with SessionLocal() as session:
            return list(session.scalars(statement))

    # --- Update ---

    def update_youtube_transcript(self, video_id: str, transcript: str) -> None:
        with SessionLocal() as session:
            session.execute(update(YouTubeVideo).where(YouTubeVideo.video_id == video_id).values(transcript=transcript))
            session.commit()

    def update_anthropic_markdown(self, guid: str, markdown: str) -> None:
        with SessionLocal() as session:
            session.execute(update(AnthropicArticle).where(AnthropicArticle.guid == guid).values(markdown=markdown))
            session.commit()

    # --- Delete ---

    def delete(self, table: SourceTable, id: str) -> None:
        """Delete one row by its primary key (video_id or guid)."""
        with SessionLocal() as session:
            row = session.get(table, id)
            if row:
                session.delete(row)
                session.commit()
