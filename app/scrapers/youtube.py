"""Get the latest videos (+ transcripts) from a list of YouTube channel IDs.

Uses the channel RSS feed, and falls back to scraping the channel page when
the feed is down (it currently returns 404 for every channel).

Test:  uv run python -m app.scrapers.youtube
"""

import html
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
from youtube_transcript_api import YouTubeTranscriptApi, YouTubeTranscriptApiException

# Channel IDs start with "UC" (find one at youtube.com/account_advanced or in the channel's "Share channel" link).
CHANNEL_IDS = [
    "UCrDwWp7EBBv4NwvScIpBDOA",  # Anthropic
    "UCXZCJLdBC09xxGZ6gcdrc6A",  # OpenAI
    "UCXUPKJO5MZQN11PqgIvyuvQ",  # Andrej Karpathy
    "UCNJ1Ymd5yFuUPtn21xtRbbw",  # AI Explained
    "UCbfYPyITQ-7l4upoX8nvctg",  # Two Minute Papers
]

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en"}
COOKIES = {"SOCS": "CAI"}  # skips YouTube's cookie-consent page


@dataclass
class Video:
    video_id: str
    title: str
    url: str
    published_at: datetime
    transcript: str | None = None


def get(url: str) -> httpx.Response:
    response = httpx.get(url, headers=HEADERS, cookies=COOKIES, follow_redirects=True, timeout=15)
    response.raise_for_status()
    return response


def get_videos_from_rss(channel_id: str) -> list[Video]:
    feed = feedparser.parse(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}").content)
    return [
        Video(
            video_id=entry.yt_videoid,
            title=entry.title,
            url=entry.link,
            published_at=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc),
        )
        for entry in feed.entries
        if "/shorts/" not in entry.link
    ]


def get_videos_from_page(channel_id: str, limit: int = 10) -> list[Video]:
    page = get(f"https://www.youtube.com/channel/{channel_id}/videos").text
    video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([\w-]{11})"', page)))[:limit]

    videos = []
    for video_id in video_ids:
        url = f"https://www.youtube.com/watch?v={video_id}"
        watch_page = get(url).text
        title = re.search(r'<meta name="title" content="([^"]*)"', watch_page).group(1)
        published = re.search(r'"publishDate":"([^"]+)"', watch_page).group(1)
        videos.append(
            Video(
                video_id=video_id,
                title=html.unescape(title),
                url=url,
                published_at=datetime.fromisoformat(published).astimezone(timezone.utc),
            )
        )
    return videos


def get_latest_videos(channel_id: str, hours: int = 24) -> list[Video]:
    try:
        videos = get_videos_from_rss(channel_id)
    except httpx.HTTPError:
        videos = get_videos_from_page(channel_id)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return [video for video in videos if video.published_at >= cutoff]


def get_transcript(video_id: str) -> str | None:
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
    except YouTubeTranscriptApiException:
        return None
    return " ".join(" ".join(snippet.text for snippet in transcript).split())


if __name__ == "__main__":
    for channel_id in CHANNEL_IDS:
        for video in get_latest_videos(channel_id, hours=24):
            video.transcript = get_transcript(video.video_id)
            print(f"\n{video.title}\n  {video.url}\n  published: {video.published_at:%Y-%m-%d %H:%M} UTC")
            print(f"  transcript: {video.transcript[:200] + '...' if video.transcript else None}")
