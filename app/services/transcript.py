"""Get the transcript of a YouTube video as plain text."""

from youtube_transcript_api import YouTubeTranscriptApi, YouTubeTranscriptApiException


def get_transcript(video_id: str) -> str | None:
    """Return the video's English transcript, or None if it has none (or YouTube blocks the request)."""
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
    except YouTubeTranscriptApiException:
        return None
    return " ".join(snippet.text for snippet in transcript)


if __name__ == "__main__":
    transcript = get_transcript("1HtydHmdhrQ")
    print(transcript[:500] if transcript else "No transcript found")
