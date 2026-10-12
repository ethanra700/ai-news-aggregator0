"""Stage 3: write a digest entry (title + 2-3 sentence summary) for every article/video that doesn't have one yet.

Input is everything in the database: youtube_videos, openai_articles and anthropic_articles.
Each result is saved to the `digests` table, so items are only ever summarized once.

Run:  uv run python -m app.services.process_digests
"""

from app.agent.digest_agent import DigestAgent
from app.database.models import TRANSCRIPT_UNAVAILABLE, AnthropicArticle, OpenAIArticle, YouTubeVideo
from app.database.repository import ArticleRepository

SOURCES = [
    ("youtube", YouTubeVideo),
    ("openai", OpenAIArticle),
    ("anthropic", AnthropicArticle),
]


def get_content(article_type: str, item) -> str | None:
    """The text to summarize for one row, or None if it isn't ready yet."""
    if article_type == "youtube":
        if item.transcript is None:
            return None  # stage 2 (process_youtube) hasn't run for this video yet
        if item.transcript == TRANSCRIPT_UNAVAILABLE:
            return item.description or item.title  # no transcript, so the description is all we have
        return item.transcript
    if article_type == "anthropic":
        return item.markdown or item.description or item.title
    return item.description or item.title  # openai: the feed only has a short description


def process_digests() -> int:
    """Summarize every article/video without a digest. Returns how many digests were created."""
    repo = ArticleRepository()
    agent = DigestAgent()

    created = 0
    for article_type, table in SOURCES:
        for item in repo.get_without_digest(table, article_type):
            content = get_content(article_type, item)
            if content is None:
                print(f"Skipping (transcript not fetched yet): {item.title}")
                continue

            try:
                digest = agent.summarize(title=item.title, content=content, source=article_type)
            except Exception as error:  # one failed request shouldn't stop the rest; it's retried next run
                print(f"Failed to summarize {item.url}: {error}")
                continue

            article_id = item.video_id if article_type == "youtube" else item.guid
            created += repo.save_digest(article_type, article_id, item.url, digest.title, digest.summary)
            print(f"[{article_type}] {digest.title}")

    print(f"\nDigests: created {created} new")
    return created


if __name__ == "__main__":
    process_digests()
