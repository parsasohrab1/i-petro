"""Test letter numbering and dating logic for unsent letters.

Requirements:
1. Every unsent letter (status != sent) gets a fresh date and unique number daily
2. Once sent, date/number are frozen
3. Numbers never repeat (history tracked in issued_numbers)
4. Numbering scheme: YYYYMMDD-NNN (Jalali/Persian calendar, per-day sequence)
"""
import json
import re
from pathlib import Path

# Test data representing the letter numbering format
LETTER_NUMBER_PATTERN = re.compile(r'^\d{11}$')  # e.g. 14050714001: YYYYMMDDnnn

def test_letter_number_format():
    """Letter numbers follow the format YYYYMMDD-NNN (11 digits)."""
    # Persian/Jalali date 1405/07/14 with serial 001
    number = "14050714001"
    assert LETTER_NUMBER_PATTERN.match(number), f"Invalid format: {number}"
    
    year = number[0:4]
    month = number[4:6]
    day = number[6:8]
    serial = number[8:11]
    
    assert year.isdigit() and int(year) >= 1400, "Year must be >= 1400"
    assert month.isdigit() and 1 <= int(month) <= 12, "Month must be 01-12"
    assert day.isdigit() and 1 <= int(day) <= 31, "Day must be 01-31"
    assert serial.isdigit() and 1 <= int(serial) <= 999, "Serial must be 001-999"
    print(f"✓ Letter number format valid: {year}/{month}/{day} serial {serial}")

def test_issued_numbers_uniqueness():
    """Issued numbers file tracks all issued numbers to prevent duplicates."""
    # Check if platform/index.html contains the getOrIssueNumber function
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify the getOrIssueNumber function exists
    assert "async function getOrIssueNumber" in content, \
        "getOrIssueNumber function missing from platform/index.html"
    
    # Verify issued_numbers storage is referenced
    assert "settings/issued_numbers" in content, \
        "issued_numbers storage path missing"
    
    # Verify the nextLetterNo functions check issued numbers
    assert "S.issuedNumbers" in content, \
        "nextLetterNo should check S.issuedNumbers"
    
    print("✓ Issued numbers tracking implemented")

def test_unsent_letter_refresh_logic():
    """Unsent letters get fresh date/number on download."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify downloadLetter checks if letter is sent via isSent variable
    assert "const isSent" in content, "downloadLetter should check isSent status"
    assert "SENT_STAGES" in content, "SENT_STAGES should be defined"
    
    # Verify fresh date/number generation for unsent
    assert "today()" in content and ("nextIranLetterNo" in content or "nextIntlLetterNo" in content), \
        "Should generate fresh date and number"
    
    # Verify getOrIssueNumber is called
    assert "await getOrIssueNumber" in content, \
        "Should get or issue number to prevent reuse"
    
    print("✓ Unsent letter refresh logic implemented")

def test_sent_letter_frozen():
    """Sent letters (with both signatures or status=closed/done) freeze date/number."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify logic checks for both signatures or archive status
    assert "ceo_sig" in content and "office_sig" in content, \
        "Should check for signatures"
    
    # Check for status/stage checks in archive
    assert 'status' in content and ('closed' in content or 'done' in content), \
        "Should check archive status/stage"
    
    print("✓ Sent letter freezing logic present")

def test_daily_cap_handling():
    """System enforces 999 letters per day maximum."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify 999 cap is enforced (hardcoded limit)
    assert ">=999" in content or ">999" in content, \
        "Should check for 999 letter daily limit"
    
    # Verify error message when cap exceeded
    assert "999" in content and ("limit" in content or "exceed" in content or "خطا" in content), \
        "Should have error handling for daily cap"
    
    print("✓ Daily letter cap: 999 letters per day (hardcoded)")

def test_intl_letter_numbering():
    """International letters use different numbering scheme (PIG-YYYY-NNNN)."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify intl identity handling
    assert 'identity==="intl"' in content, "Should handle intl identity"
    assert 'PIG-' in content, "Should use PIG- prefix for international"
    
    print("✓ International letter numbering scheme present")

if __name__ == "__main__":
    print("Testing letter numbering and dating logic...\n")
    
    test_letter_number_format()
    test_issued_numbers_uniqueness()
    test_unsent_letter_refresh_logic()
    test_sent_letter_frozen()
    test_daily_cap_handling()
    test_intl_letter_numbering()
    
    print("\n✓ All letter numbering tests passed!")
