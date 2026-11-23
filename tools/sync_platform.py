"""Turn the iPetro artifact HTML (as saved by the Artifact tool's `read`) into platform/index.html.

The artifact file is a full document wrapped by claude.ai (doctype, head, runtime blocks); the self-hosted server
wants only the page fragment (it prepends /shim.js itself) and has no /_runtime/ folder, so the wrapper and the
injected mermaid runtime blocks are removed.

    python tools/sync_platform.py path/to/artifact.html            # writes platform/index.html
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def convert(html: str) -> str:
    i = html.find("<title>")
    if i < 0:
        raise SystemExit("no <title> found: is this the iPetro artifact?")
    html = html[i:]
    html = re.sub(r"<!--claude-mermaid-runtime-begin:\d+-->.*?<!--claude-mermaid-runtime-end-->\s*", "", html, flags=re.S)
    html = re.sub(r"\s*</body>\s*</html>\s*$", "\n", html)
    return html


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    out = convert(src)
    (ROOT / "platform" / "index.html").write_text(out, encoding="utf-8", newline="\n")
    print("platform/index.html written,", len(out), "chars")
