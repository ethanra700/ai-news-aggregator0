"""Runs every scraper and collects the results in one place.

Usage:
    results = run_scrapers(hours=24)
    results.youtube, results.openai, results.anthropic
"""

from pydantic import BaseModel

from app.config import YOUTUBE_CHANNELS
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


if __name__ == "__main__":
    results = run_scrapers(hours=24)
