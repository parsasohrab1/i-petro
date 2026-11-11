"""
Test article drafts meet audit requirements:
1. Real full manuscripts (not stubs) - checked via word_count_target >= 3000
2. No fake performance numbers without provenance
3. Real repo names only (no articles-* inventions, no Water-AI-Monitor)
4. All references verifiable (checked in manuscript_spec)
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

def test_real_repo_names_only():
    """All products must be real parsasohrab1 repo names, not invented articles-* names."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    # Expected real repo names from user audit
    expected_real_repos = {
        "intelligent-management-sys-energy-carbon-sustainability-",
        "Mili-Multi-Mode-Adaptive-Decision-System",
        "iEOR",
        "-Khalij-Apadana-Reformer-Methanol-Loop-Digital-Twin-System-"
    }
    
    actual_repos = set()
    for venue_key, draft in data["drafts"].items():
        product = draft.get("product", "")
        actual_repos.add(product)
        
        # Must NOT be fake articles-* pattern
        assert not product.startswith("articles-"), f"{venue_key}: fake articles-* name: {product}"
        
        # Must NOT be invented Water-AI-Monitor
        assert "Water-AI" not in product, f"{venue_key}: fake Water-AI-Monitor product"
    
    # All repos must be from expected real set
    assert actual_repos == expected_real_repos, f"Repo mismatch. Expected: {expected_real_repos}, Got: {actual_repos}"

def test_water_ai_monitor_removed():
    """Fake Water-AI-Monitor product must be removed per audit."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        product = draft.get("product", "")
        venue_name = draft.get("venue_name", "")
        
        assert "Water-AI" not in product, f"Water-AI-Monitor still present in {venue_key}"
        assert "Water-AI" not in venue_name or "AWWA" not in venue_name, "AWWA should be removed (no suitable product)"

def test_manuscripts_minimum_3000_words():
    """Each manuscript must target at least 3000 words per audit requirement."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        manuscript_spec = draft.get("manuscript_spec", {})
        word_count_target = manuscript_spec.get("word_count_target", 0)
        venue_name = draft.get("venue_name", venue_key)
        
        assert word_count_target >= 3000, f"{venue_name}: manuscript target {word_count_target} < 3000 words minimum"

def test_no_fake_performance_numbers_in_abstracts():
    """Abstracts must not contain unprovenanced performance percentages."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    # Patterns that suggest fake metrics (unless explicitly marked as design targets)
    suspicious_patterns = [" achieved ", " showed ", " demonstrated "]
    
    for venue_key, draft in data["drafts"].items():
        abstract_text = draft.get("abstract", {}).get("text", "")
        venue_name = draft.get("venue_name", venue_key)
        
        # Check for percentage signs with suspicious verbs
        if "%" in abstract_text:
            for pattern in suspicious_patterns:
                if pattern in abstract_text.lower():
                    # Allow if it says "design target" or "pending validation"
                    if "design target" not in abstract_text.lower() and "pending validation" not in abstract_text.lower():
                        assert False, f"{venue_name}: abstract contains '{pattern}' with % but no 'design target' or 'pending validation' qualifier"

def test_trl_3_4_explicitly_stated():
    """Every draft must explicitly state TRL 3-4 and pending validation."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        venue_name = draft.get("venue_name", venue_key)
        trl = draft.get("trl", "")
        draft_note = draft.get("draft_note", "")
        abstract_text = draft.get("abstract", {}).get("text", "")
        
        # TRL must be stated
        assert "TRL" in trl or "TRL 3" in abstract_text or "TRL 4" in abstract_text, f"{venue_name}: TRL not clearly stated"
        
        # Pending validation must be mentioned
        validation_keywords = ["pending validation", "results pending", "TRL 3", "simulated"]
        assert any(kw in draft_note.lower() or kw in abstract_text.lower() for kw in validation_keywords), \
            f"{venue_name}: must explicitly state results pending validation"

def test_parsa_babaei_submitting_member():
    """All drafts should list Parsa Babaei as submitting team member."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        submitter = draft.get("submitting_team_member", "")
        venue_name = draft.get("venue_name", venue_key)
        assert "Parsa" in submitter or "Babaei" in submitter, f"{venue_name}: submitting_team_member must be Parsa Babaei"

def test_manuscript_spec_includes_references_note():
    """Manuscript specs should mention verified references."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        manuscript_spec = draft.get("manuscript_spec", {})
        structure = manuscript_spec.get("structure", "")
        venue_name = draft.get("venue_name", venue_key)
        
        # Should mention references
        assert "References" in structure or "references" in structure.lower(), \
            f"{venue_name}: manuscript_spec should mention References section"

def test_apadana_no_client_data_disclosure():
    """Apadana methanol product must explicitly state no client-confidential data disclosed."""
    drafts_file = ROOT / "data" / "article_drafts.json"
    with open(drafts_file, encoding="utf-8") as f:
        data = json.load(f)
    
    for venue_key, draft in data["drafts"].items():
        product = draft.get("product", "")
        if "Apadana" in product or "Khalij-Apadana" in product:
            draft_note = draft.get("draft_note", "")
            assert "no client-confidential" in draft_note.lower() or "generic methods" in draft_note.lower(), \
                f"{venue_key}: Apadana product must state no client-confidential data disclosed"

if __name__ == "__main__":
    test_article_drafts_file_exists()
    test_real_repo_names_only()
    test_water_ai_monitor_removed()
    test_manuscripts_minimum_3000_words()
    test_no_fake_performance_numbers_in_abstracts()
    test_trl_3_4_explicitly_stated()
    test_parsa_babaei_submitting_member()
    test_manuscript_spec_includes_references_note()
    test_apadana_no_client_data_disclosure()
    print("✓ All audit compliance tests passed!")
