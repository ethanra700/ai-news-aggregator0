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


def run(hours: int = 24) -> ScrapeResults:
    """Scrape all sources and save new items to their tables (items already saved are skipped)."""
    results = run_scrapers(hours)
    repo = ArticleRepository()
    new_youtube = repo.save_youtube_videos(results.youtube)
    new_openai = repo.save_openai_articles(results.openai)
    new_anthropic = repo.save_anthropic_articles(results.anthropic)
    print(f"Saved to database - YouTube: {new_youtube} new, OpenAI: {new_openai} new, Anthropic: {new_anthropic} new")
    return results


if __name__ == "__main__":
    run(hours=24)
