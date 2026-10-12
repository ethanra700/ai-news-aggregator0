"""Entry point: scrape all sources and save new items to the database.

Run:  uv run python main.py        (last 24 hours)
      uv run python main.py 48     (last 48 hours)
"""

import sys

from app.runner import ScrapeResults, run


def main(hours: int = 24) -> ScrapeResults:
    results = run(hours=hours)

    print(f"\n=== Scraping Results (last {hours} hours) ===")
    print(f"YouTube videos: {len(results.youtube)}")
    print(f"OpenAI articles: {len(results.openai)}")
    print(f"Anthropic articles: {len(results.anthropic)}")

    return results


if __name__ == "__main__":
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    main(hours=hours)
