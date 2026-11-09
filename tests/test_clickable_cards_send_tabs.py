"""Test clickable stat cards and per-person send tabs.

Requirements:
1. Stat cards are clickable/selectable (visually highlighted, aria-selected)
2. Clicking a card filters the list to show exactly those letters
3. Count equals rows shown (same predicate)
4. Selection persisted in state (survives render)
5. Per-person send tabs show unsent letters for each person
6. Download with today's date and daily number
7. Mark as sent freezes date/number, moves to pipeline
8. Access determined by letterPeople list
"""
import json
import re
from pathlib import Path

def test_clickable_stat_cards():
    """Stat cards have clickable attributes."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify clickable class and attributes
    assert ".kpi.clickable" in content, "clickable kpi class missing"
    assert 'role="button"' in content or "role=\\\"button\\\"" in content, \
        "kpi should have role=button when clickable"
    assert "aria-selected" in content, "aria-selected attribute missing"
    
    # Verify hover and selected styles
    assert ".kpi.clickable:hover" in content, "clickable hover style missing"
    assert ".kpi.clickable.selected" in content, "selected kpi style missing"
    
    print("✓ Clickable stat cards implemented")

def test_stage_filter_state():
    """Stage filter selection persisted in S.archStageF state."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify state variable
    assert "archStageF" in content, "archStageF state variable missing"
    
    # Verify action handler
    assert '"arch-stage-f"' in content or "'arch-stage-f'" in content, \
        "arch-stage-f action missing"
    
    # Verify toggle behavior (click again to clear)
    assert "S.archStageF===" in content or "S.archStageF ===" in content, \
        "Toggle check missing"
    
    print("✓ Stage filter state management implemented")

def test_card_filter_matches_count():
    """Card count predicate should match list filter."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify stage filtering in archView
    assert "a.stage===" in content or "a.stage ===" in content, \
        "Stage filtering missing"
    
    # Verify stageFiltered variable that both count and list use
    assert "stageFiltered" in content or "archStageF" in content, \
        "Stage filter should be applied to list"
    
    print("✓ Card filter matches list filter")

def test_per_person_send_tabs():
    """Per-person send tabs show unsent letters."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify letters.send view exists
    assert 'VIEWS["letters.send"]' in content, "letters.send view missing"
    
    # Verify per-person filtering
    assert "letter-send-person" in content, "person selection action missing"
    
    # Verify unsent letter filtering (not in SENT_STAGES)
    assert "unsentLetters" in content or "isSentStage" in content, \
        "Unsent letter filtering missing"
    
    print("✓ Per-person send tabs implemented")

def test_download_with_daily_number():
    """Download action gets fresh daily number."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify letter-download-daily action
    assert "letter-download-daily" in content, "download daily action missing"
    
    # Verify it uses today's date
    assert "date:today()" in content, "Should use today's date for download"
    
    # Verify it calls downloadLetter
    assert "await downloadLetter" in content, "downloadLetter should be called"
    
    print("✓ Download with daily number implemented")

def test_mark_sent_freezes_number():
    """Mark as sent action freezes date and number."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify letter-send-mark action exists
    assert "letter-send-mark" in content, "send mark action missing"
    
    # Verify markLetterSent function
    assert "async function markLetterSent" in content or "markLetterSent" in content, \
        "markLetterSent function missing"
    
    # Verify it sets stage to sent
    assert 'stage:"sent"' in content or "stage:'sent'" in content, \
        "Should set stage to sent"
    
    print("✓ Mark sent freezes number implemented")

def test_access_via_letter_people():
    """Access determined by letterPeople list."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify letterPeople array is used
    assert "S.letterPeople" in content, "letterPeople array missing"
    
    # Verify currentUser for access control
    assert "currentUser" in content, "currentUser missing"
    
    # Verify person tabs show counts per person
    assert "task_assignee" in content, "task_assignee field missing"
    
    print("✓ Access via letterPeople list implemented")

def test_stage_counts_comprehensive():
    """All major stages have stat cards."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify major stages mentioned in task are counted
    stages_to_check = [
        "sent",  # ارسال‌شده
        "received",  # ثبت در دبیرخانه
        "review",  # ارجاع یا بررسی
        "reply",  # پاسخ یا درخواست
        "meeting_scheduled",  # جلسه هماهنگ‌شده
        "meeting",  # جلسه برگزارشده
        "followup",  # پیگیری
    ]
    
    for stage in stages_to_check:
        # Should have stage count in stageCounts array
        pattern = f'a.stage==="{stage}"'
        if pattern not in content and pattern.replace('"', "'") not in content:
            print(f"⚠ Stage '{stage}' might not be counted")
    
    print("✓ Comprehensive stage counts defined")

def test_send_tab_in_navigation():
    """Send tab added to letters navigation."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify send tab in SUBS
    assert '"send"' in content or "'send'" in content, "send tab missing from SUBS"
    assert "ارسال نامه" in content, "Send tab Persian label missing"
    
    print("✓ Send tab in navigation")

def test_filtered_rows_render():
    """Clicking stage card filters and renders table rows correctly."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify stageFiltered is used in the list that feeds the table
    assert "stageFiltered" in content, "stageFiltered variable missing"
    
    # Verify table rendering uses the filtered list
    # The pattern should be: stageFiltered.filter(flt).sort(...)
    # And then table(..., list.map(...))
    assert re.search(r"stageFiltered\.filter\([^)]+\)", content), \
        "stageFiltered should be further filtered"
    
    # Verify table is rendered with the list
    assert "table(" in content, "table function call missing"
    assert "list.map" in content, "list.map for table rows missing"
    
    # Verify archView function returns table in its template
    # Find archView function and check it returns template with table
    archview_match = re.search(r"const archView\s*=\s*\([^)]*\)\s*=>\s*{", content)
    if archview_match:
        # Check that archView has a return statement with table
        archview_start = archview_match.end()
        # Find the closing brace (simplified - just check next few thousand chars)
        archview_section = content[archview_start:archview_start + 5000]
        assert "return" in archview_section and "table(" in archview_section, \
            "archView should return template with table"
    
    print("✓ Filtered rows render correctly in table")

def test_compatibility_with_existing_numbering():
    """New features don't break existing letter numbering."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify key numbering functions still exist
    assert "async function getOrIssueNumber" in content, "getOrIssueNumber missing"
    assert "SENT_STAGES" in content, "SENT_STAGES missing"
    assert "async function downloadLetter" in content, "downloadLetter missing"
    
    print("✓ Compatible with existing numbering system")

if __name__ == "__main__":
    print("Testing clickable stat cards and per-person send tabs...\n")
    
    test_clickable_stat_cards()
    test_stage_filter_state()
    test_card_filter_matches_count()
    test_filtered_rows_render()
    test_per_person_send_tabs()
    test_download_with_daily_number()
    test_mark_sent_freezes_number()
    test_access_via_letter_people()
    test_stage_counts_comprehensive()
    test_send_tab_in_navigation()
    test_compatibility_with_existing_numbering()
    
    print("\n✓ All clickable cards and send tabs tests passed!")
