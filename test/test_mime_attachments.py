#!/usr/bin/env python3
"""
Test MIME email parsing - verify attachments are valid PDFs
"""
import sys
import email
from email import policy
import os

def test_eml_file(eml_path, output_dir):
    """Parse .eml file and extract attachments"""
    print(f"\n=== Testing {os.path.basename(eml_path)} ===\n")
    
    with open(eml_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    
    # Check headers
    print(f"From: {msg.get('From', 'N/A')}")
    print(f"To: {msg.get('To', 'N/A')}")
    print(f"Subject: {msg.get('Subject', 'N/A')}")
    print(f"MIME-Version: {msg.get('MIME-Version', 'N/A')}")
    print(f"Content-Type: {msg.get_content_type()}")
    
    # Extract body
    body_text = ''
    if msg.is_multipart():
        for part in msg.iter_parts():
            if part.get_content_type() == 'text/plain':
                body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                break
    else:
        body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
    
    has_enclosures_en = 'Enclosures:' in body_text
    has_enclosures_fa = 'پیوست' in body_text
    has_enclosures = has_enclosures_en or has_enclosures_fa
    print(f"\nBody mentions attachments: {has_enclosures}")
    if has_enclosures:
        if has_enclosures_en:
            print("  (English: 'Enclosures:')")
        if has_enclosures_fa:
            print("  (Persian: 'پیوست')")
    
    # Extract attachments
    attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename() or 'unnamed_attachment'
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True)
        
        # Check if valid PDF
        is_pdf = payload.startswith(b'%PDF')
        
        # Save to artifacts
        att_path = os.path.join(output_dir, filename)
        with open(att_path, 'wb') as af:
            af.write(payload)
        
        attachments.append({
            'filename': filename,
            'content_type': content_type,
            'size': len(payload),
            'is_valid_pdf': is_pdf,
            'path': att_path
        })
        
        print(f"\nAttachment: {filename}")
        print(f"  Content-Type: {content_type}")
        print(f"  Size: {len(payload)} bytes")
        print(f"  Starts with %PDF: {is_pdf}")
        print(f"  Saved to: {att_path}")
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Total attachments: {len(attachments)}")
    all_pdf_type = all(a['content_type'] == 'application/pdf' for a in attachments)
    all_valid_pdf = all(a['is_valid_pdf'] for a in attachments)
    print(f"All have Content-Type application/pdf: {all_pdf_type}")
    print(f"All start with %PDF: {all_valid_pdf}")
    print(f"Body mentions files: {has_enclosures}")
    
    # Test results
    passed = []
    failed = []
    
    if len(attachments) > 0:
        passed.append("Has attachments")
    else:
        failed.append("No attachments found")
    
    if all_pdf_type:
        passed.append("All attachments are application/pdf")
    else:
        failed.append("Some attachments are not application/pdf")
    
    if all_valid_pdf:
        passed.append("All PDFs start with %PDF")
    else:
        failed.append("Some PDFs don't start with %PDF")
    
    if has_enclosures:
        passed.append("Body mentions attachments")
    else:
        failed.append("Body doesn't mention attachments")
    
    # Check for contracts (should be excluded)
    has_contract = any('contract' in a['filename'].lower() or 'قرارداد' in a['filename'] for a in attachments)
    if not has_contract:
        passed.append("No contracts attached (correct)")
    else:
        failed.append("Contract found in attachments (should be excluded)")
    
    print(f"\n=== Test Results ===")
    print(f"✓ Passed ({len(passed)}):")
    for p in passed:
        print(f"  ✓ {p}")
    
    if failed:
        print(f"\n✗ Failed ({len(failed)}):")
        for f in failed:
            print(f"  ✗ {f}")
    
    return len(failed) == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: test_mime_attachments.py <eml_file> [output_dir]")
        sys.exit(1)
    
    eml_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '/opt/cursor/artifacts'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    success = test_eml_file(eml_path, output_dir)
    sys.exit(0 if success else 1)
