# epiphany-ai

**You finally understand a word you've seen a dozen times.**

A CLI tool that transforms EPUB ebooks into personalized Anki vocabulary decks using AI enrichment.

## Features

- 📚 **Extract vocabulary** from any EPUB file
- 🔍 **Filter rare words** by frequency threshold (customizable per language)
- 🤖 **AI-powered enrichment** via OpenRouter (definitions, etymology, examples)
- 🃏 **Export to Anki** (.apkg) for spaced repetition learning
- 🌍 **Multi-language support** (English, Spanish, French)
- 💻 **Beautiful CLI** with progress indicators and rich output

## Quick Start

### Installation

1. **Clone and setup:**
```bash
cd epiphany-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

2. **Set up OpenRouter API key:**
```bash
export OPENROUTER_API_KEY="your-api-key-here"
# Or create a .env file in the project root:
# OPENROUTER_API_KEY=your-api-key-here
```

3. **Install dependencies:**
```bash
pip install typer rich ebooklib beautifulsoup4 nltk sqlalchemy genanki openai python-dotenv pydantic
```

### Usage

#### 1. Extract vocabulary from an EPUB

```bash
epiphany extract path/to/book.epub --language en --threshold 30
```

This will:
- Parse the EPUB and extract all text
- Filter words that appear ≤ 30 times (rarer words)
- Save pending words to the database (`data/epiphany.db`)
- Optionally enrich with AI (prompts for confirmation with cost estimate)

#### 2. Practice your vocabulary

```bash
epiphany practice --mode chat
```

or

```bash
epiphany practice --mode quiz
```

- **Chat mode**: Interactive conversation with a librarian agent (placeholder - full implementation pending)
- **Quiz mode**: Flashcard-style testing with definitions

#### 3. Export to Anki

```bash
epiphany export --output my_vocab.apkg
```

Generates an Anki deck with all enriched words, ready to import into Anki.

## Project Structure

```
epiphany-ai/
├── src/
│   ├── main.py           # CLI entry point (Typer)
│   ├── database.py       # SQLite operations
│   ├── epub_handler.py   # EPUB parsing & text extraction
│   ├── filter.py         # Word frequency analysis & stopwords
│   ├── ai_agent.py       # OpenRouter API integration
│   └── anki_generator.py # Anki .apkg generation
├── data/                 # SQLite database (auto-created)
├── output/              # Generated Anki decks
├── pyproject.toml       # Project configuration
├── .env                 # Environment variables (gitignored)
└── README.md
```

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key (required for AI enrichment)
- Optional: `OPENROUTER_MODEL`: Model to use (default: `openai/gpt-3.5-turbo`)

### Command Options

**extract:**
- `epub_path`: Path to EPUB file (required)
- `--language`: Language code: `en`, `es`, `fr` (default: `en`)
- `--threshold`: Frequency threshold, lower = rarer words (default: `50`)
- `--db-path`: Database file location (default: `data/epiphany.db`)

**practice:**
- `--mode`: `chat` or `quiz` (default: `chat`)
- `--language`: Filter by language (optional)
- `--db-path`: Database file location

**export:**
- `--output`: Output filename (default: `deck.apkg`)
- `--language`: Filter by language (optional)
- `--db-path`: Database file location
- `--deck-name`: Custom Anki deck name

## Database Schema

```sql
CREATE TABLE words (
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
);
```

**Status values:**
- `pending`: Extracted but not yet enriched
- `enriched`: AI enrichment complete

## Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (coming soon)
pytest
```

### Code Style

```bash
# Format code
black src tests

# Lint
ruff src tests

# Type check
mypy src
```

### Adding New Languages

1. Add stopwords to `src/filter.py` in the `STOPWORDS` dictionary
2. Update language validation in `get_rare_words()`
3. Add language name mapping in `ai_agent.py`'s `_build_prompt()`

## How It Works

### Extraction Pipeline

1. **EPUB Parsing** (`epub_handler.py`)
   - Uses `ebooklib` to read EPUB structure
   - Extracts text from all document items (chapters)
   - Cleans HTML tags with BeautifulSoup
   - Returns concatenated plain text

2. **Word Filtering** (`filter.py`)
   - Tokenizes text (language-aware, supports accented characters)
   - Counts word frequencies
   - Filters out stopwords (common words)
   - Applies frequency threshold to identify rare words
   - Returns list of `(word, frequency)` tuples

3. **Database Storage** (`database.py`)
   - Saves pending words with frequency
   - Uses `INSERT OR IGNORE` to avoid duplicates
   - Tracks status (`pending` vs `enriched`)

4. **AI Enrichment** (`ai_agent.py`)
   - Fetches pending words from database
   - Sends batches to OpenRouter API
   - Prompt requests: definition, etymology, example sentence
   - Parses structured response
   - Updates database with enriched data

5. **Anki Export** (`anki_generator.py`)
   - Fetches enriched words from database
   - Creates Anki deck with custom card template
   - Generates `.apkg` file (ZIP archive)
   - Validates output

### AI Prompt Template

```
For each of the following English words, provide:
1. A clear definition (1-2 sentences)
2. The etymology (word origin, root language, history)
3. An example sentence using the word naturally

Format your response EXACTLY as follows for each word:

Word: [word]
Definition: [definition]
Etymology: [etymology]
Example: [example sentence]

Separate each word's information with a blank line.
```

## Cost Estimation

OpenRouter pricing (as of implementation):
- GPT-3.5-Turbo: ~$0.0002 per word
- Example: 100 words ≈ $0.02

The CLI shows an approximate cost before confirming enrichment.

## Limitations & Future Work

- **Practice chat mode** is a placeholder; full implementation would use an AI agent with conversation memory
- **Stopword lists** are basic; could be enhanced with NLTK corpora
- **No NLTK integration** yet (planned for better tokenization)
- **No migrations** system for database schema changes
- **Single-threaded** processing; could parallelize AI enrichment

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- EPUB handling via [ebooklib](https://github.com/aerkalov/ebooklib)
- Anki deck generation via [genanki](https://github.com/kerrickstaley/genanki)
- AI via [OpenRouter](https://openrouter.ai/)
