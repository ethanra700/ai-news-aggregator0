"""OpenAI news scraper: latest articles from the OpenAI news RSS feed.

Usage:
    scraper = OpenAIScraper()
    articles = scraper.get_articles(hours=24)
"""

from datetime import datetime, timedelta, timezone

import feedparser
from pydantic import BaseModel

FEED_URL = "https://openai.com/news/rss.xml"
USER_AGENT = "Mozilla/5.0"  # openai.com may refuse requests that don't look like a browser


class OpenAIArticle(BaseModel):
    guid: str
    title: str
    description: str
    url: str
    published_at: datetime
    category: str | None = None


class OpenAIScraper:
    def get_articles(self, hours: int = 24) -> list[OpenAIArticle]:
        """Articles from the RSS feed published in the last `hours`, newest first."""
        feed = feedparser.parse(FEED_URL, agent=USER_AGENT)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        articles = []
        for entry in feed.entries:
            # Skip broken entries: without a date we can't filter, without a title/link it's useless in the digest.
            if not entry.get("published_parsed") or not entry.get("title") or not entry.get("link"):
                continue

            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_at >= cutoff:
                articles.append(
                    OpenAIArticle(
                        guid=entry.get("id", entry.link),
                        title=entry.title,
                        description=entry.get("description", ""),
                        url=entry.link,
                        published_at=published_at,
                        category=entry.tags[0].term if entry.get("tags") else None,
                    )
                )
        return sorted(articles, key=lambda article: article.published_at, reverse=True)


if __name__ == "__main__":
    scraper = OpenAIScraper()
    articles = scraper.get_articles(hours=200)
