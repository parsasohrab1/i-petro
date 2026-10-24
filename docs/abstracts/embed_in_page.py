"""Refresh the ABS data block in platform/index.html from platform/abstracts_seed.json.

usage: python docs/abstracts/embed_in_page.py
"""
import json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
seed = json.load(open(ROOT / "platform/abstracts_seed.json", encoding="utf-8"))
seed.pop("_note", None)
page = ROOT / "platform/index.html"
s = page.read_text(encoding="utf-8")
blob = json.dumps(seed, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
s, n = re.subn(r"/\*ABS-START\*/.*?/\*ABS-END\*/", lambda m: "/*ABS-START*/const ABS = " + blob + ";/*ABS-END*/", s, count=1, flags=re.S)
assert n == 1, "markers not found"
page.write_text(s, encoding="utf-8")
print("embedded", len(blob), "bytes")
