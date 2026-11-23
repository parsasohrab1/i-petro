"""Claude scoring for the self-hosted dashboard (the `sample` service the page uses for task checks and report grading).

Needs ANTHROPIC_API_KEY. api.anthropic.com is often unreachable from Iranian servers: set ANTHROPIC_BASE_URL to a relay
you control (any server that forwards /v1/messages) or put the whole server behind an outbound proxy (HTTPS_PROXY).
Without a key the feature stays off and the dashboard behaves as before.
"""
import json
import os
import urllib.request

KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
BASE = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
MODELS = {"quick": os.environ.get("SAMPLE_MODEL_QUICK", "claude-haiku-5-5"),
          "default": os.environ.get("SAMPLE_MODEL", "claude-sonnet-5-5"),
          "complex": os.environ.get("SAMPLE_MODEL_COMPLEX", "claude-opus-5-5")}
MAX_INPUT = 60_000


def enabled() -> bool:
    return bool(KEY)


def _messages(inp):
    if isinstance(inp, str):
        return [{"role": "user", "content": inp}]
    ok = (isinstance(inp, list) and inp
          and all(isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str) for m in inp)
          and inp[-1]["role"] == "user")
    if not ok:
        raise ValueError("bad input")
    return [{"role": m["role"], "content": m["content"]} for m in inp]


def complete(inp, tier="default", max_tokens=2000) -> dict:
    """Blocking call (run it in a thread). Returns {"text", "truncated"}."""
    msgs = _messages(inp)
    if sum(len(m["content"]) for m in msgs) > MAX_INPUT:
        raise ValueError("input too long")
    body = json.dumps({"model": MODELS.get(tier, MODELS["default"]), "max_tokens": max_tokens, "messages": msgs}).encode()
    req = urllib.request.Request(BASE + "/v1/messages", data=body, method="POST", headers={
        "content-type": "application/json", "x-api-key": KEY, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=90) as r:
        out = json.loads(r.read())
    text = "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text")
    return {"text": text, "truncated": out.get("stop_reason") == "max_tokens"}
