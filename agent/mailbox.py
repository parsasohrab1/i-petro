"""Saves drafts into the parsaint.group mailbox (cPanel) over IMAP. Nothing is ever sent:
the user reviews each draft in parsaint.group/webmail and sends it personally."""
import imaplib
import re
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from .config import env


def configured():
    return all(env(k) for k in ("IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"))


def build_message(sender, subject, body, to="", attachments=()):
    msg = EmailMessage()
    msg["From"] = sender
    if to:
        msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    msg.set_content(body)
    for path in attachments:
        msg.add_attachment(path.read_bytes(), maintype="application",
                           subtype="vnd.openxmlformats-officedocument.wordprocessingml.document", filename=path.name)
    return msg


def _drafts_folder(imap, candidates):
    status, folders = imap.list()
    names = []
    for raw in folders or []:
        line = raw.decode(errors="ignore")
        name = re.findall(r'"([^"]+)"\s*$', line) or line.rsplit(" ", 1)[-1:]
        if "\\Drafts" in line:
            return name[0]
        names.append(name[0])
    for c in candidates:
        if c in names:
            return c
    return candidates[0]


def save_draft(msg, cfg):
    host, port = env("IMAP_HOST"), int(env("IMAP_PORT", "993"))
    with imaplib.IMAP4_SSL(host, port) as imap:
        imap.login(env("IMAP_USER"), env("IMAP_PASSWORD"))
        folder = _drafts_folder(imap, cfg["mail"]["drafts_folder_candidates"])
        status, _ = imap.append(f'"{folder}"', "(\\Draft \\Seen)", imaplib.Time2Internaldate(time.time()),
                                msg.as_bytes())
        if status != "OK":
            raise RuntimeError(f"IMAP APPEND to {folder} failed: {status}")
        return folder
