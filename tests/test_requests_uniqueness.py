"""Test that investor request products are unique."""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import requests

def test_product_uniqueness():
    """Each product must be assigned to exactly one investor (no reuse)."""
    data = requests.load()
    reqs = data.get("requests", [])
    
    is_valid, duplicates = requests.validate_product_uniqueness(reqs)
    
    if not is_valid:
        msg = "Product uniqueness violated:\n"
        for product, count in duplicates.items():
            msg += f"  - {product}: used {count} times\n"
        raise AssertionError(msg)
    
    # Count matched requests
    matched = [r for r in reqs if r.get('status') != 'unmatched' and r.get('product') != 'unmatched']
    print(f"✓ All {len(matched)} matched products are unique")
    print(f"✓ Total requests: {len(reqs)} (including {len(reqs) - len(matched)} unmatched)")

if __name__ == "__main__":
    test_product_uniqueness()
    print("\nAll tests passed!")
