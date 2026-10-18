"""Company capability profile: curated product lines + a live check of the GitHub portfolio."""
import requests

from .config import load_products


def github_repos(user):
    try:
        r = requests.get(f"https://api.github.com/users/{user}/repos", params={"per_page": 100}, timeout=30)
        r.raise_for_status()
        return [{"name": x["name"], "description": x.get("description") or "", "updated": x["updated_at"][:10]}
                for x in r.json() if not x.get("fork")]
    except Exception:
        return []


def build_profile(cfg):
    products = load_products()
    repos = github_repos(cfg["company"]["github_user"])
    known = {r for p in products for r in p["repos"]}
    unmapped = [r["name"] for r in repos if r["name"] not in known]
    return {"products": products, "repo_count": len(repos), "unmapped_repos": unmapped}


def profile_text(cfg, profile):
    c = cfg["company"]
    lines = [
        f"Company: {c['name']}, {c['city']}, {c['country']} ({c['website']}).",
        f"Track record: {c['track_record']}",
        f"Public GitHub portfolio: github.com/{c['github_user']} ({profile['repo_count']} repositories).",
        "Product lines (maturity stated conservatively):",
    ]
    for p in profile["products"]:
        flag = " [IP ownership to be confirmed before offering]" if p.get("ip_check") else ""
        lines.append(f"- {p['id']}: {p['name']} ({p['domain']}) - {p['summary']} Maturity: {p['maturity']}.{flag}")
    return "\n".join(lines)
