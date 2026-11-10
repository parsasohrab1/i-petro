"""Saves drafts into the parsaint.group mailbox (cPanel) over IMAP. Nothing is ever sent:
the user reviews each draft in parsaint.group/webmail and sends it personally."""
import imaplib
import re
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

from .config import env


def configured():
    return all(env(k) for k in ("IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"))


MIME_BY_EXT = {
    ".docx": "vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "vnd.openxmlformats-officedocument.presentationml.presentation",
    ".pdf": "pdf",
    ".xlsx": "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def build_message(sender, subject, body, to="", cc="", attachments=()):
    msg = EmailMessage()
    msg["From"] = sender
    if to:
        msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    msg.set_content(body)
    for path in attachments:
        path = Path(path)
        msg.add_attachment(path.read_bytes(), maintype="application",
                           subtype=MIME_BY_EXT.get(path.suffix.lower(), "octet-stream"), filename=path.name)
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


def check():
    """Verify the parsaint.group IMAP login (Outlook / webmail connection test). Returns the Drafts folder name."""
    if not configured():
        raise RuntimeError("Set IMAP_HOST, IMAP_USER and IMAP_PASSWORD in .env first (see .env.example).")
    host, port = env("IMAP_HOST"), int(env("IMAP_PORT", "993"))
    with imaplib.IMAP4_SSL(host, port) as imap:
        imap.login(env("IMAP_USER"), env("IMAP_PASSWORD"))
        status, _ = imap.select("INBOX", readonly=True)
        if status != "OK":
            raise RuntimeError("IMAP INBOX select failed")
        return env("IMAP_USER")


def drafts_from_eml(source):
    """Yields (name, EmailMessage) for every .eml in a folder or a .zip (e.g. the ZIP the partners tab downloads)."""
    import zipfile
    from email import message_from_bytes, policy
    from pathlib import Path
    source = Path(source)
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as z:
            items = [(n, z.read(n)) for n in sorted(z.namelist()) if n.lower().endswith(".eml")]
    else:
        items = [(f.name, f.read_bytes()) for f in sorted(source.glob("*.eml"))] if source.is_dir() else [(source.name, source.read_bytes())]
    for name, raw in items:
        msg = message_from_bytes(raw, policy=policy.SMTP)
        if not msg["Date"]:
            msg["Date"] = formatdate(localtime=True)
        if not msg["Message-ID"]:
            msg["Message-ID"] = make_msgid(domain=(env("IMAP_USER") or "parsaint.group").split("@")[-1])
        yield name, msg
