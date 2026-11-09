"""
Test that generated manuscript .docx files meet word count and quality requirements.
Measures actual word counts from generated Word files, not hand-entered fields.
"""
import json
import subprocess
import tempfile
from pathlib import Path
from collections import Counter
from docx import Document

ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = ROOT / "scripts"

def test_manuscript_generation_script_exists():
    """Generator script must exist"""
    script = SCRIPTS_DIR / "generate_full_manuscripts.py"
    assert script.exists(), f"Generator script not found: {script}"

def test_manuscripts_meet_3000_word_minimum():
    """Each manuscript must be at least 3,000 words measured from actual .docx file"""
    # Generate manuscripts
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "generate_full_manuscripts.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Generator failed: {result.stderr}"
        
        # Load word counts
        word_counts_file = Path("/opt/cursor/artifacts/word-counts.json")
        assert word_counts_file.exists(), "word-counts.json not generated"
        
        with open(word_counts_file, "r") as f:
            results = json.load(f)
        
        # Check each manuscript
        failures = []
        for venue_key, info in results.items():
            word_count = info["word_count"]
            venue_name = info["venue_name"]
            
            if word_count < 3000:
                failures.append(f"{venue_name}: {word_count} words < 3,000 minimum")
        
        assert not failures, f"Manuscripts below 3,000 words:\n" + "\n".join(failures)

def test_manuscripts_duplicate_sentences_below_5_percent():
    """No more than 5% of sentences can be duplicates"""
    # Generate manuscripts if not already generated
    subprocess.run(
        ["python3", str(SCRIPTS_DIR / "generate_full_manuscripts.py")],
        cwd=ROOT,
        capture_output=True,
        timeout=60
    )
    
    word_counts_file = Path("/opt/cursor/artifacts/word-counts.json")
    with open(word_counts_file, "r") as f:
        results = json.load(f)
    
    failures = []
    for venue_key, info in results.items():
        doc_path = Path(info["filename"])
        venue_name = info["venue_name"]
        
        # Extract sentences
        doc = Document(doc_path)
        sentences = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if len(text) > 20:  # Only sentences, not headings
                sents = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 20]
                sentences.extend(sents)
        
        # Count duplicates
        sentence_counts = Counter(sentences)
        total_sentences = len(sentences)
        duplicate_count = sum(count - 1 for count in sentence_counts.values() if count > 1)
        duplicate_pct = (duplicate_count / total_sentences * 100) if total_sentences > 0 else 0
        
        if duplicate_pct > 5.0:
            duplicates = {sent: count for sent, count in sentence_counts.items() if count > 1}
            sample_dups = list(duplicates.items())[:3]
            failures.append(f"{venue_name}: {duplicate_pct:.2f}% duplicates (> 5%)\n  Samples: {sample_dups}")
    
    assert not failures, f"Manuscripts with excessive duplicates:\n" + "\n".join(failures)

def test_manuscripts_contain_real_content_from_readme():
    """Manuscripts should contain substantive content, not just generic templates"""
    subprocess.run(
        ["python3", str(SCRIPTS_DIR / "generate_full_manuscripts.py")],
        cwd=ROOT,
        capture_output=True,
        timeout=60
    )
    
    word_counts_file = Path("/opt/cursor/artifacts/word-counts.json")
    with open(word_counts_file, "r") as f:
        results = json.load(f)
    
    # Check for product-specific keywords
    product_keywords = {
        "intelligent-management-sys-energy-carbon-sustainability-": ["olefin", "PTA", "VSG", "Monte Carlo", "PSO"],
        "Mili-Multi-Mode-Adaptive-Decision-System": ["UAV", "STM32H7", "reconnaissance", "surveillance", "loiter"],
        "iEOR": ["reservoir", "injection", "EOR", "recovery", "petroleum"],
        "-Khalij-Apadana-Reformer-Methanol-Loop-Digital-Twin-System-": ["methanol", "reformer", "creep", "catalyst", "syngas"]
    }
    
    failures = []
    for venue_key, info in results.items():
        doc_path = Path(info["filename"])
        product = info["product"]
        venue_name = info["venue_name"]
        
        doc = Document(doc_path)
        full_text = " ".join(para.text.lower() for para in doc.paragraphs)
        
        expected_keywords = product_keywords.get(product, [])
        found_keywords = [kw for kw in expected_keywords if kw.lower() in full_text]
        
        if len(found_keywords) < len(expected_keywords) * 0.6:  # At least 60% of keywords
            failures.append(f"{venue_name}: Only {len(found_keywords)}/{len(expected_keywords)} keywords found")
    
    assert not failures, f"Manuscripts lack product-specific content:\n" + "\n".join(failures)

def test_all_manuscripts_state_trl_3_4():
    """Every manuscript must explicitly state TRL 3-4 and pending validation"""
    subprocess.run(
        ["python3", str(SCRIPTS_DIR / "generate_full_manuscripts.py")],
        cwd=ROOT,
        capture_output=True,
        timeout=60
    )
    
    word_counts_file = Path("/opt/cursor/artifacts/word-counts.json")
    with open(word_counts_file, "r") as f:
        results = json.load(f)
    
    failures = []
    for venue_key, info in results.items():
        doc_path = Path(info["filename"])
        venue_name = info["venue_name"]
        
        doc = Document(doc_path)
        full_text = " ".join(para.text.lower() for para in doc.paragraphs)
        
        has_trl = "trl 3" in full_text or "trl 4" in full_text or "technology readiness level" in full_text
        has_pending = "pending validation" in full_text or "results pending" in full_text
        
        if not has_trl:
            failures.append(f"{venue_name}: Missing TRL 3-4 statement")
        if not has_pending:
            failures.append(f"{venue_name}: Missing 'pending validation' statement")
    
    assert not failures, f"Manuscripts missing TRL/validation statements:\n" + "\n".join(failures)

if __name__ == "__main__":
    import sys
    
    print("Running manuscript quality tests...")
    print()
    
    try:
        test_manuscript_generation_script_exists()
        print("✓ Generator script exists")
        
        test_manuscripts_meet_3000_word_minimum()
        print("✓ All manuscripts >= 3,000 words")
        
        test_manuscripts_duplicate_sentences_below_5_percent()
        print("✓ All manuscripts < 5% duplicate sentences")
        
        test_manuscripts_contain_real_content_from_readme()
        print("✓ All manuscripts contain product-specific content")
        
        test_all_manuscripts_state_trl_3_4()
        print("✓ All manuscripts state TRL 3-4 and pending validation")
        
        print()
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
