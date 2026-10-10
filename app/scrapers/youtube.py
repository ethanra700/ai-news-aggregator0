"""Get the latest videos for a YouTube channel ID.

Transcripts are fetched separately by app/services/transcript.py.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser


@dataclass
class Video:
    video_id: str
    title: str
    url: str
    published_at: datetime
    transcript: str | None = None


def get_latest_videos(channel_id: str, hours: int = 24) -> list[Video]:
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    videos = []
    for entry in feed.entries:
        published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published_at >= cutoff and "/shorts/" not in entry.link:
            videos.append(Video(entry.yt_videoid, entry.title, entry.link, published_at))
    return videos


if __name__ == "__main__":
    videos = get_latest_videos(channel_id="UCn8ujwUInbJkBhffxqAPBVQ", hours = 200)
    
