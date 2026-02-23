import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
from typing import Optional
from pathlib import Path

# Import our modules
from .epub_handler import read_epub
from .filter import get_rare_words
from .database import Database
from .ai_agent import enrich_words
from .anki_generator import create_deck_from_database

# Initialize Typer and Rich Console
app = typer.Typer(help="Epiphany AI: Turn EPUBs into Brain Power.")
console = Console()


@app.command()
def extract(
    epub_path: Path = typer.Argument(..., help="Path to the .epub file", exists=True),
    language: str = typer.Option("en", help="Target language code (en, es, fr)"),
    threshold: int = typer.Option(50, help="Word frequency threshold (lower = rarer words)"),
    db_path: Path = typer.Option("data/epiphany.db", help="Database file path")
):
    """
    Extracts vocabulary from an EPUB, filters common words, and enriches via AI.
    """
    console.print(Panel(f"[bold cyan]Epiphany AI[/bold cyan]: Analyzing [yellow]{epub_path.name}[/yellow]"))
    
    # Initialize database
    db = Database(db_path)
    
    try:
        # 1. Parsing Step
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Parsing EPUB chapters...", total=None)
            text = read_epub(epub_path)
        
        console.print("[green]✔[/green] EPUB Parsed.")
        
        # 2. Filtering Step (Local)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Filtering for rare words (Threshold: {threshold})...", total=None)
            rare_words = get_rare_words(text, language, threshold)
        
        if not rare_words:
            console.print("[yellow]⚠[/yellow] No rare words found. Try adjusting the threshold.")
            return
        
        # Convert to format for database
        words_to_save = [{'word': word, 'frequency': freq} for word, freq in rare_words]
        inserted = db.save_pending_words(words_to_save, language)
        
        console.print(f"[green]✔[/green] Found [bold]{inserted}[/bold] potential new words.")
        
        # 3. AI Enrichment Step
        pending_count = db.get_word_count(language=language, status='pending')
        
        if pending_count > 0:
            if typer.confirm(f"Send {pending_count} words to OpenRouter for definitions? (Cost approx ${pending_count * 0.0002:.2f})"):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                ) as progress:
                    progress.add_task(description="Contacting AI Agent...", total=None)
                    # Get pending words
                    pending_words = db.get_pending_words(language=language)
                    
                    # Enrich with AI
                    enriched_data = enrich_words(pending_words, language)
                    
                    # Prepare data for database update
                    word_ids = list(enriched_data.keys())
                    definitions = {wid: data['definition'] for wid, data in enriched_data.items()}
                    etymologies = {wid: data['etymology'] for wid, data in enriched_data.items()}
                    examples = {wid: data['example_sentence'] for wid, data in enriched_data.items()}
                    
                    # Update database
                    updated = db.mark_words_enriched(word_ids, definitions, etymologies, examples)
                
                console.print(f"[green]✔[/green] Enriched and saved [bold]{updated}[/bold] words.")
                console.print("[blue]Tip:[/blue] Run 'export' to create an Anki deck.")
            else:
                console.print("[yellow]Skipped AI enrichment. Words saved as pending.[/yellow]")
                console.print("[blue]Tip:[/blue] Run 'extract' again later or use 'export' for pending words.")
        else:
            console.print("[green]All words already enriched![/green]")
            console.print("[blue]Tip:[/blue] Run 'export' to create an Anki deck.")
    
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        logger = logging.getLogger(__name__)
        logger.exception("Error during extraction")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def practice(
    mode: str = typer.Option("chat", help="Practice mode: 'chat' or 'quiz'"),
    language: str = typer.Option(None, help="Language filter (optional)"),
    db_path: Path = typer.Option("data/epiphany.db", help="Database file path")
):
    """
    Interactive practice session with your saved vocabulary.
    """
    console.print(Panel("[bold magenta]Epiphany Practice Mode[/bold magenta]"))
    
    db = Database(db_path)
    
    try:
        # Fetch enriched words
        words = db.get_all_words(language=language, status='enriched')
        
        if not words:
            console.print("[yellow]No enriched words found in database.[/yellow]")
            console.print("[blue]Tip:[/blue] Run 'extract' and complete AI enrichment first.")
            return
        
        console.print(f"[green]Loaded {len(words)} words for practice.[/green]\n")
        
        if mode == "chat":
            _chat_mode(console, words)
        elif mode == "quiz":
            _quiz_mode(console, words)
        else:
            console.print(f"[red]Unknown mode: {mode}. Use 'chat' or 'quiz'.[/red]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


def _chat_mode(console: Console, words: list):
    """
    Chat mode: AI acts as a librarian, using vocabulary in conversation.
    """
    console.print("[italic]Agent is assuming the role of a librarian...[/italic]\n")
    console.print("[dim]Type 'exit' or 'quit' to leave.[/dim]\n")
    
    # Build vocabulary context
    vocab_list = "\n".join([f"- {w['word']}: {w['definition']}" for w in words[:20]])  # Limit context
    if len(words) > 20:
        vocab_list += f"\n... and {len(words) - 20} more"
    
    system_prompt = f"""You are a knowledgeable librarian helping a student learn vocabulary. 
You have access to these vocabulary words and their definitions:

{vocab_list}

When conversing, naturally incorporate these words into your responses when appropriate. 
Explain concepts clearly and encourage learning. Keep responses concise and helpful."""
    
    # Simple chat loop (we'll use a mock implementation since we don't have a separate chat agent)
    # In a full implementation, this would use an AI agent with conversation memory
    
    while True:
        user_input = typer.prompt("You")
        if user_input.lower() in ["exit", "quit"]:
            console.print("[yellow]Goodbye![/yellow]")
            break
        
        # Mock response - in production, this would call an AI chat agent
        console.print("[bold cyan]Librarian:[/bold cyan] This is a placeholder. In a full implementation, I'd respond using the vocabulary words.")
        console.print("[dim](Chat mode would use an AI agent with access to your vocabulary list)[/dim]\n")


def _quiz_mode(console: Console, words: list):
    """
    Quiz mode: Flashcard-style testing.
    """
    import random
    
    console.print("[bold]Quiz time![/bold] I'll show you a definition, you guess the word.\n")
    console.print("[dim]Type 'skip' to skip, 'exit' to quit.[/dim]\n")
    
    # Shuffle words
    quiz_words = words.copy()
    random.shuffle(quiz_words)
    
    score = 0
    total = 0
    
    for word_data in quiz_words:
        total += 1
        definition = word_data['definition']
        correct_answer = word_data['word']
        
        console.print(f"[bold cyan]Definition:[/bold cyan] {definition}")
        guess = typer.prompt("Your guess").strip().lower()
        
        if guess in ["exit", "quit"]:
            break
        elif guess == "skip":
            console.print(f"[yellow]Skipped. The word was: [bold]{correct_answer}[/bold][/yellow]\n")
            continue
        
        if guess == correct_answer.lower():
            console.print("[green]✓ Correct![/green]\n")
            score += 1
        else:
            console.print(f"[red]✗ Incorrect. The word was: [bold]{correct_answer}[/bold][/red]\n")
        
        # Show etymology and example
        if word_data.get('etymology'):
            console.print(f"[dim]Etymology: {word_data['etymology']}[/dim]")
        if word_data.get('example_sentence'):
            console.print(f"[dim]Example: {word_data['example_sentence']}[/dim]")
        console.print()
    
    console.print(f"[bold]Quiz complete![/bold] Score: {score}/{total} ({score/total*100:.1f}%)")


@app.command()
def export(
    output: Path = typer.Option("deck.apkg", help="Output filename"),
    language: str = typer.Option(None, help="Language filter (optional)"),
    db_path: Path = typer.Option("data/epiphany.db", help="Database file path"),
    deck_name: str = typer.Option(None, help="Custom deck name")
):
    """
    Export processed words to an Anki (.apkg) file.
    """
    console.print(f"Generating Anki deck at [bold]{output}[/bold]...")
    
    try:
        db = Database(db_path)
        
        success = create_deck_from_database(
            db=db,
            language=language,
            output_path=output,
            deck_name=deck_name
        )
        
        if success:
            console.print("[green]✔[/green] Export complete.")
            
            # Validate deck
            from .anki_generator import validate_deck
            validation = validate_deck(output)
            if validation['valid']:
                console.print(f"[dim]Deck size: {validation['size_bytes']} bytes[/dim]")
            else:
                console.print(f"[yellow]Warning: Deck validation failed: {validation['error']}[/yellow]")
        else:
            console.print("[red]✗[/red] Failed to create deck. No enriched words found.")
            console.print("[blue]Tip:[/blue] Run 'extract' and complete AI enrichment first.")
    
    except Exception as e:
        console.print(f"[red]✗[/red] Error creating deck: {e}")
        raise typer.Exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    app()