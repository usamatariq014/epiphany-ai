"""
Anki deck generator for epiphany-ai.
Creates .apkg files from enriched vocabulary words.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
import genanki

logger = logging.getLogger(__name__)


# Anki card model (template)
# This defines the fields and styling for our vocabulary cards
VOCAB_MODEL = genanki.Model(
    1607392319,  # Random model ID (must be unique)
    'Epiphany Vocabulary',
    fields=[
        {'name': 'Word'},
        {'name': 'Definition'},
        {'name': 'Etymology'},
        {'name': 'Example'},
    ],
    templates=[
        {
            'name': 'Card 1',
            'qfmt': '''
<div style="font-family: Arial; font-size: 24px; text-align: center; padding: 20px;">
<b>{{Word}}</b>
</div>
            ''',
            'afmt': '''
<div style="font-family: Arial; font-size: 18px; padding: 20px;">
<b>{{Word}}</b>

<hr>

<div style="color: #2c3e50;">
<p><b>Definition:</b><br>{{Definition}}</p>

<p><b>Etymology:</b><br>{{Etymology}}</p>

<p><b>Example:</b><br>{{Example}}</p>
</div>
            ''',
        },
    ],
    css='''
.card {
 font-family: Arial;
 font-size: 18px;
 text-align: left;
 color: black;
 background-color: white;
}
    '''
)


def create_deck(
    words: List[Dict[str, Any]], 
    output_path: Path = Path("output/deck.apkg"),
    deck_name: str = "Epiphany Vocabulary"
) -> bool:
    """
    Create an Anki deck from a list of enriched words.
    
    Args:
        words: List of word dictionaries with keys:
               word, definition, etymology, example_sentence, language
        output_path: Path where .apkg file will be saved
        deck_name: Name of the Anki deck
        
    Returns:
        True if deck created successfully, False otherwise
    """
    if not words:
        logger.warning("No words provided for deck creation")
        return False
    
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create deck with unique ID
        deck = genanki.Deck(
            2059400110,  # Random deck ID (must be unique)
            deck_name
        )
        
        # Add notes for each word
        added_count = 0
        for word_data in words:
            # Skip words without essential data
            if not word_data.get('word') or not word_data.get('definition'):
                logger.warning(f"Skipping word '{word_data.get('word')}' - missing required fields")
                continue
            
            # Prepare note fields
            note = genanki.Note(
                model=VOCAB_MODEL,
                fields=[
                    word_data.get('word', ''),
                    word_data.get('definition', ''),
                    word_data.get('etymology', ''),
                    word_data.get('example_sentence', '')
                ]
            )
            
            deck.add_note(note)
            added_count += 1
        
        if added_count == 0:
            logger.warning("No valid words to create deck")
            return False
        
        # Generate the .apkg file
        package = genanki.Package(deck)
        package.write_to_file(str(output_path))
        
        logger.info(f"Created Anki deck with {added_count} cards at {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating Anki deck: {e}")
        return False


def create_deck_from_database(
    db,
    language: str = None,
    output_path: Path = Path("output/deck.apkg"),
    deck_name: str = None
) -> bool:
    """
    Convenience function: create deck directly from database.
    
    Args:
        db: Database instance
        language: Optional language filter
        output_path: Output file path
        deck_name: Deck name (defaults to "Epiphany Vocabulary [lang]")
        
    Returns:
        True if successful
    """
    # Fetch enriched words from database
    words = db.get_all_words(language=language, status='enriched')
    
    if not words:
        logger.warning(f"No enriched words found in database for language '{language}'")
        return False
    
    # Set deck name if not provided
    if not deck_name:
        lang_suffix = f" ({language})" if language else ""
        deck_name = f"Epiphany Vocabulary{lang_suffix}"
    
    return create_deck(words, output_path, deck_name)


def validate_deck(output_path: Path) -> Dict[str, Any]:
    """
    Validate a created deck file.
    
    Args:
        output_path: Path to .apkg file
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'exists': False,
        'size_bytes': 0,
        'valid': False,
        'error': None
    }
    
    try:
        if not output_path.exists():
            results['error'] = "File does not exist"
            return results
        
        results['exists'] = True
        results['size_bytes'] = output_path.stat().st_size
        
        # Basic sanity check: .apkg files are ZIP archives
        import zipfile
        if zipfile.is_zipfile(str(output_path)):
            results['valid'] = True
        else:
            results['error'] = "File is not a valid ZIP archive"
            
    except Exception as e:
        results['error'] = str(e)
    
    return results