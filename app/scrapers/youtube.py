"""YouTube scraper: latest videos for a channel ID, with transcripts.

Usage:
    scraper = YouTubeScraper()
    videos = scraper.scrape_channel("UCn8ujwUInbJkBhffxqAPBVQ", hours=24)
"""

from datetime import datetime, timedelta, timezone

import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, YouTubeTranscriptApiException

FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


class Transcript(BaseModel):
    text: str


class ChannelVideo(BaseModel):
    video_id: str
    title: str
    url: str
    published_at: datetime
    transcript: Transcript | None = None


class YouTubeScraper:
    def __init__(self, languages: tuple[str, ...] = ("en",)):
        self.languages = languages
        self.transcript_api = YouTubeTranscriptApi()

    def get_latest_videos(self, channel_id: str, hours: int = 24) -> list[ChannelVideo]:
        """Videos from the channel's RSS feed published in the last `hours` (Shorts skipped)."""
        feed = feedparser.parse(FEED_URL.format(channel_id=channel_id))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        videos = []
        for entry in feed.entries:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_at >= cutoff and "/shorts/" not in entry.link:
                videos.append(
                    ChannelVideo(
                        video_id=entry.yt_videoid,
                        title=entry.title,
                        url=entry.link,
                        published_at=published_at,
                    )
                )
        return videos

    def get_transcript(self, video_id: str) -> Transcript | None:
        """The video's transcript, or None if it has none (or YouTube blocks the request)."""
        try:
            transcript = self.transcript_api.fetch(video_id, languages=self.languages)
        except YouTubeTranscriptApiException:
            return None
        return Transcript(text=" ".join(snippet.text for snippet in transcript))

    def scrape_channel(self, channel_id: str, hours: int = 24) -> list[ChannelVideo]:
        """Latest videos for the channel, each with its transcript filled in."""
        videos = self.get_latest_videos(channel_id, hours)
        for video in videos:
            video.transcript = self.get_transcript(video.video_id)
        return videos


if __name__ == "__main__":
    scraper = YouTubeScraper()
    videos = scraper.scrape_channel("UCn8ujwUInbJkBhffxqAPBVQ", hours=200)
