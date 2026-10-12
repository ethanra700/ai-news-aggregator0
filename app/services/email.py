"""Email sending service (Gmail SMTP).

Needs GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env. EMAIL_TO is optional (defaults to GMAIL_ADDRESS).
"""

import smtplib
from email.message import EmailMessage

from app.config import EMAIL_TO, GMAIL_ADDRESS, GMAIL_APP_PASSWORD

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465  # SSL


def send_email(subject: str, html: str, text: str, to: str | None = None) -> None:
    """Send one email from your Gmail account, with an HTML version and a plain-text fallback."""
    recipient = to or EMAIL_TO
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not recipient:
        raise RuntimeError("Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD (and optionally EMAIL_TO) in .env to send email.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = recipient
    message.set_content(text)  # plain-text version
    message.add_alternative(html, subtype="html")  # HTML version, shown by most email apps

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(message)
