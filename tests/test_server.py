"""Server tests need PostgreSQL: set TEST_DATABASE_URL (CI does), otherwise they are skipped."""
import json
import os

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("psycopg_pool")
URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")

H = {"X-Requested-With": "ppt"}


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    os.environ["DATABASE_URL"] = URL
    os.environ["COOKIE_SECURE"] = "0"
    from server import db, manage
    db.close()
    db.init_schema()
    with db.pool().connection() as c:
        c.execute("TRUNCATE users, sessions, docs, assets CASCADE")
    for uid, role in (("boss", "owner"), ("adm", "admin"), ("ann", "member"), ("bob", "member")):
        from server import security
        with db.pool().connection() as c:
            c.execute("INSERT INTO users (id, email, name, pw_hash, role) VALUES (%s,%s,%s,%s,%s)",
                      (uid, f"{uid}@x.io", uid, security.hash_password("correct-horse-1"), role))
    from fastapi.testclient import TestClient
    from server.app import app
    with TestClient(app) as c:
        yield c
    db.close()


def client_as(env, uid):
    from fastapi.testclient import TestClient
    from server.app import app
    c = TestClient(app)
    r = c.post("/api/login", json={"email": f"{uid}@x.io", "password": "correct-horse-1"}, headers=H)
    assert r.status_code == 200, r.text
    c.__enter__()
    return c


def test_login_required_and_wrong_password(env):
    from fastapi.testclient import TestClient
    from server.app import app
    anon = TestClient(app)
    assert anon.get("/api/me").status_code == 401
    assert anon.get("/api/col", params={"path": "tasks"}).status_code == 401
    assert anon.post("/api/login", json={"email": "ann@x.io", "password": "nope"}, headers=H).status_code == 401
    assert anon.get("/", follow_redirects=False).status_code == 302


def test_csrf_header_required_for_writes(env):
    ann = client_as(env, "ann")
    assert ann.put("/api/doc", params={"path": "reports/ann/items/2026-10-01"}, json={"text": "x"}).status_code == 403
    assert ann.put("/api/doc", params={"path": "reports/ann/items/2026-10-01"}, json={"text": "x"}, headers=H).status_code == 200


def test_me_roles(env):
    assert client_as(env, "boss").get("/api/me").json()["isOwner"] is True
    adm = client_as(env, "adm").get("/api/me").json()
    assert adm["canEdit"] and not adm["isOwner"]
    assert not client_as(env, "ann").get("/api/me").json()["canEdit"]


def test_reports_and_mindtest_are_private_to_person_and_owner(env):
    ann, bob, boss, adm = (client_as(env, u) for u in ("ann", "bob", "boss", "adm"))
    for p in ("reports/ann/items/d1", "mindtest/ann/items/result"):
        assert ann.put("/api/doc", params={"path": p}, json={"v": 1}, headers=H).status_code == 200
        assert ann.get("/api/doc", params={"path": p}).json()["exists"]
        assert boss.get("/api/doc", params={"path": p}).json()["exists"]
        assert bob.get("/api/doc", params={"path": p}).status_code == 403
        assert adm.get("/api/doc", params={"path": p}).status_code == 403           # admins are not the owner
        assert bob.put("/api/doc", params={"path": p}, json={"v": 2}, headers=H).status_code == 403
        assert boss.put("/api/doc", params={"path": p}, json={"v": 2}, headers=H).status_code == 403


def test_tasks_are_filtered_per_member(env):
    adm, ann, bob = (client_as(env, u) for u in ("adm", "ann", "bob"))
    adm.put("/api/doc", params={"path": "tasks/t1"}, json={"assignee": "ann", "created_by": "adm"}, headers=H)
    adm.put("/api/doc", params={"path": "tasks/t2"}, json={"assignee": "bob", "created_by": "adm"}, headers=H)
    ids = lambda c: [d["id"] for d in c.get("/api/col", params={"path": "tasks"}).json()["docs"]]
    assert ids(ann) == ["t1"] and ids(bob) == ["t2"] and set(ids(adm)) == {"t1", "t2"}
    assert ann.get("/api/doc", params={"path": "tasks/t2"}).status_code == 403
    assert ann.put("/api/doc", params={"path": "tasks/t2"}, json={"assignee": "bob"}, headers=H).status_code == 403


