"""Runs every scraper and saves the results to the database.

Usage:
    run(hours=24)                      # scrape all sources and save new items
    results = run_scrapers(hours=24)   # only scrape: results.youtube, results.openai, results.anthropic
"""

from pydantic import BaseModel

from app.config import YOUTUBE_CHANNELS
from app.database.repository import ArticleRepository
from app.scrapers.anthropic_news import AnthropicArticle, AnthropicScraper
from app.scrapers.openai_news import OpenAIArticle, OpenAIScraper
from app.scrapers.youtube import ChannelVideo, YouTubeScraper


class ScrapeResults(BaseModel):
    youtube: list[ChannelVideo]
    openai: list[OpenAIArticle]
    anthropic: list[AnthropicArticle]


def run_scrapers(hours: int = 24) -> ScrapeResults:
    """Scrape all sources for content published in the last `hours`."""
    youtube_scraper = YouTubeScraper()
    videos = []
    for channel_id in YOUTUBE_CHANNELS:
        videos.extend(youtube_scraper.scrape_channel(channel_id, hours))

    return ScrapeResults(
        youtube=videos,
        openai=OpenAIScraper().get_articles(hours),
        anthropic=AnthropicScraper().get_articles(hours),
    )


def to_database_rows(results: ScrapeResults) -> list[dict]:
    """Convert the scraper models into rows for the `articles` table (every row needs the same keys)."""
    rows = []
    for video in results.youtube:
        rows.append(
            {
                "source": "youtube",
                "guid": video.video_id,
                "title": video.title,
                "url": video.url,
                "description": None,
                "content": video.transcript.text if video.transcript else None,
                "published_at": video.published_at,
            }
        )
    for source, articles in [("openai", results.openai), ("anthropic", results.anthropic)]:
        for article in articles:
            rows.append(
                {
                    "source": source,
                    "guid": article.guid,
                    "title": article.title,
                    "url": article.url,
                    "description": article.description,
                    "content": None,  # full article text can be added later
                    "published_at": article.published_at,
                }
            )
    return rows


def run(hours: int = 24) -> int:
    """Scrape all sources and save new items to the database. Returns how many were new."""
    results = run_scrapers(hours)
    rows = to_database_rows(results)
    new_count = ArticleRepository().save_articles(rows)
    print(f"Scraped {len(rows)} item(s), {new_count} new saved to the database")
    return new_count


if __name__ == "__main__":
    run(hours=24)
