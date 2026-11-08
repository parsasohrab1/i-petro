"""Test that investor request products are unique and match authoritative CSV."""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import requests

def test_product_uniqueness():
    """Each product must be assigned to exactly one investor/paper (no reuse)."""
    data = requests.load()
    reqs = data.get("requests", [])
    
    # Load authoritative assignments
    product_assignments = requests.load_product_assignments()
    print(f"Loaded {len(product_assignments)} authoritative product assignments from CSV")
    
    is_valid, duplicates, conflicts = requests.validate_product_uniqueness(reqs, product_assignments)
    
    if duplicates:
        msg = "Product uniqueness violated (duplicates within requests):\n"
        for product, count in duplicates.items():
            msg += f"  - {product}: used {count} times in requests\n"
        raise AssertionError(msg)
    
    if conflicts:
        msg = "Product assignment conflicts with authoritative CSV:\n"
        for product, [req_assigned, csv_assigned] in conflicts.items():
            msg += f"  - {product}: assigned to {req_assigned} in requests, but CSV says {csv_assigned}\n"
        raise AssertionError(msg)
    
    if not is_valid:
        raise AssertionError("Product uniqueness validation failed")
    
    # Count matched requests
    matched = [r for r in reqs if r.get('status') != 'unmatched' and r.get('product') != 'unmatched']
    print(f"✓ All {len(matched)} matched products are unique")
    print(f"✓ No conflicts with authoritative CSV assignments")
    print(f"✓ Total requests: {len(reqs)} (including {len(reqs) - len(matched)} unmatched)")
    
    # Report paper-assigned products
    paper_products = [p for p, a in product_assignments.items() if a == 'paper']
    print(f"✓ {len(paper_products)} products correctly assigned to papers (not investors)")

if __name__ == "__main__":
    test_product_uniqueness()
    print("\nAll tests passed!")
