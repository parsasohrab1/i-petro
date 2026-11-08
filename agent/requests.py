"""Investor request tracking for outreach status.

Loaded from requests_seed.json. Rule: one unique product per investor/paper, no product reused.
"""
import json
import csv
from .config import ROOT

SEED_FILE = ROOT / "requests_seed.json"
PRODUCT_ASSIGNMENT_CSV = ROOT / "product-assignment.csv"

def load():
    """Load requests from seed file."""
    if not SEED_FILE.exists():
        return {"requests": []}
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))

def load_product_assignments():
    """Load authoritative product assignments from CSV.
    
    Returns dict mapping product -> assigned_to (investor id or 'paper')
    """
    if not PRODUCT_ASSIGNMENT_CSV.exists():
        return {}
    
    assignments = {}
    with PRODUCT_ASSIGNMENT_CSV.open('r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            product = row['product'].strip()
            assigned_to = row['assigned_to'].strip()
            if product:
                assignments[product] = assigned_to
    return assignments

def validate_product_uniqueness(requests, product_assignments=None):
    """Validate that each product is used only once across matched requests AND papers.
    
    Args:
        requests: List of request records
        product_assignments: Optional dict from load_product_assignments() for validation
    
    Returns (is_valid, duplicates_dict, conflicts_dict) where:
        - duplicates_dict maps product -> count (within requests)
        - conflicts_dict maps product -> [assigned_in_requests, assigned_in_csv]
    """
    if product_assignments is None:
        product_assignments = load_product_assignments()
    
    product_counts = {}
    product_to_investor = {}
    matched = [r for r in requests if r.get('status') != 'unmatched' and r.get('product') != 'unmatched']
    
    for req in matched:
        product = req['product']
        investor = req.get('investor_id', req.get('investor', ''))
        product_counts[product] = product_counts.get(product, 0) + 1
        if product not in product_to_investor:
            product_to_investor[product] = []
        product_to_investor[product].append(investor)
    
    duplicates = {p: count for p, count in product_counts.items() if count > 1}
    
    # Check conflicts with CSV assignments (products assigned to papers or different investors)
    conflicts = {}
    for product, investor_list in product_to_investor.items():
        if product in product_assignments:
            csv_assigned = product_assignments[product]
            request_assigned = investor_list[0] if len(investor_list) == 1 else investor_list
            # Conflict if CSV says "paper" but we're assigning to investor, or different investor
            if csv_assigned == 'paper':
                conflicts[product] = [request_assigned, 'paper (from CSV)']
            elif csv_assigned != investor_list[0]:
                conflicts[product] = [request_assigned, csv_assigned]
    
    is_valid = len(duplicates) == 0 and len(conflicts) == 0
    return is_valid, duplicates, conflicts
