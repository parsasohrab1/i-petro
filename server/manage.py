"""Admin commands:  python -m server.manage <command>

  create-user --email a@b.c --name "Name" --role owner|admin|member [--id ID] [--password-stdin]
  set-password --email a@b.c [--password-stdin]
  list-users
  list-members                                 (member documents: id, name, email)
  import-backup ppt-backup-YYYY-MM-DD.json     (the backup file the dashboard's ERP -> backup page produces)
  import-export data/platform_export/manifest.json   (the folder written by `python -m agent export-platform`)
"""
import argparse
import getpass
import json
import re
import secrets
import sys
from pathlib import Path

from psycopg.types.json import Jsonb

from . import db, rules, security

# dashboard backup collection name -> Firestore-style collection path
BACKUP_PATHS = {
    "settings": "settings", "members": "members", "tasks": "tasks", "letters": "letters", "letters_archive": "letters_archive",
    "products": "products", "patents": "patents", "finance": "finance", "clients": "clients", "tracking": "tracking",
    "tenders": "market/data/tenders", "events": "market/data/events", "investors": "market/data/investors",
    "leads": "market/data/leads", "partners": "market/data/partners", "patent_ops": "patentops/data/items",
}


def _password(args, prompt="Password: "):
    if args.password_stdin:
        return sys.stdin.readline().rstrip("\n")
    pw = getpass.getpass(prompt)
    if pw != getpass.getpass("Repeat: "):
        sys.exit("passwords differ")
    return pw


def _check_password(pw):
    if len(pw) < 10:
        sys.exit("password must be at least 10 characters")


def _put(c, path, data, who="import"):
    rules.split(path)
    c.execute("INSERT INTO docs (path, parent, id, data, updated_by) VALUES (%s, %s, %s, %s, %s) "
              "ON CONFLICT (path) DO UPDATE SET data = EXCLUDED.data, updated = now(), updated_by = EXCLUDED.updated_by",
              (path, rules.parent_of(path), path.split("/")[-1], Jsonb(data), who))


def create_user(args):
    pw = _password(args)
    _check_password(pw)
    uid = args.id or re.sub(r"[^A-Za-z0-9_\-]", "", args.email.split("@")[0]) or "u" + secrets.token_hex(4)
    with db.pool().connection() as c:
        c.execute("INSERT INTO users (id, email, name, pw_hash, role) VALUES (%s, %s, %s, %s, %s)",
                  (uid, args.email.strip().lower(), args.name, security.hash_password(pw), args.role))
    print(f"created {args.role} {uid} <{args.email}>")


def set_password(args):
    pw = _password(args)
    _check_password(pw)
    with db.pool().connection() as c:
        n = c.execute("UPDATE users SET pw_hash = %s WHERE lower(email) = %s", (security.hash_password(pw), args.email.lower())).rowcount
        c.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE lower(email) = %s)", (args.email.lower(),))
    print("updated" if n else "no such user")


def list_users(_):
    with db.pool().connection() as c:
        for r in c.execute("SELECT id, email, name, role, active FROM users ORDER BY created"):
            print("\t".join(map(str, r)))


def list_members(_):
    """Imported members keep their old ids; create each login with --id set to that id so the rules match them."""
    with db.pool().connection() as c:
        for i, d in c.execute("SELECT id, data FROM docs WHERE parent = 'members' ORDER BY id"):
            print(f"{i}\t{d.get('full_name', '')}\t{d.get('email', '')}")


def import_backup(args):
    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    cols, n = data.get("collections", data), 0
    with db.pool().connection() as c:
        for name, rows in cols.items():
            if name == "settings":
                for row in rows:
                    _put(c, "settings/company", {k: v for k, v in row.items() if k != "id"}); n += 1
            elif name in ("reports", "attendance", "mindtest"):
                sub = {"reports": "items", "attendance": "days", "mindtest": "items"}[name]
                for row in rows:
                    member, rid = row.get("member"), row.get("id")
                    if member and rid:
                        _put(c, f"{name}/{member}/{sub}/{rid}", {k: v for k, v in row.items() if k not in ("member", "id")}); n += 1
            elif name in BACKUP_PATHS:
                for row in rows:
                    if row.get("id"):
                        _put(c, f"{BACKUP_PATHS[name]}/{row['id']}", {k: v for k, v in row.items() if k != "id"}); n += 1
            else:
                print("skipped unknown collection", name)
    print(f"imported {n} documents")


def import_export(args):
    manifest = Path(args.file)
    n = 0
    with db.pool().connection() as c:
        for batch in json.loads(manifest.read_text(encoding="utf-8"))["batches"]:
            for d in batch:
                fp = Path(d["file_path"])
                if not fp.exists():
                    fp = manifest.parent / d["collection"] / fp.name
                _put(c, f"{d['collection']}/{d['doc_id']}", json.loads(fp.read_text(encoding="utf-8"))); n += 1
    print(f"imported {n} documents")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="server.manage")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create-user"); p.add_argument("--email", required=True); p.add_argument("--name", default="")
    p.add_argument("--role", choices=["owner", "admin", "member"], required=True); p.add_argument("--id"); p.add_argument("--password-stdin", action="store_true"); p.set_defaults(f=create_user)
    p = sub.add_parser("set-password"); p.add_argument("--email", required=True); p.add_argument("--password-stdin", action="store_true"); p.set_defaults(f=set_password)
    sub.add_parser("list-users").set_defaults(f=list_users)
    sub.add_parser("list-members").set_defaults(f=list_members)
    p = sub.add_parser("import-backup"); p.add_argument("file"); p.set_defaults(f=import_backup)
    p = sub.add_parser("import-export"); p.add_argument("file"); p.set_defaults(f=import_export)
    args = ap.parse_args(argv)
    db.init_schema()
    args.f(args)
    db.close()


if __name__ == "__main__":
    main()
