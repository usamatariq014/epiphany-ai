"""
Database layer for epiphany-ai.
Handles SQLite operations for vocabulary words.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for vocabulary words."""
    
    def __init__(self, db_path: Path = Path("data/epiphany.db")):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    language TEXT NOT NULL,
                    frequency INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    definition TEXT,
                    etymology TEXT,
                    example_sentence TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(word, language)
                )
            """)
            
            # Create indexes for faster queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_word_language ON words(word, language)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON words(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_language ON words(language)")
            
            logger.info(f"Database initialized at {self.db_path}")
    
    def save_pending_words(self, words: List[Dict[str, Any]], language: str) -> int:
        """
        Batch insert new words into the database.
        
        Args:
            words: List of dicts with 'word' and 'frequency' keys
            language: Language code (en, es, fr)
            
        Returns:
            Number of new words inserted (excluding duplicates)
        """
        inserted_count = 0
        
        with self._get_connection() as conn:
            for word_data in words:
                word = word_data['word'].strip().lower()
                frequency = word_data['frequency']
                
                try:
                    # Insert or update if exists but was previously deleted/ignored
                    cursor = conn.execute("""
                        INSERT OR IGNORE INTO words (word, language, frequency, status, created_at, updated_at)
                        VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (word, language, frequency))
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                        
                except sqlite3.Error as e:
                    logger.error(f"Error inserting word '{word}': {e}")
                    continue
        
        logger.info(f"Saved {inserted_count} new pending words for language '{language}'")
        return inserted_count
    
    def get_pending_words(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch words that await AI enrichment.
        
        Args:
            language: Optional language filter
            
        Returns:
            List of word dictionaries with id, word, language, frequency
        """
        with self._get_connection() as conn:
            query = """
                SELECT id, word, language, frequency
                FROM words
                WHERE status = 'pending'
            """
            params = []
            
            if language:
                query += " AND language = ?"
                params.append(language)
            
            query += " ORDER BY frequency DESC"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def mark_words_enriched(
        self, 
        word_ids: List[int], 
        definitions: Dict[int, str],
        etymologies: Dict[int, str],
        example_sentences: Dict[int, str]
    ) -> int:
        """
        Update words with AI-enriched data and mark as enriched.
        
        Args:
            word_ids: List of word IDs to update
            definitions: Mapping of word_id -> definition
            etymologies: Mapping of word_id -> etymology
            example_sentences: Mapping of word_id -> example sentence
            
        Returns:
            Number of words successfully updated
        """
        updated_count = 0
        
        with self._get_connection() as conn:
            for word_id in word_ids:
                definition = definitions.get(word_id)
                etymology = etymologies.get(word_id)
                example = example_sentences.get(word_id)
                
                try:
                    cursor = conn.execute("""
                        UPDATE words
                        SET status = 'enriched',
                            definition = ?,
                            etymology = ?,
                            example_sentence = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND status = 'pending'
                    """, (definition, etymology, example, word_id))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                        
                except sqlite3.Error as e:
                    logger.error(f"Error updating word ID {word_id}: {e}")
                    continue
        
        logger.info(f"Marked {updated_count} words as enriched")
        return updated_count
    
    def get_all_words(
        self, 
        language: Optional[str] = None, 
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve words from database with optional filters.
        
        Args:
            language: Optional language filter
            status: Optional status filter ('pending', 'enriched')
            
        Returns:
            List of complete word dictionaries
        """
        with self._get_connection() as conn:
            query = """
                SELECT id, word, language, frequency, status, 
                       definition, etymology, example_sentence,
                       created_at, updated_at
                FROM words
            """
            params = []
            
            if language:
                query += " WHERE language = ?"
                params.append(language)
            
            if status:
                if params:
                    query += " AND status = ?"
                else:
                    query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY frequency DESC"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_word_count(self, language: Optional[str] = None, status: Optional[str] = None) -> int:
        """Get count of words matching filters."""
        with self._get_connection() as conn:
            query = "SELECT COUNT(*) FROM words"
            params = []
            
            if language:
                query += " WHERE language = ?"
                params.append(language)
            if status:
                if params:
                    query += " AND status = ?"
                else:
                    query += " WHERE status = ?"
                params.append(status)
            
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def delete_word(self, word: str, language: str) -> bool:
        """
        Delete a specific word.
        
        Returns:
            True if word was deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM words WHERE word = ? AND language = ?",
                (word.lower(), language)
            )
            return cursor.rowcount > 0
    
    def reset_status(self, language: Optional[str] = None, to_status: str = 'pending') -> int:
        """
        Reset word statuses (e.g., to re-run AI enrichment).
        
        Returns:
            Number of words reset
        """
        with self._get_connection() as conn:
            query = "UPDATE words SET status = ?, updated_at = CURRENT_TIMESTAMP"
            params = [to_status]
            
            if language:
                query += " WHERE language = ?"
                params.append(language)
            
            cursor = conn.execute(query, params)
            return cursor.rowcount
    
    def close(self):
        """Close database connection (not needed with context manager, but available)."""
        pass