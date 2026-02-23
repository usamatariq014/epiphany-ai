"""
EPUB handler for epiphany-ai.
Extracts and cleans text from EPUB ebooks.
"""
import logging
from pathlib import Path
from typing import List, Optional
from ebooklib import epub
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def read_epub(epub_path: Path) -> str:
    """
    Extract all text content from an EPUB file.
    
    Args:
        epub_path: Path to the .epub file
        
    Returns:
        Concatenated plain text from all chapters
        
    Raises:
        FileNotFoundError: If EPUB file doesn't exist
        Exception: For other EPUB parsing errors
    """
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    try:
        logger.info(f"Reading EPUB: {epub_path}")
        book = epub.read_epub(str(epub_path))
        
        # Extract text from all items
        text_parts = []
        
        # Get all items that are documents (chapters)
        for item in book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                # item.get_content() returns bytes, decode to string
                content = item.get_content().decode('utf-8', errors='ignore')
                cleaned_text = _clean_html_content(content)
                if cleaned_text.strip():
                    text_parts.append(cleaned_text)
        
        full_text = '\n\n'.join(text_parts)
        logger.info(f"Extracted {len(full_text)} characters from {len(text_parts)} chapters")
        
        return full_text
        
    except Exception as e:
        logger.error(f"Error reading EPUB {epub_path}: {e}")
        raise


def _clean_html_content(html_content: str) -> str:
    """
    Remove HTML tags and clean text content.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Cleaned plain text
    """
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link", "head"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive newlines
        text = '\n'.join(line for line in text.split('\n') if line.strip())
        
        return text
        
    except Exception as e:
        logger.warning(f"Error cleaning HTML content: {e}")
        # Fallback: return original content as plain text
        return html_content


def get_chapter_count(epub_path: Path) -> int:
    """
    Get the number of chapters/documents in the EPUB.
    
    Args:
        epub_path: Path to the .epub file
        
    Returns:
        Number of document items
    """
    try:
        book = epub.read_epub(str(epub_path))
        count = sum(1 for item in book.get_items() if item.get_type() == epub.ITEM_DOCUMENT)
        return count
    except Exception as e:
        logger.error(f"Error counting chapters: {e}")
        return 0


def get_metadata(epub_path: Path) -> dict:
    """
    Extract metadata from EPUB.
    
    Args:
        epub_path: Path to the .epub file
        
    Returns:
        Dictionary with title, author, language, etc.
    """
    try:
        book = epub.read_epub(str(epub_path))
        metadata = {}
        
        # Get title
        title = book.get_metadata('DC', 'title')
        if title:
            metadata['title'] = title[0][0]
        
        # Get author
        creator = book.get_metadata('DC', 'creator')
        if creator:
            metadata['author'] = creator[0][0]
        
        # Get language
        language = book.get_metadata('DC', 'language')
        if language:
            metadata['language'] = language[0][0]
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return {}