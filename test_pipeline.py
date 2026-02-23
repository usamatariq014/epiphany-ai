#!/usr/bin/env python3
"""
Test script for epiphany-ai core functionality.
Tests database operations, word filtering, and Anki generation without EPUB/API.
"""
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import Database
from filter import get_rare_words, get_word_frequencies
from anki_generator import create_deck, validate_deck


def test_database():
    """Test database operations."""
    logger.info("Testing Database...")
    
    db = Database(Path("test_data/test.db"))
    
    # Test saving words
    test_words = [
        {'word': 'epiphany', 'frequency': 5},
        {'word': 'vocabulary', 'frequency': 12},
        {'word': 'algorithm', 'frequency': 3},
        {'word': 'beautiful', 'frequency': 25},
    ]
    
    inserted = db.save_pending_words(test_words, 'en')
    assert inserted == 4, f"Expected 4 inserted, got {inserted}"
    logger.info(f"✓ Saved {inserted} words")
    
    # Test getting pending words
    pending = db.get_pending_words('en')
    assert len(pending) == 4, f"Expected 4 pending, got {len(pending)}"
    logger.info(f"✓ Retrieved {len(pending)} pending words")
    
    # Test marking as enriched
    word_ids = [w['id'] for w in pending]
    definitions = {wid: f"Definition for word {wid}" for wid in word_ids}
    etymologies = {wid: f"Etymology for word {wid}" for wid in word_ids}
    examples = {wid: f"Example sentence for word {wid}" for wid in word_ids}
    
    updated = db.mark_words_enriched(word_ids, definitions, etymologies, examples)
    assert updated == 4, f"Expected 4 updated, got {updated}"
    logger.info(f"✓ Marked {updated} words as enriched")
    
    # Test getting enriched words
    enriched = db.get_all_words(status='enriched')
    assert len(enriched) == 4, f"Expected 4 enriched, got {len(enriched)}"
    assert all(w['definition'] for w in enriched), "All words should have definitions"
    logger.info(f"✓ Retrieved {len(enriched)} enriched words")
    
    # Test word count
    count = db.get_word_count(status='enriched')
    assert count == 4, f"Expected count 4, got {count}"
    logger.info(f"✓ Word count: {count}")
    
    db.close()
    logger.info("✓ Database tests passed!\n")
    return True


def test_filter():
    """Test word filtering."""
    logger.info("Testing Word Filter...")
    
    sample_text = """
    The algorithm was beautiful and efficient. 
    The algorithm solved the epiphany of computational complexity.
    Vocabulary building is essential for algorithmic thinking.
    Beautiful solutions require deep understanding.
    """
    
    # Test getting rare words
    rare_words = get_rare_words(sample_text, 'en', threshold=5)
    logger.info(f"Found {len(rare_words)} rare words")
    
    # Should find words that appear <= 5 times
    word_dict = dict(rare_words)
    assert 'epiphany' in word_dict, "Should find 'epiphany'"
    assert 'algorithmic' in word_dict, "Should find 'algorithmic'"
    logger.info(f"✓ Rare words: {[w for w, _ in rare_words]}")
    
    # Test word frequencies
    freqs = get_word_frequencies(sample_text, 'en')
    assert freqs['algorithm'] == 2, f"Expected 'algorithm' count 2, got {freqs.get('algorithm')}"
    assert freqs['beautiful'] == 2, f"Expected 'beautiful' count 2, got {freqs.get('beautiful')}"
    logger.info(f"✓ Frequencies: {freqs}")
    
    # Test stopwords are filtered
    rare_lower = [w.lower() for w, _ in rare_words]
    assert 'the' not in rare_lower, "Stopwords should be filtered"
    assert 'and' not in rare_lower, "Stopwords should be filtered"
    logger.info("✓ Stopwords properly filtered")
    
    logger.info("✓ Filter tests passed!\n")
    return True


def test_anki_generator():
    """Test Anki deck generation."""
    logger.info("Testing Anki Generator...")
    
    # Create test data
    test_words = [
        {
            'word': 'epiphany',
            'definition': 'A sudden realization or understanding',
            'etymology': 'From Greek epiphaneia, meaning appearance',
            'example_sentence': 'She had an epiphany about her career path.',
            'language': 'en'
        },
        {
            'word': 'algorithm',
            'definition': 'A step-by-step procedure for solving a problem',
            'etymology': 'From Latin algorismus, from al-Khwarizmi',
            'example_sentence': 'The sorting algorithm runs in O(n log n) time.',
            'language': 'en'
        },
    ]
    
    output_path = Path("test_data/test_deck.apkg")
    success = create_deck(test_words, output_path, deck_name="Test Deck")
    
    assert success, "Deck creation should succeed"
    logger.info(f"✓ Created deck at {output_path}")
    
    # Validate deck
    validation = validate_deck(output_path)
    assert validation['exists'], "Deck file should exist"
    assert validation['valid'], "Deck should be valid ZIP"
    logger.info(f"✓ Deck validation: {validation}")
    
    logger.info("✓ Anki Generator tests passed!\n")
    return True


def test_full_pipeline():
    """Test the full pipeline with mock data."""
    logger.info("Testing Full Pipeline (Mock)...")
    
    # 1. Simulate text extraction (we'd normally use epub_handler)
    sample_text = """
    The algorithm was beautiful and efficient. 
    The algorithm solved the epiphany of computational complexity.
    Vocabulary building is essential for algorithmic thinking.
    Beautiful solutions require deep understanding.
    """
    
    # 2. Filter words
    rare_words = get_rare_words(sample_text, 'en', threshold=5)
    logger.info(f"Filtered {len(rare_words)} rare words")
    
    # 3. Save to database
    db = Database(Path("test_data/pipeline_test.db"))
    words_to_save = [{'word': w, 'frequency': f} for w, f in rare_words]
    inserted = db.save_pending_words(words_to_save, 'en')
    logger.info(f"Saved {inserted} words to database")
    
    # 4. Get pending words (simulating what would be sent to AI)
    pending = db.get_pending_words('en')
    logger.info(f"Retrieved {len(pending)} pending words")
    
    # 5. Simulate AI enrichment (mock)
    word_ids = [w['id'] for w in pending]
    definitions = {wid: f"Mock definition for word {wid}" for wid in word_ids}
    etymologies = {wid: f"Mock etymology for word {wid}" for wid in word_ids}
    examples = {wid: f"Mock example for word {wid}" for wid in word_ids}
    
    updated = db.mark_words_enriched(word_ids, definitions, etymologies, examples)
    logger.info(f"Enriched {updated} words")
    
    # 6. Get enriched words
    enriched = db.get_all_words(status='enriched')
    logger.info(f"Retrieved {len(enriched)} enriched words")
    
    # 7. Export to Anki
    output_path = Path("test_data/pipeline_deck.apkg")
    success = create_deck(enriched, output_path, deck_name="Pipeline Test Deck")
    assert success, "Deck creation should succeed"
    logger.info(f"✓ Created deck with {len(enriched)} cards")
    
    db.close()
    logger.info("✓ Full pipeline test passed!\n")
    return True


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("EPIPHANY-AI TEST SUITE")
    logger.info("=" * 60 + "\n")
    
    # Create test_data directory
    Path("test_data").mkdir(exist_ok=True)
    
    tests = [
        test_database,
        test_filter,
        test_anki_generator,
        test_full_pipeline,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"RESULTS: {passed} passed, {failed} failed")
    logger.info("=" * 60)
    
    # Cleanup test files
    import shutil
    if Path("test_data").exists():
        shutil.rmtree("test_data")
        logger.info("Cleaned up test_data directory")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)