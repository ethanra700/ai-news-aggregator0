# Architecture

## What this project is

An **AI news aggregator** that runs once a day and emails a personal digest of what happened in AI.

It collects new content from two kinds of sources:

- **YouTube channels**: the latest videos and their transcripts.
- **Blogs**: e.g. OpenAI and Anthropic news posts, as full article text.

Everything collected is saved in a **Postgres** database. Once a day, an **OpenAI** model summarizes each new item. It then writes a short digest, filtered and ranked by a "user profile" prompt that describes what you care about. Each entry is a short snippet with a link back to the original. The digest is **emailed** to your inbox.

The daily run is triggered by a **GitHub Actions** scheduled workflow against a hosted **Neon** Postgres database. For local development, Postgres runs in **Docker**.

## How a daily run works

```mermaid
flowchart LR
    A[Scrape sources<br/>YouTube + blogs] --> B[Save new items<br/>Postgres: articles]
    B --> C[Summarize each new item<br/>OpenAI]
    C --> D[Build digest from last 24h<br/>OpenAI + user profile prompt]
    D --> E[Email digest<br/>Resend]
    E --> F[Mark digest as sent<br/>Postgres: digests]
```

1. **Scrape**: for each source, fetch content published in the last 24 hours.
2. **Store**: insert it into `articles`. The URL is unique, so re-running never creates duplicates.
3. **Summarize**: every article without a summary gets a 2–3 sentence summary from OpenAI.
4. **Digest**: all of the day's summaries, plus the user profile prompt, go to OpenAI, which returns a structured list of `{title, snippet, url, source}`. That list is rendered to HTML and saved in `digests`.
5. **Email**: send the HTML to your inbox and record `sent_at`.

## File structure

Status: ✅ implemented · 🟡 partly done · 🔲 placeholder (not written yet)

```
ai-news-aggregator0/
├── main.py                       🔲 CLI entry point
├── pyproject.toml                ✅ project metadata + dependencies (uv)
├── uv.lock                       ✅ exact pinned versions (commit this)
├── .env.example                  ✅ template for required environment variables
├── .gitignore                    ✅ keeps .env and .venv out of git
├── readme.md                     🔲 quick-start for humans
├── ARCHITECTURE.md               ✅ this file
├── docker/
│   ├── docker-compose.yml        🔲 local Postgres database
│   └── Dockerfile                🔲 container for the app (optional)
├── .github/workflows/
│   └── daily-digest.yml          🔲 scheduled daily run
└── app/
    ├── __init__.py
    ├── models.py                 🔲 database tables (SQLAlchemy)
    ├── database.py               🔲 database connection + sessions
    ├── scrapers/
    │   ├── youtube.py            ✅ latest videos + transcripts per channel
    │   └── blog.py               🔲 latest blog posts + article text
    ├── services/
    │   ├── llm.py                🔲 OpenAI calls (summaries + digest)
    │   └── email.py              🔲 sends the digest email
    ├── agent/
    │   └── prompts.py            🔲 user profile + system prompts
    ├── digest.py                 🔲 builds the daily digest
    ├── config.py                 ✅ YouTube channels to monitor
    └── runner.py                 🟡 runs all scrapers (later: the whole pipeline)
```

### What goes in each file

#### Entry point

**`main.py`**: the command-line entry point. Planned commands:

| Command | Does |
|---|---|
| `init-db` | Creates the database tables (safe to run repeatedly) |
| `ingest` | Scrapes all sources and saves new articles |
| `summarize` | Summarizes articles that don't have a summary yet |
| `digest` | Builds today's digest (`--dry-run` writes HTML to a file instead of emailing) |
| `run` | All of the above, then sends the email; this is what the daily job calls |

#### `app/`: database

**`models.py`**: the SQLAlchemy table definitions:

| Table | Columns | Purpose |
|---|---|---|
| `sources` | `id`, `name`, `type` (`youtube` / `blog`), `url`, `feed_url`, `channel_id`, `is_active`, `created_at` | What to scrape |
| `articles` | `id`, `source_id` → sources, `title`, `url` (unique), `published_at`, `content`, `summary`, `created_at` | One row per video or blog post. `content` holds the transcript or article text |
| `digests` | `id`, `period_start`, `period_end`, `items` (JSON), `content_html`, `created_at`, `sent_at` | One row per daily email |

