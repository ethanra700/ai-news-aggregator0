"""Insert a few real YouTube videos into youtube_videos, for testing while the RSS feed is down.

Transcripts are left empty so stage 2 (app/services/process_youtube.py) can fill them in.
Safe to run more than once: videos already in the table are skipped.

Run:  uv run python -m app.database.seed_youtube   (or the Run button)
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the project root to Python's import path, so `from app...` works when this file is run directly.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.repository import ArticleRepository  # noqa: E402
from app.scrapers.youtube import ChannelVideo  # noqa: E402

SEED_VIDEOS = [
    ChannelVideo(
        video_id="PUBc2G0Tj5E",
        channel_id="UCXZCJLdBC09xxGZ6gcdrc6A",  # OpenAI
        title="Meet the New Codex CLI",
        url="https://www.youtube.com/watch?v=PUBc2G0Tj5E",
        published_at=datetime(2026, 10, 5, 18, 29, tzinfo=timezone.utc),
        description="OpenAI introduces the new Codex CLI.",
    ),
    ChannelVideo(
        video_id="ZHVNTTKu9fU",
        channel_id="UCbfYPyITQ-7l4upoX8nvctg",  # Two Minute Papers
        title="The Billion Dollar AI Advantage Is Disappearing",
        url="https://www.youtube.com/watch?v=ZHVNTTKu9fU",
        published_at=datetime(2026, 10, 5, 9, 53, tzinfo=timezone.utc),
        description="Two Minute Papers on how quickly frontier AI capabilities are spreading.",
    ),
    ChannelVideo(
        video_id="_rtp1XzaP6Q",
        channel_id="UCNJ1Ymd5yFuUPtn21xtRbbw",  # AI Explained
        title="OpenAI Security: Controlling Models is Now 'Hell'",
        url="https://www.youtube.com/watch?v=_rtp1XzaP6Q",
        published_at=datetime(2026, 10, 1, 21, 20, tzinfo=timezone.utc),
        description="AI Explained on model security and control.",
    ),
    ChannelVideo(
        video_id="1HtydHmdhrQ",
        channel_id="UCn8ujwUInbJkBhffxqAPBVQ",  # Dave Ebbelaar
        title="How to Start Freelancing as an Engineer (Contracts vs Projects)",
        url="https://www.youtube.com/watch?v=1HtydHmdhrQ",
        published_at=datetime(2026, 10, 10, 17, 23, tzinfo=timezone.utc),
        description="Dave Ebbelaar on getting started with freelancing as an engineer.",
    ),
    ChannelVideo(
        video_id="EWvNQjAaOHw",
        channel_id="UCXUPKJO5MZQN11PqgIvyuvQ",  # Andrej Karpathy
        title="How I use LLMs",
        url="https://www.youtube.com/watch?v=EWvNQjAaOHw",
        published_at=datetime(2025, 2, 27, 22, 29, tzinfo=timezone.utc),
        description="Andrej Karpathy walks through how he uses LLMs day to day.",
    ),
]


if __name__ == "__main__":
    new_count = ArticleRepository().save_youtube_videos(SEED_VIDEOS)
    print(f"Seeded youtube_videos: {new_count} new of {len(SEED_VIDEOS)}")
