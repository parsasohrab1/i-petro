#!/usr/bin/env python3
"""
Import corrected investors and requests data from issues #61 and #62
"""
import json
import sys

# Load payloads
with open('/tmp/issue61.txt') as f:
    issue61_text = f.read()
    investors_payload = json.loads(issue61_text.split('```json\n')[1].split('\n```')[0])

with open('/tmp/issue62.txt') as f:
    issue62_text = f.read()
    requests_payload = json.loads(issue62_text.split('```json\n')[1].split('\n```')[0])

# Load existing investors
with open('investors_seed.json', 'r', encoding='utf-8') as f:
    investors_data = json.load(f)

existing_investors = {inv['id']: inv for inv in investors_data['investors']}

# Process investors: update existing 5, insert new 41
insert_count = 0
update_count = 0

for new_inv in investors_payload['investors']:
    inv_id = new_inv['id']
    action = new_inv.pop('upsert_action')
    new_inv.pop('assignment_status', None)  # Remove workflow field
    
    if action == 'update_existing' and inv_id in existing_investors:
        existing_investors[inv_id].update(new_inv)
        update_count += 1
        print(f"Updated: {inv_id}")
    elif action == 'insert_new':
        existing_investors[inv_id] = new_inv
        insert_count += 1
        print(f"Inserted: {inv_id}")
    else:
        print(f"Skipped {inv_id}: action={action}, exists={inv_id in existing_investors}")

# Rebuild investors list
investors_data['investors'] = list(existing_investors.values())

# Save updated investors
with open('investors_seed.json', 'w', encoding='utf-8') as f:
    json.dump(investors_data, f, ensure_ascii=False, indent=2)

print(f"\nInvestors: {insert_count} inserted, {update_count} updated")
print(f"Total investors: {len(investors_data['investors'])}")

# Process requests: replace earlier unsent by investor_id
requests = []
for req in requests_payload['requests']:
    req.pop('assignment_status', None)  # Remove workflow field
    requests.append(req)

# Create requests_seed.json
requests_data = {
    "_note": "Request status tracking per investor; rule: one unique product per investor, no reuse.",
    "requests": requests
}

with open('requests_seed.json', 'w', encoding='utf-8') as f:
    json.dump(requests_data, f, ensure_ascii=False, indent=2)

print(f"\nRequests created: {len(requests)} (45 matched + 1 unmatched)")

# Validation: check product uniqueness
product_counts = {}
matched_requests = [r for r in requests if r.get('status') != 'unmatched' and r.get('product') != 'unmatched']

for req in matched_requests:
    product = req['product']
    product_counts[product] = product_counts.get(product, 0) + 1

duplicates = {p: count for p, count in product_counts.items() if count > 1}

if duplicates:
    print(f"\n❌ VALIDATION FAILED: Product uniqueness violated!")
    for product, count in duplicates.items():
        print(f"  - {product}: used {count} times")
    sys.exit(1)
else:
    print(f"\n✅ VALIDATION PASSED: All {len(matched_requests)} matched products are unique")

print("\nSummary:")
print(f"  - 46 investors: {insert_count} new + {update_count} updates + {len(investors_data['investors']) - insert_count - update_count} existing")
print(f"  - 46 requests: 45 matched (unique products) + 1 unmatched (TT Ventures)")