**`database.py`**: creates the SQLAlchemy engine from `DATABASE_URL` and provides a session factory. The same code works for local Docker Postgres and Neon; only the URL changes. It also has the function that creates the tables (`Base.metadata.create_all`).

#### `app/scrapers/`: collecting content

**`youtube.py`** ✅. Given a list of channel IDs (`UC...`), it returns each channel's videos from the last N hours, with transcripts.

- `CHANNEL_IDS`: the channels to follow.
- `get_latest_videos(channel_id, hours=24)`: tries the channel's RSS feed (`youtube.com/feeds/videos.xml?channel_id=...`). If the feed fails, it falls back to reading the channel's Videos page and each video's watch page for the exact publish date. Shorts are skipped.
- `get_transcript(video_id)`: the English transcript as plain text via `youtube-transcript-api`, or `None` if there isn't one.
- Run on its own to test: `uv run python -m app.scrapers.youtube`.

**`blog.py`** 🔲. Returns blog posts from the last N hours, with their full text.

- If the blog has an RSS feed (e.g. `openai.com/news/rss.xml`), read that.
- Otherwise (e.g. `anthropic.com/news`, which has no feed), fetch the listing page and pick out article links with BeautifulSoup.
- Fetch each post and extract clean body text with `trafilatura`.

Both scrapers should return the same shape of data (title, url, published_at, content), so the rest of the pipeline doesn't care where an item came from.

#### `app/services/`: external services

**`llm.py`**: all OpenAI calls.

- `summarize(article)`: a 2–3 sentence summary of one item. Long transcripts are truncated first to control cost.
- `build_digest(summaries, profile)`: uses OpenAI structured outputs to return a ranked, filtered list of `{title, snippet, url, source}` plus a short intro.
- The model name comes from configuration, so it can be changed without code edits.

**`email.py`**: sends the digest via Resend's free tier (3,000 emails/month). The default sender is `onboarding@resend.dev`, which can deliver to your own address without setting up a domain.

#### `app/agent/`: prompts

**`prompts.py`**: the text that steers the LLM.

- `USER_PROFILE`: who you are, which topics you care about, what to skip, and the tone you want. **This is the main thing to edit to personalize the digest.**
- System prompts for the per-item summary and the digest.

#### `app/`: orchestration

**`digest.py`**: selects articles published in the last 24 hours, calls `llm.build_digest`, renders the result to HTML and plain text, and saves a `digests` row.

**`config.py`**: `YOUTUBE_CHANNELS`, the list of channel IDs to monitor. OpenAI and Anthropic need no config (their feed URLs live in their scrapers).

**`runner.py`**: `run_scrapers(hours=24)` runs every scraper and returns a `ScrapeResults` model (`youtube`, `openai`, `anthropic` lists). It will grow into the full pipeline: scrape → store → summarize → digest → email.

#### Infrastructure

**`docker/docker-compose.yml`**: a single `postgres:16` container on port 5432 with a named volume, for local development. Start it with `docker compose -f docker/docker-compose.yml up -d`.

**`docker/Dockerfile`**: optional. Packages the app as a container. GitHub Actions doesn't need it.

**`.github/workflows/daily-digest.yml`**: runs every day at 06:00 UTC, and can also be started by hand from the Actions tab. Steps: check out the code → install uv → `uv sync` → `uv run python main.py run`. Secrets come from the repo's **Settings → Secrets**.

## Configuration

All settings come from environment variables: a local `.env` file (never committed), or GitHub secrets in production.

