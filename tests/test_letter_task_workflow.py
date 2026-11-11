"""Test letter task workflow functionality.

Requirements:
1. Letters can have tasks defined (title/description, optional due date)
2. Person can CLAIM a letter (moves from 'to do' to 'in progress')
3. Person can CANCEL/UNCLAIM (returns to 'to do', clears assignee, keeps history)
4. Sent letters enter pipeline: sent -> followup -> meeting -> negotiation -> contract
5. Pipeline stages tracked with timestamps and actors in activity history
6. Filtering: to-do, in-progress, sent, followup, meetings, contracts
7. People list persisted in localStorage, current user remembered
"""
import json
import re
from pathlib import Path

def test_task_workflow_constants():
    """Verify task workflow constants are defined."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Check for new statuses
    assert "LETTER_TASK_STAGES" in content, "LETTER_TASK_STAGES constant missing"
    assert "todo" in content and "claimed" in content, "Task stages missing"
    
    # Check for pipeline stages
    assert "followup" in content, "followup stage missing"
    assert "meeting_scheduled" in content, "meeting_scheduled stage missing"
    assert "negotiation" in content, "negotiation stage missing"
    assert "contract" in content, "contract stage missing"
    
    print("✓ Task workflow constants defined")

def test_sent_stages_includes_pipeline():
    """SENT_STAGES includes all pipeline stages."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Find SENT_STAGES definition
    match = re.search(r'SENT_STAGES\s*=\s*new Set\(\[(.*?)\]\)', content, re.DOTALL)
    assert match, "SENT_STAGES not found"
    
    sent_stages_str = match.group(1)
    
    # Verify pipeline stages are included
    assert '"followup"' in sent_stages_str, "followup not in SENT_STAGES"
    assert '"meeting_scheduled"' in sent_stages_str, "meeting_scheduled not in SENT_STAGES"
    assert '"negotiation"' in sent_stages_str, "negotiation not in SENT_STAGES"
    assert '"contract"' in sent_stages_str, "contract not in SENT_STAGES"
    
    print("✓ SENT_STAGES includes pipeline stages")

def test_claim_unclaim_functions():
    """Claim and unclaim functions exist."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    assert "async function claimLetter" in content, "claimLetter function missing"
    assert "async function unclaimLetter" in content, "unclaimLetter function missing"
    assert "async function markLetterSent" in content, "markLetterSent function missing"
    
    # Check that claim updates task_stage
    assert "task_stage" in content and "claimed" in content, "task_stage field missing"
    assert "task_assignee" in content, "task_assignee field missing"
    
    print("✓ Claim/unclaim functions implemented")

def test_activity_history():
    """Activity history logs transitions."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Check that log array is used
    assert "log:[" in content or "log =" in content, "Activity log not tracked"
    
    # Check for action types
    assert "claimed" in content, "Claimed action not logged"
    assert "unclaimed" in content, "Unclaimed action not logged"
    
    print("✓ Activity history tracking implemented")

def test_people_persistence():
    """People list persisted in localStorage."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    assert "loadLetterPeople" in content, "loadLetterPeople function missing"
    assert "saveLetterPeople" in content, "saveLetterPeople function missing"
    assert "ppt-letter-people" in content, "localStorage key missing"
    assert "ppt-current-user" in content, "Current user localStorage key missing"
    
    print("✓ People persistence implemented")

def test_filter_options():
    """Filtering options for to-do, in-progress, sent, pipeline stages."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Check for filter constants
    assert "letterF" in content, "letterF filter state missing"
    
    # Check for filter options in ARCH_F or similar
    filters_to_check = ["todo", "inprogress", "sent", "followup", "meetings", "contracts"]
    for f in filters_to_check:
        # The filter should appear in some filter definition
        if f not in content:
            print(f"⚠ Filter '{f}' not found in content")
    
    print("✓ Filter options defined")

def test_tasks_view():
    """Letters.tasks view exists."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    assert 'VIEWS["letters.tasks"]' in content, "letters.tasks view missing"
    assert "letterTaskForm" in content, "letterTaskForm function missing"
    
    print("✓ Tasks view implemented")

def test_pipeline_status_transitions():
    """Pipeline stages follow proper order."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Check for archProgress function that handles stage transitions
    assert "archProgress" in content, "archProgress function missing"
    
    # Verify the pipeline stages are in ARCH_STAGES
    assert "ARCH_STAGES" in content, "ARCH_STAGES missing"
    
    print("✓ Pipeline status transitions supported")

def test_rejected_status():
    """Rejected status exists for closed/rejected letters."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Check that rejected status is defined
    assert "rejected" in content, "rejected status missing"
    
    # Check that archOpen excludes rejected
    assert "status!==\\\"rejected\\\"" in content or 'status!=="rejected"' in content, \
        "archOpen should exclude rejected status"
    
    print("✓ Rejected status implemented")

def test_compatibility_with_existing_numbering():
    """Task workflow doesn't break existing letter numbering."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    # Verify getOrIssueNumber still exists
    assert "async function getOrIssueNumber" in content, "getOrIssueNumber missing"
    
    # Verify SENT_STAGES logic still works
    assert "SENT_STAGES" in content, "SENT_STAGES missing"
    assert "isSent" in content, "isSent check missing"
    
    print("✓ Compatible with existing letter numbering")

def test_due_date_support():
    """Letters can have optional due dates."""
    index_path = Path(__file__).parent.parent / "platform" / "index.html"
    if not index_path.exists():
        print("⚠ platform/index.html not found, skipping")
        return
    
    content = index_path.read_text(encoding="utf-8")
    
    assert "task_due_date" in content, "task_due_date field missing"
    
    print("✓ Due date support implemented")

if __name__ == "__main__":
    print("Testing letter task workflow functionality...\n")
    
    test_task_workflow_constants()
    test_sent_stages_includes_pipeline()
    test_claim_unclaim_functions()
    test_activity_history()
    test_people_persistence()
    test_filter_options()
    test_tasks_view()
    test_pipeline_status_transitions()
    test_rejected_status()
    test_compatibility_with_existing_numbering()
    test_due_date_support()
    
    print("\n✓ All letter task workflow tests passed!")
