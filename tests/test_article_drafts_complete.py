"""
Test that all paper rows have both abstract and manuscript data (or drafts).
PR #69 made buttons always show; this test ensures no paper resolves to placeholder.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

def test_article_drafts_file_exists():
    """data/article_drafts.json must exist."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    assert drafts_file.exists(), "data/article_drafts.json not found"
    
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    assert "drafts" in data, "article_drafts.json missing 'drafts' key"
    assert isinstance(data["drafts"], dict), "drafts must be a dict"

def test_all_drafts_have_required_fields():
    """Every draft must have venue_name, product, abstract, and manuscript."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        assert "venue_name" in draft, f"{venue_key}: missing venue_name"
        assert "product" in draft, f"{venue_key}: missing product"
        assert "abstract" in draft, f"{venue_key}: missing abstract"
        assert "manuscript" in draft, f"{venue_key}: missing manuscript"
        
        # Check abstract structure
        abs_data = draft["abstract"]
        assert "title" in abs_data, f"{venue_key}: abstract missing title"
        assert "text" in abs_data or "abstract_text" in abs_data, f"{venue_key}: abstract missing text"
        assert "keywords" in abs_data, f"{venue_key}: abstract missing keywords"
        assert isinstance(abs_data["keywords"], list), f"{venue_key}: keywords must be list"
        
        # Check manuscript structure
        ms_data = draft["manuscript"]
        assert "title" in ms_data, f"{venue_key}: manuscript missing title"
        assert "abstract_full" in ms_data or "sections" in ms_data, f"{venue_key}: manuscript needs abstract_full or sections"
        assert "keywords" in ms_data, f"{venue_key}: manuscript missing keywords"

def test_five_firebase_venues_have_drafts():
    """The 5 Firebase-only venues mentioned must have drafts."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    drafts = data["drafts"]
    
    # Check that we have at least 5 drafts
    assert len(drafts) >= 5, f"Expected at least 5 venue drafts, got {len(drafts)}"
    
    # Check for specific venues mentioned in requirements
    # (keys are normalized; actual keys in JSON may differ)
    expected_venues = [
        "applied_energy",  # Applied Energy (Elsevier)
        "intellisys",      # IntelliSys 2027
        "awwa",            # AWWA 2027
        "global_energy",   # Global Energy Show 2027
        "eign"             # EIGN-2027
    ]
    
    draft_keys_lower = [k.lower() for k in drafts.keys()]
    found = []
    for expected in expected_venues:
        if any(expected in dk for dk in draft_keys_lower):
            found.append(expected)
    
    assert len(found) >= 5, f"Expected all 5 venues, found {len(found)}: {found}. Keys: {list(drafts.keys())}"

def test_abstract_word_counts():
    """Abstracts should be roughly 150-300 words for most venues."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        abs_text = draft["abstract"].get("text") or draft["abstract"].get("abstract_text", "")
        word_count = len(abs_text.split())
        # Reasonable range: abstracts are typically 150-350 words
        assert 100 <= word_count <= 400, f"{venue_key}: abstract has {word_count} words (expected 100-400)"

def test_trl_statement_in_manuscripts():
    """Every manuscript must explicitly state TRL and that results are pending validation."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        # Check that TRL is stated somewhere
        trl_stated = "trl" in draft or "TRL" in str(draft)
        assert trl_stated, f"{venue_key}: TRL not mentioned"
        
        # Check draft_note for validation warning
        draft_note = draft.get("draft_note", "")
        validation_warned = any(phrase in draft_note.lower() for phrase in [
            "pending validation",
            "no real",
            "simulation",
            "trl 3",
            "trl 4",
            "draft"
        ])
        assert validation_warned, f"{venue_key}: draft_note must warn about validation status"

def test_products_unique_across_venues():
    """Each product should be assigned to only one venue (uniqueness rule)."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    products_used = []
    for venue_key, draft in data["drafts"].items():
        product = draft.get("product")
        assert product not in products_used, f"Product {product} used multiple times (venue {venue_key})"
        products_used.append(product)

def test_parsa_babaei_submitting_member():
    """All drafts should list Parsa Babaei as submitting team member."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        submitter = draft.get("submitting_team_member", "")
        assert "Parsa" in submitter or "Babaei" in submitter, f"{venue_key}: submitting_team_member must be Parsa Babaei"

if __name__ == "__main__":
    # Run all tests
    test_article_drafts_file_exists()
    test_all_drafts_have_required_fields()
    test_five_firebase_venues_have_drafts()
    test_abstract_word_counts()
    test_trl_statement_in_manuscripts()
    test_products_unique_across_venues()
    test_parsa_babaei_submitting_member()
    print("✓ All article drafts tests passed!")
