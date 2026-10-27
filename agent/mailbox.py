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
