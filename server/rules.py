"""Access rules, the server-side counterpart of the Firestore rules the dashboard had on claude.ai.

Roles: owner (everything), admin (the dashboard's `canEdit`), member. Paths are Firestore-style:
a document has an even number of segments, a collection an odd number.

Default: every signed-in user reads and writes, except where listed below. Collection reads are filtered
document by document with `can_read`, so a collection query never leaks rows the user may not open.
"""
import re

SEG = re.compile(r"^[A-Za-z0-9_.:\-]{1,200}$")
MAX_DOC_BYTES = 1_000_000


def split(path: str):
    segs = [s for s in path.split("/") if s != ""]
    if not segs or not all(SEG.match(s) and set(s) != {"."} for s in segs):
        raise ValueError("bad path")
    return segs


def is_doc(path: str) -> bool:
    return len(split(path)) % 2 == 0


def parent_of(path: str) -> str:
    return "/".join(split(path)[:-1])


def _admin(u):
    return u["role"] in ("owner", "admin")


def _mine(data, uid):
    return bool(data) and (data.get("assignee") == uid or data.get("created_by") == uid)


def can_read(u, path: str, data=None) -> bool:
    s, uid = split(path), u["id"]
    top = s[0]
    if top in ("scholarships",) or (top == "settings" and len(s) > 1 and s[1] == "scholar"):
        return u["role"] == "owner"                                   # the owner's personal applications
    if top in ("finance", "clients"):
        return _admin(u)                                               # includes finance/_portal (submission-portal logins)
    if top in ("reports", "mindtest"):                                 # /<member>/items/*: the person and the owner only
        return len(s) < 2 or s[1] == uid or u["role"] == "owner"
    if top == "attendance":
        return len(s) < 2 or s[1] == uid or _admin(u)
    if top == "members":
        return _admin(u) or (len(s) > 1 and s[1] == uid)
    if top == "tasks":
        return _admin(u) or (len(s) > 1 and _mine(data, uid))
    return True


def can_write(u, path: str, old=None, new=None) -> bool:
    s, uid = split(path), u["id"]
    top = s[0]
    if top in ("scholarships",) or (top == "settings" and len(s) > 1 and s[1] == "scholar"):
        return u["role"] == "owner"
    if top in ("finance", "clients"):
        return _admin(u)
    if top in ("reports", "mindtest"):
        return len(s) > 1 and s[1] == uid                              # nobody edits another person's report or test
    if top == "attendance":
        return len(s) > 1 and (s[1] == uid or _admin(u))
    if top == "members":
        return _admin(u) or (len(s) > 1 and s[1] == uid)
    if top == "tasks":
        return _admin(u) or _mine(old, uid) or _mine(new, uid)
    if top == "settings":
        return _admin(u)
    return True
