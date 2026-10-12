"""Curator agent: ranks digest entries by how relevant they are to the user profile.

All digests are sent in ONE request, so the model can compare them against each other.
Uses the OpenAI Responses API with structured output (same setup as the digest agent).

Usage:
    agent = CuratorAgent()
    ranked = agent.rank(digests)   # list[RankedDigest], best first
"""

from openai import OpenAI
from pydantic import BaseModel, Field

from app.agent.prompts import CURATOR_INSTRUCTIONS
from app.config import OPENAI_MODEL
from app.database.models import Digest
from app.user_profile import USER_PROFILE


# --- Structured output: what the model must return ---


class DigestScore(BaseModel):
    digest_id: str = Field(description="The digest's id, copied exactly from the input")
    # Reasoning comes before the score so the model explains first, then decides (gives better scores).
    reasoning: str = Field(description="One sentence explaining the score in terms of the reader's interests")
    relevance_score: int = Field(description="Integer from 1 (irrelevant) to 10 (must read)")


class CuratorOutput(BaseModel):
    scores: list[DigestScore] = Field(description="One score for every digest entry in the input")


# --- What the rest of the app gets back ---


class RankedDigest(BaseModel):
    rank: int  # 1 = most relevant
    relevance_score: int  # 1-10
    reasoning: str
    digest_id: str
    article_type: str
    title: str
    summary: str
    url: str


class CuratorAgent:
    def __init__(self, model: str = OPENAI_MODEL, user_profile: str = USER_PROFILE):
        self.client = OpenAI()  # reads OPENAI_API_KEY from the environment (.env)
        self.model = model
        self.instructions = CURATOR_INSTRUCTIONS.format(user_profile=user_profile)

    def rank(self, digests: list[Digest]) -> list[RankedDigest]:
        """Score every digest against the user profile and return them sorted, most relevant first."""
        if not digests:
            return []

        entries = "\n\n".join(
            f"digest_id: {d.id}\nsource: {d.article_type}\ntitle: {d.title}\nsummary: {d.summary}" for d in digests
        )
        response = self.client.responses.parse(
            model=self.model,
            instructions=self.instructions,
            input=f"Rank these {len(digests)} digest entries:\n\n{entries}",
            text_format=CuratorOutput,
        )
        scores = {score.digest_id: score for score in response.output_parsed.scores}

        # Build the result from OUR digests, not the model's list: ignores any made-up ids,
        # and an entry the model skipped still appears (at the bottom, score 0).
        results = []
        for digest in digests:
            score = scores.get(digest.id)
            results.append(
                {
                    "relevance_score": max(1, min(10, score.relevance_score)) if score else 0,
                    "reasoning": score.reasoning if score else "Not scored by the model.",
                    "digest_id": digest.id,
                    "article_type": digest.article_type,
                    "title": digest.title,
                    "summary": digest.summary,
                    "url": digest.url,
                }
            )
        results.sort(key=lambda result: result["relevance_score"], reverse=True)
        return [RankedDigest(rank=position, **result) for position, result in enumerate(results, start=1)]
