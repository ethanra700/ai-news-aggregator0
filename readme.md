# Personal AI News Agent

An automated pipeline that scrapes AI news from YouTube and AI lab blogs, uses LLM agents to summarize and rank it against my interests, and emails me a personalized daily briefing.

<img width="1298" height="455" alt="diagram" src="https://github.com/user-attachments/assets/547223e4-d692-4672-ab62-3163ab505321" />


## How It Works

1. **Scrape:** Pulls new content from the last 24 hours via RSS feeds for YouTube channels, the OpenAI blog, and the Anthropic blog.
2. **Extract:** Fetches YouTube transcripts and converts blog pages from HTML to Markdown.
3. **Store:** Saves raw content in a Neon serverless PostgreSQL database using SQLAlchemy.
4. **Digest Agent:** Uses GPT-4o-mini to generate a short summary of each new article or video.
5. **Curator Agent:** Ranks the day's digests against a user profile and selects the top 10.
6. **Email Agent:** Writes an introduction and formats the top stories into an HTML email.
7. **Deliver:** Sends the briefing to my inbox through Gmail SMTP.

The full pipeline runs once a day on a GitHub Actions cron schedule.

## Tech Stack

- **Language:** Python
- **LLM:** OpenAI API (GPT-4o-mini, Responses API with structured outputs)
- **Database:** Neon PostgreSQL, SQLAlchemy
- **Scraping:** Feedparser, YouTube Transcript API, HTML-to-Markdown
- **Automation:** GitHub Actions
- **Tooling:** uv, Pydantic, Docker (local Postgres)

## Setup

1. Clone the repo and install dependencies:
```bash
   uv sync
```
2. Copy `.env.example` to `.env` and fill in:
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (Neon connection string)
   - `MY_EMAIL` and `APP_PASSWORD` (Gmail app password)
3. Edit your interests in the user profile file.
4. Run the pipeline locally:
```bash
   uv run main.py
```
5. To automate it, add the same variables as GitHub repository secrets. The workflow in `.github/workflows/` runs it daily.
