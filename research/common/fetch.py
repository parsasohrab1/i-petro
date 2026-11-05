"""Download helpers for the real-data validation work.

Only hosts that the working environment allows are used (GitHub raw / git clone, PyPI, conda). Large downloads are cached in
$RESEARCH_DATA (default ~/research_data) and are never committed to the repository.
"""
import hashlib
import os
import pathlib
import subprocess
import urllib.request

DATA = pathlib.Path(os.environ.get("RESEARCH_DATA", pathlib.Path.home() / "research_data"))


def path(*parts):
    p = DATA.joinpath(*parts); p.parent.mkdir(parents=True, exist_ok=True); return p


def raw(repo, ref, file, dest=None, timeout=120):
    """Download one file from a public GitHub repository (https://raw.githubusercontent.com/<repo>/<ref>/<file>)."""
    dest = pathlib.Path(dest) if dest else path(repo.replace("/", "__"), pathlib.PurePosixPath(file).name)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"https://raw.githubusercontent.com/{repo}/{ref}/{file}", timeout=timeout) as r, open(dest, "wb") as f:
            f.write(r.read())
    return dest


def clone(repo, subdirs=None, depth=1):
    """Shallow (optionally sparse) clone of a public GitHub repository into the cache."""
    d = path(repo.replace("/", "__"), "clone"); 
    if not d.exists():
        subprocess.run(["git", "clone", "-q", "--depth", str(depth), "--filter=blob:none", "--sparse", f"https://github.com/{repo}", str(d)], check=True)
        if subdirs:
            subprocess.run(["git", "-C", str(d), "sparse-checkout", "set", *subdirs], check=True)
        else:
            subprocess.run(["git", "-C", str(d), "sparse-checkout", "disable"], check=True)
    return d


def sha256(p):
    h = hashlib.sha256(); h.update(pathlib.Path(p).read_bytes()); return h.hexdigest()
