"""Company capability profile from products.json (generic product names only)."""
from .config import load_products


def build_profile(cfg):
    return {"products": load_products()}


def profile_text(cfg, profile):
    c = cfg["company"]
    lines = [
        f"Company: {c['name']}, {c['city']}, {c['country']} ({c['website']}).",
        f"Track record: {c['track_record']}",
        "Product lines (maturity stated conservatively):",
    ]
    for p in profile["products"]:
        flag = " [IP ownership to be confirmed before offering]" if p.get("ip_check") else ""
        lines.append(f"- {p['id']}: {p['name']} ({', '.join(p['domains'])}) - {p['summary']} Maturity: {p['maturity']}.{flag}")
    return "\n".join(lines)
