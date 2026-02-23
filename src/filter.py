"""
Word filter for epiphany-ai.
Identifies rare words from text based on frequency thresholds.
"""
import logging
import re
from collections import Counter
from typing import List, Tuple, Dict, Set
from pathlib import Path

logger = logging.getLogger(__name__)

# Built-in stopwords for supported languages
# These are common words that learners typically already know
STOPWORDS = {
    'en': {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'its', 'our', 'their', 'this', 'that', 'these', 'those',
        'here', 'there', 'where', 'when', 'why', 'how', 'what', 'which', 'who', 'whom',
        'not', 'no', 'yes', 'so', 'if', 'then', 'than', 'as', 'up', 'down', 'out', 'off',
        'over', 'under', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'only', 'own', 'same', 'too', 'very', 'just', 'now', 'then',
        'about', 'above', 'after', 'against', 'between', 'into', 'through', 'during',
        'before', 'after', 'from', 'to', 'into', 'toward', 'through', 'past', 'upon',
        'about', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'shall', 'should',
        'may', 'might', 'must', 'can', 'could', 'one', 'ones', 'two', 'three', 'four',
        'five', 'six', 'seven', 'eight', 'nine', 'ten', 'first', 'second', 'third',
        'mr', 'mrs', 'ms', 'dr', 'prof', 'etc', 'vs', 'etc.', 'eg', 'i.e', 'et al',
    },
    'es': {
        'a', 'al', 'de', 'del', 'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'y', 'o', 'pero', 'si', 'no', 'que', 'porque', 'por', 'para', 'con', 'en',
        'es', 'son', 'fue', 'fueron', 'ser', 'estado', 'estar', 'tener', 'tengo',
        'tienes', 'tiene', 'tenemos', 'tienen', 'haber', 'haya', 'hago', 'haces',
        'hacemos', 'hacen', 'ir', 'voy', 'vas', 'va', 'vamos', 'van', 'poder',
        'puedo', 'puedes', 'puede', 'podemos', 'pueden', 'querer', 'quiero',
        'quieres', 'quiere', 'queremos', 'quieren', 'decir', 'digo', 'dices',
        'dice', 'decimos', 'dicen', 'ver', 'veo', 'ves', 've', 'vemos', 'ven',
        'dar', 'doy', 'das', 'da', 'damos', 'dan', 'saber', 'sé', 'sabes',
        'sabe', 'sabemos', 'saben', 'conocer', 'conozco', 'conoces', 'conoce',
        'conocemos', 'conocen', 'yo', 'tú', 'él', 'ella', 'nosotros', 'nosotras',
        'vosotros', 'vosotras', 'ellos', 'ellas', 'mi', 'tu', 'su', 'nuestro',
        'nuestra', 'vuestro', 'vuestra', 'este', 'esta', 'estos', 'estas',
        'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas',
        'cual', 'cuya', 'cuyo', 'cuyos', 'cuyas', 'donde', 'cuando', 'como',
        'que', 'quien', 'cuyo', 'cuanto', 'cuanta', 'cuantos', 'cuantas',
        'todo', 'toda', 'todos', 'todas', 'mucho', 'mucha', 'muchos', 'muchas',
        'poco', 'poca', 'pocos', 'pocas', 'grande', 'grandes', 'pequeño', 'pequeña',
        'pequeños', 'pequeñas', 'nuevo', 'nueva', 'nuevos', 'nuevas', 'viejo', 'vieja',
        'viejos', 'viejas', 'bueno', 'buena', 'buenos', 'buenas', 'malo', 'mala',
        'malos', 'malas', 'primero', 'segundo', 'tercero', 'último', 'mismo', 'misma',
        'mismos', 'mismas', 'otro', 'otra', 'otros', 'otras', 'tal', 'cual', 'cuales',
        'tan', 'tanto', 'tanta', 'tantos', 'tantas', 'más', 'menos', 'algo', 'nada',
        'alguien', 'nadie', 'quien', 'quienes', 'donde', 'donde', 'cuando', 'cual',
        'cuales', 'cuya', 'cuyas', 'cuyo', 'cuyos', 'cuyas', 'aunque', 'porque',
        'pues', 'si', 'como', 'según', 'sin', 'sobre', 'entre', 'durante', 'hasta',
        'desde', 'antes', 'después', 'aquí', 'allí', 'ahí', 'allá', 'cerca', 'lejos',
        'arriba', 'abajo', 'dentro', 'fuera', 'delante', 'detrás', 'izquierda',
        'derecha', 'hoy', 'ayer', 'mañana', 'ahora', 'luego', 'antes', 'después',
        'siempre', 'nunca', 'a veces', 'muchas veces', 'pocas veces', 'bien', 'mal',
        'regular', 'muy', 'bastante', 'poco', 'demasiado', 'tan', 'tanto', 'casi',
        'cerca', 'lejos', 'junto', 'separado', 'uno', 'dos', 'tres', 'cuatro', 'cinco',
        'seis', 'siete', 'ocho', 'nueve', 'diez', 'cien', 'mil', 'millón',
    },
    'fr': {
        'le', 'la', 'les', 'des', 'du', 'de', 'un', 'une', 'des', 'et', 'ou', 'mais',
        'donc', 'or', 'ni', 'car', 'parce', 'que', 'qui', 'quoi', 'dont', 'où',
        'quand', 'comment', 'pourquoi', 'combien', 'quel', 'quelle', 'quels', 'quelles',
        'ce', 'cette', 'ces', 'celui', 'celle', 'ceux', 'celles', 'mon', 'ma', 'mes',
        'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'notre', 'nos', 'votre', 'vos',
        'leur', 'leurs', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
        'me', 'te', 'lui', 'se', 'nous', 'vous', 'leur', 'en', 'y', 'être', 'avoir',
        'faire', 'dire', 'aller', 'voir', 'savoir', 'pouvoir', 'vouloir', 'venir',
        'devoir', 'prendre', 'donner', 'parler', 'aimer', 'penser', 'comprendre',
        'appeler', 'trouver', 'mettre', 'dormir', 'manger', 'boire', 'travailler',
        'jouer', 'lire', 'écrire', 'chanter', 'danser', 'marcher', 'courir', 'sauter',
        'voler', 'nager', 'je', 'tu', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
        'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'notre', 'nos',
        'votre', 'vos', 'leur', 'leurs', 'ce', 'cet', 'cette', 'ces', 'tel', 'telle',
        'tels', 'telles', 'certains', 'certaines', 'plusieurs', 'quelque', 'quelques',
        'un', 'une', 'des', 'aucun', 'aucune', 'aucuns', 'aucunes', 'tout', 'toute',
        'tous', 'toutes', 'beaucoup', 'peu', 'trop', 'assez', 'moins', 'plus', 'très',
        'trop', 'assez', 'un peu', 'beaucoup', 'tant', 'tellement', 'aussi', 'encore',
        'déjà', 'bientôt', 'tôt', 'tard', 'maintenant', 'alors', 'aujourd\'hui',
        'hier', 'demain', 'cependant', 'mais', 'ou', 'donc', 'ni', 'car', 'parce',
        'que', 'puisque', 'comme', 'si', 'quand', 'lorsque', 'tandis', 'pendant',
        'durant', 'avant', 'après', 'depuis', 'jusqu\'à', 'vers', 'chez', 'dans',
        'en', 'sur', 'sous', 'au', 'aux', 'à', 'aux', 'par', 'pour', 'avec', 'sans',
        'sous', 'sur', 'dans', 'de', 'des', 'du', 'en', 'au', 'aux', 'vers', 'chez',
        'ici', 'là', 'là-bas', 'partout', 'ailleurs', 'dedans', 'dehors', 'dessus',
        'dessous', 'près', 'loin', 'devant', 'derrière', 'à gauche', 'à droite',
        'haut', 'bas', 'premier', 'deuxième', 'troisième', 'dernier', 'même', 'tel',
        'quel', 'autre', 'différent', 'vrai', 'faux', 'bon', 'mauvais', 'jeune', 'vieux',
        'chaud', 'froid', 'gros', 'mince', 'long', 'court', 'grand', 'petit', 'nouveau',
        'ancien', 'beau', 'laid', 'clair', 'sombre', 'droit', 'tordu', 'plein', 'vide',
        'vif', 'lent', 'rapide', 'fort', 'faible', 'dur', 'mol', 'cher', 'bon marché',
        'propre', 'sale', 'sec', 'humide', 'chaud', 'froid', 'brûlant', 'gelé',
    }
}

