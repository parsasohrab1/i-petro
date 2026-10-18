"""Daily notification: Telegram bot message and/or an email to the owner's own inbox."""
import smtplib
from email.message import EmailMessage

import requests

from .config import env


def telegram(text, log):
    token, chat = env("TELEGRAM_BOT_TOKEN"), env("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return False
    for i in range(0, len(text), 3900):  # Telegram message limit is 4096 chars
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30,
                          json={"chat_id": chat, "text": text[i:i + 3900], "disable_web_page_preview": True})
        if not r.ok:
            log(f"Telegram failed: {r.status_code} {r.text[:200]}")
            return False
    return True


def email_self(subject, text, log):
    host, user, pwd, to = env("SMTP_HOST"), env("SMTP_USER"), env("SMTP_PASSWORD"), env("NOTIFY_EMAIL")
    if not (host and user and pwd and to):
        return False
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = user, to, subject
    msg.set_content(text)
    try:
        with smtplib.SMTP_SSL(host, int(env("SMTP_PORT", "465")), timeout=60) as s:
            s.login(user, pwd)
            s.send_message(msg)
        return True
    except Exception as exc:
        log(f"Notification email failed: {exc}")
        return False


def notify(subject, text, log):
    sent = [name for name, ok in (("telegram", telegram(text, log)), ("email", email_self(subject, text, log))) if ok]
    if not sent:
        log("No notification channel configured - summary printed only.")
    return sent
