"""iPetro server: PostgreSQL + REST API + session login + live updates, serving the unchanged dashboard.

The dashboard (platform/index.html) talks to `window.claude` (db, user, assets, downloads) that claude.ai provides.
shim.js implements the same interface against this API, so the page needs no change; sample (Claude scoring) is
intentionally absent here because api.anthropic.com is not reachable from Iranian servers.
"""
import asyncio
import json
import os
import re
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from psycopg.types.json import Jsonb

from . import db, rules, security

ROOT = Path(__file__).resolve().parent
PAGE = Path(os.environ.get("PLATFORM_HTML", ROOT.parent / "platform" / "index.html"))
COOKIE = "ppt_session"
SESSION_DAYS = int(os.environ.get("SESSION_DAYS", "14"))
SECURE = os.environ.get("COOKIE_SECURE", "1") != "0"        # set COOKIE_SECURE=0 only for plain-http testing
MAX_UPLOAD = int(os.environ.get("MAX_UPLOAD_MB", "20")) * 1024 * 1024
CSRF_HEADER = "x-requested-with"

_subs: set = set()
_loop = None


@asynccontextmanager
async def lifespan(app):
    global _loop
    _loop = asyncio.get_running_loop()
    db.init_schema()
    yield
    db.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


def publish(event: dict):
    """Called from worker threads after a write; wakes every open SSE stream."""
    if _loop is None:
        return
    msg = json.dumps(event)
    for q in list(_subs):
        _loop.call_soon_threadsafe(q.put_nowait, msg)


# ------------------------------------------------------------------ auth
_fails: dict = {}


def _throttled(key):
    now = time.time()
    hits = [t for t in _fails.get(key, []) if now - t < 600]
    _fails[key] = hits
    return len(hits) >= 5


def current_user(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "login required")
    with db.pool().connection() as c:
        row = c.execute(
            "SELECT u.id, u.email, u.name, u.role FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = %s AND s.expires > now() AND u.active", (security.token_hash(token),)).fetchone()
    if not row:
        raise HTTPException(401, "login required")
    return {"id": row[0], "email": row[1], "name": row[2], "role": row[3]}


def csrf(request: Request):
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get(CSRF_HEADER) != "ppt":
        raise HTTPException(403, "missing X-Requested-With")


@app.post("/api/login")
async def login(request: Request, response: Response):
    csrf(request)
    body = await request.json()
    email = str(body.get("email", "")).strip().lower()
    key = (request.client.host if request.client else "?", email)
    if _throttled(key):
        raise HTTPException(429, "too many attempts, try again in 10 minutes")
    with db.pool().connection() as c:
        row = c.execute("SELECT id, pw_hash FROM users WHERE lower(email) = %s AND active", (email,)).fetchone()
        ok = security.verify_password(str(body.get("password", "")), row[1] if row else security.hash_password("x"))
        if not (row and ok):
            _fails.setdefault(key, []).append(time.time())
            raise HTTPException(401, "wrong email or password")
        token = security.new_token()
        c.execute("INSERT INTO sessions (token_hash, user_id, expires) VALUES (%s, %s, %s)",
                  (security.token_hash(token), row[0], datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)))
        c.execute("DELETE FROM sessions WHERE expires < now()")
    _fails.pop(key, None)
    response.set_cookie(COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True, samesite="lax", secure=SECURE, path="/")
    return {"ok": True}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    csrf(request)
    token = request.cookies.get(COOKIE)
    if token:
        with db.pool().connection() as c:
            c.execute("DELETE FROM sessions WHERE token_hash = %s", (security.token_hash(token),))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return {"id": user["id"], "name": user["name"], "isOwner": user["role"] == "owner",
            "canEdit": user["role"] in ("owner", "admin"), "role": user["role"]}


# ------------------------------------------------------------------ documents
def _path(path: str, want_doc: bool):
    try:
        if rules.is_doc(path) != want_doc:
            raise ValueError
        return path.strip("/")
    except ValueError:
        raise HTTPException(400, "bad path")


@app.get("/api/doc")
def get_doc(path: str, user=Depends(current_user)):
    path = _path(path, True)
    with db.pool().connection() as c:
        row = c.execute("SELECT data FROM docs WHERE path = %s", (path,)).fetchone()
    if row is None:
        if not rules.can_read(user, path):
            raise HTTPException(403, "forbidden")
        return {"exists": False}
    if not rules.can_read(user, path, row[0]):
        raise HTTPException(403, "forbidden")
    return {"exists": True, "id": path.split("/")[-1], "data": row[0]}


