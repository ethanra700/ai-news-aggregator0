"""Stage 2 for Anthropic: download the full text (markdown) for saved articles that don't have it yet.

Run:  uv run python -m app.services.process_anthropic
"""

from app.database.repository import ArticleRepository
from app.scrapers.anthropic_news import AnthropicScraper


def process_anthropic_markdown() -> int:
    """Fill in `markdown` for every Anthropic article where it's empty. Returns how many were filled in."""
    repo = ArticleRepository()
    scraper = AnthropicScraper()

    articles = repo.get_anthropic_articles_without_markdown()
    processed = 0
    for article in articles:
        markdown = scraper.get_article_markdown(article.url)
        if markdown:
            repo.update_anthropic_markdown(article.guid, markdown)
            processed += 1
        else:
            print(f"Could not get markdown for: {article.url}")  # stays empty, so the next run retries it

    print(f"Anthropic: added markdown to {processed} of {len(articles)} article(s)")
    return processed


if __name__ == "__main__":
    process_anthropic_markdown()
