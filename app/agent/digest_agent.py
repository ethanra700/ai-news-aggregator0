"""Digest agent: turns one article or video into a short digest entry (title + 2-3 sentence summary).

Uses the OpenAI Responses API with structured output: the reply is parsed straight into the DigestSummary model.

Usage:
    agent = DigestAgent()
    result = agent.summarize(title="...", content="...", source="youtube")
    result.title, result.summary
"""

from openai import OpenAI
from pydantic import BaseModel, Field

from app.agent.prompts import DIGEST_INSTRUCTIONS
from app.config import OPENAI_MODEL

# Long transcripts are cut to this many characters to keep each request cheap (~8k tokens).
MAX_CONTENT_CHARS = 30_000


class DigestSummary(BaseModel):
    """The structured output the model must return."""

    title: str = Field(description="Short, specific headline for the digest entry")
    summary: str = Field(description="2-3 sentence summary of the key point and why it matters")


class DigestAgent:
    def __init__(self, model: str = OPENAI_MODEL):
        self.client = OpenAI()  # reads OPENAI_API_KEY from the environment (.env)
        self.model = model

    def summarize(self, title: str, content: str, source: str) -> DigestSummary:
        response = self.client.responses.parse(
            model=self.model,
            instructions=DIGEST_INSTRUCTIONS,
            input=f"Source: {source}\nOriginal title: {title}\n\nContent:\n{content[:MAX_CONTENT_CHARS]}",
            text_format=DigestSummary,
        )
        return response.output_parsed


if __name__ == "__main__":
    agent = DigestAgent()
    result = agent.summarize(
        title="Introducing the Anthropic Cyber Mission",
        content="Anthropic announces a new program to help defenders use Claude for cybersecurity work.",
        source="anthropic",
    )
    print(result)
