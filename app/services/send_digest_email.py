"""Stage 5: build the daily email from the top-ranked digests and send it.

Run:  uv run python -m app.services.send_digest_email            (build + send)
      uv run python -m app.services.send_digest_email --preview  (build only, saves digest_preview.html)
"""

import sys
from pathlib import Path

from app.agent.email_agent import DigestEmail, EmailAgent
from app.services.curate_digests import curate_digests
from app.services.email import send_email

TOP_N = 10
PREVIEW_FILE = Path("digest_preview.html")


def send_digest_email(hours: int = 24, preview: bool = False) -> DigestEmail | None:
    """Rank the last `hours` of digests, write the email for the top 10, and send it (or save a preview)."""
    ranked = curate_digests(hours)
    if not ranked:
        print("Nothing to email.")
        return None

    email = EmailAgent().create_email(ranked[:TOP_N])
    print(f"\nSubject: {email.subject}")

    if preview:
        PREVIEW_FILE.write_text(email.html, encoding="utf-8")
        print(f"Preview saved to {PREVIEW_FILE.resolve()} (open it in your browser). Not sent.")
    else:
        send_email(email.subject, email.html, email.text)
        print("Email sent.")
    return email


if __name__ == "__main__":
    send_digest_email(hours=24, preview="--preview" in sys.argv)
