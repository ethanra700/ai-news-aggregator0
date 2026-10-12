"""App settings and what to monitor. Edit this file to add or remove sources."""

import os

from dotenv import load_dotenv

load_dotenv()  # reads variables from the .env file in the project root, if there is one

# Defaults to the local Docker database (docker/docker-compose.yml). Set DATABASE_URL in .env to use another one.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://ai_news:ai_news_password@localhost:5433/ai_news")

# OpenAI model used to write the digest summaries. OPENAI_API_KEY must be set in .env (the OpenAI client reads it).
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# YouTube channel IDs (start with "UC"). Find one on the channel page: About -> Share channel -> Copy channel ID.
YOUTUBE_CHANNELS = [
    "UCn8ujwUInbJkBhffxqAPBVQ",  # Dave Ebbelaar
    "UCXZCJLdBC09xxGZ6gcdrc6A",  # OpenAI
    "UCrDwWp7EBBv4NwvScIpBDOA",  # Anthropic
    "UCNJ1Ymd5yFuUPtn21xtRbbw",  # AI Explained
    "UCbfYPyITQ-7l4upoX8nvctg",  # Two Minute Papers
    "UCXUPKJO5MZQN11PqgIvyuvQ",  # Andrej Karpathy
]