def test_members_finance_scholarship_rules(env):
    boss, adm, ann = (client_as(env, u) for u in ("boss", "adm", "ann"))
    adm.put("/api/doc", params={"path": "members/bob"}, json={"full_name": "Bob"}, headers=H)
    assert ann.get("/api/doc", params={"path": "members/bob"}).status_code == 403
    assert ann.get("/api/col", params={"path": "members"}).json()["docs"] == []
    assert ann.put("/api/doc", params={"path": "members/ann"}, json={"full_name": "Ann"}, headers=H).status_code == 200
    assert adm.put("/api/doc", params={"path": "finance/f1"}, json={"a": 1}, headers=H).status_code == 200
    assert ann.get("/api/doc", params={"path": "finance/f1"}).status_code == 403
    assert boss.put("/api/doc", params={"path": "settings/scholar"}, json={"x": 1}, headers=H).status_code == 200
    assert adm.get("/api/doc", params={"path": "settings/scholar"}).status_code == 403
    assert ann.put("/api/doc", params={"path": "settings/company"}, json={"x": 1}, headers=H).status_code == 403
    assert adm.put("/api/doc", params={"path": "settings/company"}, json={"x": 1}, headers=H).status_code == 200


def test_attendance_admin_can_close_exit(env):
    ann, adm, bob = (client_as(env, u) for u in ("ann", "adm", "bob"))
    assert ann.put("/api/doc", params={"path": "attendance/ann/days/2026-10-30"}, json={"in": "09:00"}, headers=H).status_code == 200
    assert adm.put("/api/doc", params={"path": "attendance/ann/days/2026-10-30"}, json={"in": "09:00", "out": "17:00"}, headers=H).status_code == 200
    assert bob.get("/api/doc", params={"path": "attendance/ann/days/2026-10-30"}).status_code == 403


def test_path_validation_and_doc_vs_collection(env):
    ann = client_as(env, "ann")
    assert ann.get("/api/doc", params={"path": "tasks"}).status_code == 400            # a collection is not a document
    assert ann.get("/api/col", params={"path": "tasks/t1"}).status_code == 400
    assert ann.get("/api/doc", params={"path": "tasks/../members/x"}).status_code == 400
    assert ann.put("/api/doc", params={"path": "market/data/x"}, content="[1]", headers=H).status_code in (400, 422)


def test_delete_and_overwrite(env):
    adm = client_as(env, "adm")
    adm.put("/api/doc", params={"path": "products/p1"}, json={"n": 1}, headers=H)
    adm.put("/api/doc", params={"path": "products/p1"}, json={"n": 2}, headers=H)
    assert adm.get("/api/doc", params={"path": "products/p1"}).json()["data"] == {"n": 2}
    assert adm.delete("/api/doc", params={"path": "products/p1"}, headers=H).status_code == 200
    assert adm.get("/api/doc", params={"path": "products/p1"}).json() == {"exists": False}


def test_assets_roundtrip_and_unsafe_type_downgraded(env):
    ann = client_as(env, "ann")
    r = ann.post("/api/assets", files={"file": ("sig.png", b"\x89PNG-bytes", "image/png")}, headers=H)
    aid = r.json()["id"]
    got = ann.get(f"/_blob/{aid}")
    assert got.content == b"\x89PNG-bytes" and got.headers["content-type"] == "image/png"
    r = ann.post("/api/assets", files={"file": ("x.html", b"<script>alert(1)</script>", "text/html")}, headers=H)
    got = ann.get(f"/_blob/{r.json()['id']}")
    assert got.headers["content-type"] == "application/octet-stream"
    from fastapi.testclient import TestClient
    from server.app import app
    assert TestClient(app).get(f"/_blob/{aid}").status_code == 401


def test_index_is_served_with_shim_after_login(env):
    r = client_as(env, "ann").get("/")
    assert r.status_code == 200 and r.text.startswith('<script src="/shim.js"></script>')
    assert "window.claude" in client_as(env, "ann").get("/shim.js").text


def test_import_backup_maps_collections(env, tmp_path):
    from server import manage
    f = tmp_path / "b.json"
    f.write_text(json.dumps({"collections": {
        "members": [{"id": "carl", "full_name": "Carl"}],
        "reports": [{"member": "carl", "id": "2026-10-01", "text": "t"}],
        "tenders": [{"id": "T1", "title": "x"}],
        "settings": [{"name_fa": "ش"}]}}), encoding="utf-8")
    manage.main(["import-backup", str(f)])
    boss = client_as(env, "boss")
    assert boss.get("/api/doc", params={"path": "members/carl"}).json()["data"] == {"full_name": "Carl"}
    assert boss.get("/api/doc", params={"path": "reports/carl/items/2026-10-01"}).json()["data"] == {"text": "t"}
    assert boss.get("/api/doc", params={"path": "market/data/tenders/T1"}).json()["exists"]
    assert boss.get("/api/doc", params={"path": "settings/company"}).json()["data"] == {"name_fa": "ش"}
