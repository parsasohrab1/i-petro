"""Data-request agent: datasets that Claude cannot reach (blocked hosts) become tasks for the active member.

The registry (`agent/data_registry.json`) lists every dataset the research code needs but the working environment cannot download
(the environment reaches only GitHub, PyPI, conda and a few cloud buckets). For each entry whose status is `blocked` the agent builds one
task document (`kind: data_download`, `venue` = the article id, `assignee` = the active member) with the download link, the expected files
and the exact destination path. `check_received` marks an entry `received` when its files are present, and the task is then ready to be
closed. Documents are exported under data/platform_export/tasks/ and applied with the ArtifactData tool using `set` WITHOUT `if_version`:
an existing task (possibly already edited by the member) is then refused instead of overwritten, so the export is create-only.
Files are uploaded by the member on the task itself in the platform (asset store); the agent's `destination` path is only the folder where Claude copies them in the product repository after reading them.
"""
import datetime
import json
import pathlib

from .config import DATA_DIR, ROOT

REGISTRY = pathlib.Path(__file__).with_name("data_registry.json")
EXPORT_DIR = DATA_DIR / "platform_export" / "tasks"
KIND = "data_download"


def load():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def destination(entry):
    """Relative path (inside the product's private repo, branch data-upload) where the files are to be placed."""
    base = "research/" + entry["module"] if entry["module"] != "src" else "data"
    return f"{base}/data_raw/"


def description(reg, entry):
    files = "\n".join(f"  - {f}" for f in entry["files"])
    return (f"دانلود داده‌ی «{entry['name']}» برای مقاله‌ی {entry['article']} (محصول {entry['product']}).\n\n"
            f"چرا تسک؟ Claude به این سایت دسترسی ندارد و بدون داده‌ی واقعی نمی‌تواند نتیجه را بازتولید کند.\n\n"
            f"۱) دانلود از: {entry['url']}\n   مجوز: {entry['license']}\n   فایل‌های موردنیاز:\n{files}\n\n"
            f"۲) آپلود: {reg['place_rule_fa']}\n\n"
            f"معیار پذیرش: همه‌ی فایل‌ها در همین تسک بارگذاری شده‌اند (نام و SHA256 هر فایل خودکار ثبت می‌شود) و تسک «انجام‌شده» شده است.")


def task_doc(reg, entry, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {"title": f"دانلود داده‌ها – {entry['name'].split('(')[0].strip()}", "desc": description(reg, entry), "type": "task", "points": None, "sprint": "",
            "priority": "high", "assignee": reg["assignee"], "team": "ai", "due": reg["due"], "blocked": False, "blocker_note": "", "status": "todo",
            "kind": KIND, "venue": entry["article"], "dataset": entry["id"], "created_by": reg["created_by"], "created": now, "updated": now}


def blocked(reg=None):
    reg = reg or load()
    return [e for e in reg["datasets"] if e["status"] == "blocked"]


def export(reg=None):
    """Write one JSON file per blocked dataset (doc id dr_<id>) and return the list of writes for ArtifactData."""
    reg = reg or load()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    writes = []
    for e in blocked(reg):
        p = EXPORT_DIR / f"dr_{e['id']}.json"
        p.write_text(json.dumps(task_doc(reg, e), ensure_ascii=False), encoding="utf-8")
        writes.append({"op": "set", "collection": "tasks", "doc_id": f"dr_{e['id']}", "file_path": str(p)})
    return writes


def check_received(entry, roots):
    """True when the destination folder exists under one of the roots and holds at least one non-empty file."""
    for r in roots:
        d = pathlib.Path(r) / entry["repo"] / destination(entry)
        if d.is_dir() and any(f.is_file() and f.stat().st_size > 0 for f in d.rglob("*")):
            return True
    return False


def refresh(reg=None, roots=()):
    """Mark entries `received` when their files are found; returns (reg, newly_received_ids)."""
    reg = reg or load()
    got = []
    for e in reg["datasets"]:
        if e["status"] == "blocked" and check_received(e, roots):
            e["status"] = "received"; got.append(e["id"])
    return reg, got


def notification_lines(reg=None):
    b = blocked(reg)
    return [f"📥 {len(b)} مجموعه‌داده منتظر دانلود دستی است (تسک «دانلود داده‌ها» برای {(reg or load())['assignee_name']})."] if b else []
