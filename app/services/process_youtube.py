"""Stage 2 for YouTube: fetch transcripts for saved videos that don't have one yet.

If a transcript can't be fetched, the video is marked with TRANSCRIPT_UNAVAILABLE so it isn't retried every run.

Run:  uv run python -m app.services.process_youtube
"""

from app.database.models import TRANSCRIPT_UNAVAILABLE
from app.database.repository import ArticleRepository
from app.scrapers.youtube import YouTubeScraper


def process_youtube_transcripts() -> int:
    """Fill in `transcript` for every video where it's empty. Returns how many transcripts were found."""
    repo = ArticleRepository()
    scraper = YouTubeScraper()

    videos = repo.get_youtube_videos_without_transcript()
    processed = 0
    for video in videos:
        transcript = scraper.get_transcript(video.video_id)
        if transcript:
            repo.update_youtube_transcript(video.video_id, transcript.text)
            processed += 1
        else:
            repo.update_youtube_transcript(video.video_id, TRANSCRIPT_UNAVAILABLE)
            print(f"No transcript for: {video.title} ({video.url})")

    print(f"YouTube: added transcripts to {processed} of {len(videos)} video(s)")
    return processed


if __name__ == "__main__":
    process_youtube_transcripts()
