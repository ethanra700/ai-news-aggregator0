"""Stage 4: rank the digests from the last 24 hours by relevance to the user profile (app/user_profile.py).

Run:  uv run python -m app.services.curate_digests
"""

from app.agent.curator_agent import CuratorAgent, RankedDigest
from app.database.repository import ArticleRepository


def curate_digests(hours: int = 24) -> list[RankedDigest]:
    """Rank digests created in the last `hours`. Returns them most relevant first."""
    digests = ArticleRepository().get_recent_digests(hours)
    if not digests:
        print(f"No digests created in the last {hours} hours. Run process_digests first.")
        return []

    ranked = CuratorAgent().rank(digests)

    print(f"=== {len(ranked)} digest(s) ranked for you (last {hours} hours) ===\n")
    for item in ranked:
        print(f"{item.rank}. [{item.relevance_score}/10] {item.title}  ({item.article_type})")
        print(f"   Why: {item.reasoning}")
        print(f"   {item.url}\n")
    return ranked


if __name__ == "__main__":
    curate_digests(hours=24)
