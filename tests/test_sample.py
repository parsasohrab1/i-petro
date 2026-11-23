import io
import json

import pytest

from server import sample


def test_messages_validation():
    assert sample._messages("hi") == [{"role": "user", "content": "hi"}]
    with pytest.raises(ValueError):
        sample._messages([{"role": "assistant", "content": "x"}])
    with pytest.raises(ValueError):
        sample._messages(5)


def test_complete_calls_messages_api(monkeypatch):
    seen = {}

    class R(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake(req, timeout=0):
        seen["url"], seen["body"], seen["key"] = req.full_url, json.loads(req.data), req.get_header("X-api-key")
        return R(json.dumps({"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}).encode())

    monkeypatch.setattr(sample, "KEY", "k")
    monkeypatch.setattr(sample.urllib.request, "urlopen", fake)
    out = sample.complete("score this", "quick")
    assert out == {"text": "ok", "truncated": False}
    assert seen["url"].endswith("/v1/messages") and seen["key"] == "k"
    assert seen["body"]["model"] == sample.MODELS["quick"]


def test_too_long_input_rejected():
    with pytest.raises(ValueError):
        sample.complete("x" * (sample.MAX_INPUT + 1))