@app.get("/api/col")
def get_col(path: str, user=Depends(current_user)):
    path = _path(path, False)
    with db.pool().connection() as c:
        rows = c.execute("SELECT id, data FROM docs WHERE parent = %s ORDER BY id", (path,)).fetchall()
    return {"docs": [{"id": i, "data": d} for i, d in rows if rules.can_read(user, f"{path}/{i}", d)]}


@app.put("/api/doc")
async def put_doc(request: Request, path: str, user=Depends(current_user)):
    csrf(request)
    path = _path(path, True)
    raw = await request.body()
    if len(raw) > rules.MAX_DOC_BYTES:
        raise HTTPException(413, "document too large")
    try:
        data = json.loads(raw)
        assert isinstance(data, dict)
    except Exception:
        raise HTTPException(400, "body must be a JSON object")
    with db.pool().connection() as c:
        old = c.execute("SELECT data FROM docs WHERE path = %s", (path,)).fetchone()
        if not rules.can_write(user, path, old[0] if old else None, data):
            raise HTTPException(403, "forbidden")
        c.execute("INSERT INTO docs (path, parent, id, data, updated_by) VALUES (%s, %s, %s, %s, %s) "
                  "ON CONFLICT (path) DO UPDATE SET data = EXCLUDED.data, updated = now(), updated_by = EXCLUDED.updated_by",
                  (path, rules.parent_of(path), path.split("/")[-1], Jsonb(data), user["id"]))
    publish({"path": path, "parent": rules.parent_of(path)})
    return {"ok": True}


@app.delete("/api/doc")
def delete_doc(request: Request, path: str, user=Depends(current_user)):
    csrf(request)
    path = _path(path, True)
    with db.pool().connection() as c:
        old = c.execute("SELECT data FROM docs WHERE path = %s", (path,)).fetchone()
        if old is None:
            return {"ok": True}
        if not rules.can_write(user, path, old[0], None):
            raise HTTPException(403, "forbidden")
        c.execute("DELETE FROM docs WHERE path = %s", (path,))
    publish({"path": path, "parent": rules.parent_of(path)})
    return {"ok": True}


@app.get("/api/events")
async def events(request: Request, user=Depends(current_user)):
    """Server-sent events: only {path, parent} of changed documents; clients refetch what they watch (so rules still apply)."""
    q: asyncio.Queue = asyncio.Queue()
    _subs.add(q)

    async def stream():
        try:
            yield "retry: 3000\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=20)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                if await request.is_disconnected():
                    break
        finally:
            _subs.discard(q)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ------------------------------------------------------------------ files
@app.post("/api/assets")
async def upload(request: Request, file: UploadFile = File(...), user=Depends(current_user)):
    csrf(request)
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "file too large")
    aid = secrets.token_hex(12)
    with db.pool().connection() as c:
        c.execute("INSERT INTO assets (id, name, mime, size, data, owner) VALUES (%s, %s, %s, %s, %s, %s)",
                  (aid, (file.filename or "")[:200], file.content_type or "application/octet-stream", len(data), data, user["id"]))
    return {"id": aid}


@app.get("/_blob/{aid}")
def blob(aid: str, user=Depends(current_user)):
    if not re.fullmatch(r"[0-9a-f]{24}", aid):
        raise HTTPException(404)
    with db.pool().connection() as c:
        row = c.execute("SELECT mime, data FROM assets WHERE id = %s", (aid,)).fetchone()
    if not row:
        raise HTTPException(404)
    # served as an attachment-safe type; never let an uploaded file run as HTML/JS in our origin
    mime = row[0] if row[0] and row[0].split(";")[0] in SAFE_MIME else "application/octet-stream"
    return Response(bytes(row[1]), media_type=mime, headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"})


SAFE_MIME = {"image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf", "text/plain", "application/json",
             "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"}


# ------------------------------------------------------------------ pages
@app.get("/healthz")
def healthz():
    with db.pool().connection() as c:
        c.execute("SELECT 1")
    return {"ok": True}


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return (ROOT / "login.html").read_text(encoding="utf-8")


@app.get("/shim.js")
def shim():
    return Response((ROOT / "shim.js").read_text(encoding="utf-8"), media_type="application/javascript",
                    headers={"Cache-Control": "no-cache"})


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    try:
        current_user(request)
    except HTTPException:
        return HTMLResponse(status_code=302, headers={"Location": "/login"})
    html = PAGE.read_text(encoding="utf-8")
    html = '<script src="/shim.js"></script>' + html      # the page is a fragment (no <head>); the shim must run first
    return HTMLResponse(html, headers={"Cache-Control": "no-store", "X-Frame-Options": "SAMEORIGIN",
                                       "Referrer-Policy": "same-origin",
                                       "Permissions-Policy": "geolocation=(self)"})
