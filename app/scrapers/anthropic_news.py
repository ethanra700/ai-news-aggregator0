"""Anthropic news scraper: latest articles from Anthropic's News, Research and Engineering pages.

Anthropic has no official RSS feed, so this reads community-maintained feeds from
https://github.com/Olshansk/rss-feeds (they scrape anthropic.com and publish RSS files).

Usage:
    scraper = AnthropicScraper()
    articles = scraper.get_articles(hours=24)
    markdown = scraper.get_article_markdown(articles[0].url)
"""

from datetime import datetime, timedelta, timezone

import feedparser
import trafilatura
from pydantic import BaseModel

FEED_URLS = [
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
]


class AnthropicArticle(BaseModel):
    guid: str
    title: str
    description: str
    url: str
    published_at: datetime
    category: str | None = None


class AnthropicScraper:
    def get_articles(self, hours: int = 24) -> list[AnthropicArticle]:
        """Articles from all three feeds published in the last `hours`, newest first, without duplicates."""
        # The feeds only have the publish *day* (time is always 00:00), so round the cutoff down to
        # the start of that day. Otherwise a post from yesterday would fall outside a 24-hour window.
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)

        articles = {}  # guid -> article, so a post that appears in several feeds is only kept once
        for feed_url in FEED_URLS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Skip broken entries: without a date we can't filter, without a title/link it's useless in the digest.
                if not entry.get("published_parsed") or not entry.get("title") or not entry.get("link"):
                    continue

                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                guid = entry.get("id", entry.link)
                if published_at >= cutoff and guid not in articles:
                    articles[guid] = AnthropicArticle(
                        guid=guid,
                        title=entry.title,
                        description=entry.get("description", ""),
                        url=entry.link,
                        published_at=published_at,
                        category=entry.tags[0].term if entry.get("tags") else None,
                    )
        return sorted(articles.values(), key=lambda article: article.published_at, reverse=True)

    def get_article_markdown(self, url: str) -> str | None:
        """Download the article page and return its main text as Markdown, or None if it can't be fetched."""
        html = trafilatura.fetch_url(url)
        if not html:
            return None
        return trafilatura.extract(html, output_format="markdown")


if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles = scraper.get_articles(hours=200)
