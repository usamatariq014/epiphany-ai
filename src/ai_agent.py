"""
AI Agent for epiphany-ai.
Enriches vocabulary words using OpenRouter API.
"""
import logging
import os
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI, RateLimitError, APIConnectionError, APIError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AIAgent:
    """AI agent for enriching vocabulary words via OpenRouter."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-3.5-turbo"):
        """
        Initialize AI agent.
        
        Args:
            api_key: OpenRouter API key (if None, reads from OPENROUTER_API_KEY env var)
            model: Model to use (default: openai/gpt-3.5-turbo)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        logger.info(f"AI Agent initialized with model: {model}")
    
    def enrich_words(
        self, 
        words: List[Dict[str, Any]], 
        language: str = 'en',
        batch_size: int = 10
    ) -> Dict[int, Dict[str, str]]:
        """
        Enrich a list of words with definitions, etymology, and example sentences.
        
        Args:
            words: List of word dictionaries with 'id' and 'word' keys
            language: Language code (en, es, fr)
            batch_size: Number of words to process per API call
            
        Returns:
            Dictionary mapping word_id to enrichment data:
            {
                word_id: {
                    'definition': str,
                    'etymology': str,
                    'example_sentence': str
                }
            }
        """
        if not words:
            logger.warning("No words provided for enrichment")
            return {}
        
        logger.info(f"Enriching {len(words)} words in batches of {batch_size}")
        
        results = {}
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            batch_results = self._enrich_batch(batch, language)
            results.update(batch_results)
            
            # Rate limiting: small delay between batches
            if i + batch_size < len(words):
                time.sleep(1)
        
        logger.info(f"Successfully enriched {len(results)} words")
        return results
    
    def _enrich_batch(
        self, 
        batch: List[Dict[str, Any]], 
        language: str
    ) -> Dict[int, Dict[str, str]]:
        """
        Enrich a single batch of words.
        
        Args:
            batch: List of word dictionaries
            language: Language code
            
        Returns:
            Dictionary mapping word_id to enrichment data
        """
        # Build prompt
        word_list = [w['word'] for w in batch]
        prompt = self._build_prompt(word_list, language)
        
        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful linguist and language teacher. Provide clear, concise, and accurate information about words."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500,
                top_p=1,
                stream=False
            )
            
            # Parse response
            content = response.choices[0].message.content
            results = self._parse_response(content, batch)
            
            return results
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            # Wait and retry once
            time.sleep(5)
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful linguist and language teacher."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )
                content = response.choices[0].message.content
                results = self._parse_response(content, batch)
                return results
            except Exception as retry_e:
                logger.error(f"Retry failed: {retry_e}")
                return {}
                
        except APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            return {}
            
        except APIError as e:
            logger.error(f"API error: {e}")
            return {}
            
        except Exception as e:
            logger.error(f"Unexpected error during enrichment: {e}")
            return {}
    
    def _build_prompt(self, words: List[str], language: str) -> str:
        """
        Build prompt for word enrichment.
        
        Args:
            words: List of words to enrich
            language: Language code
            
        Returns:
            Formatted prompt string
        """
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French'
        }
        lang_name = language_names.get(language, 'English')
        
        prompt = f"""For each of the following {lang_name} words, provide:
1. A clear definition (1-2 sentences)
2. The etymology (word origin, root language, history)
3. An example sentence using the word naturally

Format your response EXACTLY as follows for each word:

Word: [word]
Definition: [definition]
Etymology: [etymology]
Example: [example sentence]

Separate each word's information with a blank line.

Words to enrich:
"""
        for word in words:
            prompt += f"- {word}\n"
        
        return prompt
    
    def _parse_response(
        self, 
        content: str, 
        batch: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, str]]:
        """
        Parse API response into structured data.
        
        Args:
            content: Raw API response text
            batch: Original batch of words with IDs
            
        Returns:
            Dictionary mapping word_id to enrichment data
        """
        results = {}
        
        # Create mapping of word to id
        word_to_id = {w['word'].lower(): w['id'] for w in batch}
        
        # Split response by double newlines (separator between words)
        sections = content.strip().split('\n\n')
        
        for section in sections:
            if not section.strip():
                continue
            
            # Parse section
            lines = section.strip().split('\n')
            word_data = {'definition': '', 'etymology': '', 'example_sentence': ''}
            current_word = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Word:'):
                    current_word = line[5:].strip().lower()
                elif line.startswith('Definition:'):
                    word_data['definition'] = line[11:].strip()
                elif line.startswith('Etymology:'):
                    word_data['etymology'] = line[10:].strip()
                elif line.startswith('Example:'):
                    word_data['example_sentence'] = line[8:].strip()
            
            if current_word and current_word in word_to_id:
                word_id = word_to_id[current_word]
                # Only add if we have at least a definition
                if word_data['definition']:
                    results[word_id] = word_data
        
        # Check if we missed any words
        if len(results) < len(batch):
            logger.warning(f"Only parsed {len(results)}/{len(batch)} words from response")
        
        return results


def enrich_words(
    words: List[Dict[str, Any]], 
    language: str = 'en',
    api_key: Optional[str] = None,
    model: str = "openai/gpt-3.5-turbo"
) -> Dict[int, Dict[str, str]]:
    """
    Convenience function to enrich words without managing agent instance.
    
    Args:
        words: List of word dictionaries with 'id' and 'word' keys
        language: Language code
        api_key: OpenRouter API key
        model: Model to use
        
    Returns:
        Dictionary mapping word_id to enrichment data
    """
    agent = AIAgent(api_key=api_key, model=model)
    return agent.enrich_words(words, language)