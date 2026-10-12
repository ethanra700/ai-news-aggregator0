"""Email agent: turns the curator's ranked digests into a ready-to-send daily email.

The LLM writes only the subject line and the intro (Responses API + structured output).
The list of articles is then laid out in Python, so links and order are always exactly right.

Usage:
    email = EmailAgent().create_email(ranked_digests)   # DigestEmail(subject, html, text)
"""

from datetime import date
from html import escape

from openai import OpenAI
from pydantic import BaseModel, Field

from app.agent.curator_agent import RankedDigest
from app.agent.prompts import EMAIL_INSTRUCTIONS
from app.config import OPENAI_MODEL
from app.user_profile import USER_NAME

SOURCE_LABELS = {"youtube": "YouTube", "openai": "OpenAI", "anthropic": "Anthropic"}


class EmailIntro(BaseModel):
    """The structured output the model must return."""

    subject: str = Field(description="Short email subject line naming the 1-2 biggest stories")
    intro: str = Field(description="3-4 sentence opening paragraph that previews the top stories")


class DigestEmail(BaseModel):
    """The finished email, ready to send."""

    subject: str
    html: str
    text: str


class EmailAgent:
    def __init__(self, model: str = OPENAI_MODEL, name: str = USER_NAME):
        self.client = OpenAI()  # reads OPENAI_API_KEY from the environment (.env)
        self.model = model
        self.name = name

    def write_intro(self, digests: list[RankedDigest], today: str) -> EmailIntro:
        stories = "\n".join(f"{d.rank}. {d.title}: {d.summary}" for d in digests)
        response = self.client.responses.parse(
            model=self.model,
            instructions=EMAIL_INSTRUCTIONS.format(name=self.name, date=today),
            input=f"Reader's name: {self.name}\nToday's date: {today}\n\nToday's ranked stories:\n{stories}",
            text_format=EmailIntro,
        )
        return response.output_parsed

    def create_email(self, digests: list[RankedDigest], today: date | None = None) -> DigestEmail:
        """Build the full email from the ranked digests (already sorted, best first)."""
        today_text = (today or date.today()).strftime("%B %d, %Y")  # e.g. "October 12, 2026"
        intro = self.write_intro(digests, today_text)
        return DigestEmail(
            subject=intro.subject,
            html=render_html(intro.intro, digests),
            text=render_text(intro.intro, digests),
        )


def render_html(intro: str, digests: list[RankedDigest]) -> str:
    items = "".join(
        f"""
        <div style="margin: 0 0 24px 0;">
          <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.04em;">
            #{d.rank} &middot; {escape(SOURCE_LABELS.get(d.article_type, d.article_type))}
          </div>
          <a href="{escape(d.url)}" style="font-size: 17px; font-weight: 600; color: #111827; text-decoration: none;">
            {escape(d.title)}
          </a>
          <p style="margin: 6px 0 0 0; font-size: 15px; line-height: 1.5; color: #374151;">{escape(d.summary)}</p>
          <a href="{escape(d.url)}" style="font-size: 14px; color: #2563eb;">Read more &rarr;</a>
        </div>"""
        for d in digests
    )
    return f"""\
<div style="max-width: 600px; margin: 0 auto; padding: 24px; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;">
  <p style="font-size: 16px; line-height: 1.6; color: #111827; margin: 0 0 28px 0;">{escape(intro)}</p>
  {items}
  <p style="font-size: 12px; color: #9ca3af; margin-top: 32px;">Curated for you by your AI news aggregator.</p>
</div>"""


def render_text(intro: str, digests: list[RankedDigest]) -> str:
    """Plain-text version, shown by email apps that don't display HTML."""
    items = "\n\n".join(
        f"{d.rank}. {d.title} ({SOURCE_LABELS.get(d.article_type, d.article_type)})\n{d.summary}\n{d.url}"
        for d in digests
    )
    return f"{intro}\n\n{items}\n"