# Pre-compile regex patterns for performance
WORD_PATTERN = re.compile(r"\b[a-zA-Zà-ÿÀ-ÿ'-]+\b")  # Includes accented characters
CONTRACTED_PATTERN = re.compile(r"\b(n't|'ll|'re|'ve|'d|'m|'s)\b", re.IGNORECASE)


def get_rare_words(text: str, language: str = 'en', threshold: int = 50) -> List[Tuple[str, int]]:
    """
    Extract rare words from text based on frequency threshold.
    
    Args:
        text: Input text to analyze
        language: Language code (en, es, fr)
        threshold: Frequency threshold - words appearing <= threshold times are considered rare
                   Lower = rarer words (default 50)
        
    Returns:
        List of tuples (word, frequency) sorted by frequency ascending (rarest first)
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to get_rare_words")
        return []
    
    # Validate language
    if language not in STOPWORDS:
        logger.warning(f"Language '{language}' not supported. Using English stopwords.")
        language = 'en'
    
    # Tokenize
    words = _tokenize(text, language)
    
    if not words:
        logger.warning("No words found after tokenization")
        return []
    
    # Count frequencies
    word_counts = Counter(words)
    
    # Filter out stopwords and very short words
    stopwords = STOPWORDS[language]
    filtered_counts = {
        word: count 
        for word, count in word_counts.items() 
        if word not in stopwords and len(word) > 1  # Exclude single characters
    }
    
    # Apply threshold: keep words with frequency <= threshold
    rare_words = [
        (word, count) 
        for word, count in filtered_counts.items() 
        if count <= threshold
    ]
    
    # Sort by frequency ascending (rarest first), then alphabetically
    rare_words.sort(key=lambda x: (x[1], x[0]))
    
    logger.info(f"Found {len(rare_words)} rare words from {len(filtered_counts)} unique non-stopwords")
    return rare_words


def _tokenize(text: str, language: str) -> List[str]:
    """
    Tokenize text into words, language-aware.
    
    Args:
        text: Input text
        language: Language code
        
    Returns:
        List of lowercase word tokens
    """
    # Convert to lowercase
    text_lower = text.lower()
    
    # Find all word tokens (including accented characters and hyphens)
    words = WORD_PATTERN.findall(text_lower)
    
    # Normalize: strip quotes/hyphens at edges, filter empty
    normalized = []
    for word in words:
        # Strip leading/trailing quotes and hyphens
        word = word.strip("'\"-")
        if word and len(word) > 0:
            normalized.append(word)
    
    return normalized


def get_word_frequencies(text: str, language: str = 'en') -> Dict[str, int]:
    """
    Calculate frequency distribution of all non-stopwords.
    
    Args:
        text: Input text
        language: Language code
        
    Returns:
        Dictionary mapping words to their frequencies
    """
    words = _tokenize(text, language)
    word_counts = Counter(words)
    
    # Filter stopwords
    stopwords = STOPWORDS.get(language, STOPWORDS['en'])
    filtered = {word: count for word, count in word_counts.items() if word not in stopwords}
    
    return dict(filtered)


def get_stopwords(language: str = 'en') -> Set[str]:
    """
    Get the set of stopwords for a given language.
    
    Args:
        language: Language code
        
    Returns:
        Set of stopword strings
    """
    return STOPWORDS.get(language, STOPWORDS['en'])


def add_custom_stopwords(language: str, words: List[str]):
    """
    Add custom stopwords to a language's stopword set.
    
    Args:
        language: Language code
        words: List of words to add as stopwords
    """
    if language not in STOPWORDS:
        STOPWORDS[language] = set()
    
    STOPWORDS[language].update(word.lower() for word in words)
    logger.info(f"Added {len(words)} custom stopwords to language '{language}'")


def get_statistics(text: str, language: str = 'en') -> Dict[str, int]:
    """
    Get text statistics.
    
    Returns:
        Dictionary with total_words, unique_words, stopwords_removed, etc.
    """
    words = _tokenize(text, language)
    total_words = len(words)
    unique_words = len(set(words))
    
    stopwords = STOPWORDS.get(language, STOPWORDS['en'])
    stopword_count = sum(1 for w in words if w in stopwords)
    
    return {
        'total_words': total_words,
        'unique_words': unique_words,
        'stopwords_removed': stopword_count,
        'content_words': total_words - stopword_count,
    }