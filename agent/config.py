"""Configuration and paths. Secrets come only from environment variables (or a local .env)."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"


def _load_dotenv():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def load_config():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def load_products():
    return json.loads((ROOT / "products.json").read_text(encoding="utf-8"))["products"]


def env(name, default=None):
    value = os.environ.get(name, default)
    return value if value not in ("", None) else default
