"""Investor request tracking for outreach status.

Loaded from requests_seed.json. Rule: one unique product per investor, no product reused.
"""
import json
from .config import ROOT

SEED_FILE = ROOT / "requests_seed.json"

def load():
    """Load requests from seed file."""
    if not SEED_FILE.exists():
        return {"requests": []}
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))

def validate_product_uniqueness(requests):
    """Validate that each product is used only once across matched requests.
    
    Returns (is_valid, duplicates_dict) where duplicates_dict maps product -> count
    """
    product_counts = {}
    matched = [r for r in requests if r.get('status') != 'unmatched' and r.get('product') != 'unmatched']
    
    for req in matched:
        product = req['product']
        product_counts[product] = product_counts.get(product, 0) + 1
    
    duplicates = {p: count for p, count in product_counts.items() if count > 1}
    return len(duplicates) == 0, duplicates