| Variable | Example | Used by |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/news` | database |
| `OPENAI_API_KEY` | `sk-...` | LLM |
| `OPENAI_MODEL` | `gpt-5-mini` | LLM (optional) |
| `RESEND_API_KEY` | `re_...` | email |
| `EMAIL_FROM` | `onboarding@resend.dev` | email |
| `EMAIL_TO` | your inbox | email |

For Neon, use its connection string with `?sslmode=require` on the end.

## Tech stack

| Concern | Choice |
|---|---|
| Language / deps | Python 3.12+, uv |
| Database | Postgres (Docker locally, Neon in production), SQLAlchemy 2 |
| Scraping | httpx, feedparser, BeautifulSoup, trafilatura, youtube-transcript-api |
| LLM | OpenAI (structured outputs) |
| Email | Resend |
| Scheduling | GitHub Actions cron |

## Running locally

```powershell
uv sync                                         # install dependencies
docker compose -f docker/docker-compose.yml up -d   # start Postgres (once written)
uv run python -m app.scrapers.youtube           # test the YouTube scraper
uv run python main.py run                       # full pipeline (once written)
```

## Build plan

Each step is built and tested before moving to the next. Tick a box when it's done.

- [x] **1. YouTube scraper** (`app/scrapers/youtube.py`)
  Latest videos per channel ID, filtered by time, with transcripts.
  *Test:* `uv run python -m app.scrapers.youtube` prints the last 24h of videos with transcript text.

- [ ] **2. Database + local Postgres** (`docker/docker-compose.yml`, `app/models.py`, `app/database.py`, `.env`)
  Postgres container; `sources`, `articles`, `digests` tables; engine/session from `DATABASE_URL`; a function that creates the tables.
  *Test:* `docker compose -f docker/docker-compose.yml up -d`, run the create-tables function, then `\dt` in `psql` shows all three tables.

- [ ] **3. Blog scraper** (`app/scrapers/blog.py`)
  OpenAI via RSS, Anthropic via the HTML listing page; full article text with trafilatura. Returns the same shape as the YouTube scraper.
  *Test:* `uv run python -m app.scrapers.blog` prints recent posts from both blogs with article text.

- [ ] **4. Save scraped items** (`app/runner.py` ingest step)
  Insert sources and articles into the database, skipping URLs that already exist.
  *Test:* run ingest twice; the `articles` table has rows from both scrapers and no duplicates.

- [ ] **5. OpenAI summaries** (`app/services/llm.py`, `app/agent/prompts.py`)
  `summarize()` for every article with no summary; long content is truncated first.
  *Test:* run summarize; `articles.summary` is filled in and reads well.

- [ ] **6. Daily digest** (`app/digest.py`, `USER_PROFILE` in `prompts.py`)
  Last 24h of summaries + user profile → structured OpenAI output → HTML, saved to `digests`.
  *Test:* `digest --dry-run` writes an HTML file; open it in a browser and check the items, links and ranking.

- [ ] **7. Email** (`app/services/email.py`)
  Send the digest through Resend and set `digests.sent_at`.
  *Test:* the email arrives in your inbox, and `sent_at` is set.

- [ ] **8. CLI + full pipeline** (`main.py`, `app/runner.py`)
  The `init-db`, `ingest`, `summarize`, `digest` and `run` commands; `run` does everything in order, and one failing source doesn't stop the rest.
  *Test:* `uv run python main.py run` from a fresh database ends with the email in your inbox; running it again adds no duplicates.

- [ ] **9. Production: Neon + GitHub Actions** (`.github/workflows/daily-digest.yml`)
  Create a free Neon database; add `DATABASE_URL`, `OPENAI_API_KEY`, `RESEND_API_KEY` and `EMAIL_TO` as repo secrets; daily cron at 06:00 UTC plus a manual "Run workflow" button.
  *Test:* start the workflow by hand from the Actions tab; the job goes green, the email arrives, and the rows appear in the Neon console. Check whether YouTube blocks transcripts from GitHub's servers; if it does, add a proxy.

- [ ] **10. Tests + readme** (`tests/`, `readme.md`)
  pytest tests for feed parsing (using saved sample XML) and digest HTML rendering; a quick-start section in the readme.
  *Test:* `uv run pytest` passes.

## Known issues and risks

- **The YouTube RSS feed is unreliable.** Since Oct 5, 2026 it has been returning 404 for every channel. The scraper falls back to reading the channel page, which costs more requests.
- **YouTube blocks transcript requests from cloud servers,** and from home IPs after many requests (`IpBlocked`). GitHub Actions runs on cloud IPs, so the scheduled job will probably need a proxy (e.g. Webshare, which the library supports) or the YouTube Data API.
- **openai.com sometimes shows bot challenges** (Cloudflare) to scrapers. Use the RSS feed where one exists.
- **Anthropic's news page has no RSS feed,** so its HTML scraper may break when the site's layout changes.
- **GitHub pauses scheduled workflows after 60 days with no repo activity.** Re-enable the workflow from the Actions tab.
