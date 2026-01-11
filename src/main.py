import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
from typing import Optional
from pathlib import Path

# Initialize Typer and Rich Console
app = typer.Typer(help="Epiphany AI: Turn EPUBs into Brain Power.")
console = Console()

@app.command()
def extract(
    epub_path: Path = typer.Argument(..., help="Path to the .epub file", exists=True),
    language: str = typer.Option("en", help="Target language code (en, es, fr)"),
    threshold: int = typer.Option(50, help="Word frequency threshold (lower = rarer words)")
):
    """
    Extracts vocabulary from an EPUB, filters common words, and enriches via AI.
    """
    console.print(Panel(f"[bold cyan]Epiphany AI[/bold cyan]: Analyzing [yellow]{epub_path.name}[/yellow]"))

    # 1. Parsing Step
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Parsing EPUB chapters...", total=None)
        # TODO: Call src.epub_handler.read_epub(epub_path)
        import time; time.sleep(1) # Simulation
    
    console.print("[green]✔[/green] EPUB Parsed.")

    # 2. Filtering Step (Local)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"Filtering for rare words (Threshold: {threshold})...", total=None)
        # TODO: Call src.filter.get_rare_words(text, language)
        # TODO: Call src.database.save_pending_words()
        time.sleep(1) # Simulation

    console.print(f"[green]✔[/green] Found [bold]142[/bold] potential new words.")

    # 3. AI Enrichment Step
    if typer.confirm("Send these words to OpenRouter for definitions? (Cost approx $0.02)"):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Contacting AI Agent...", total=None)
            # TODO: Call src.ai_agent.enrich_words()
            time.sleep(2) # Simulation
        
        console.print("[green]✔[/green] Database updated successfully!")
        console.print("[blue]Tip:[/blue] Run 'export' to create an Anki deck.")


@app.command()
def practice(
    mode: str = typer.Option("chat", help="Practice mode: 'chat' or 'quiz'"),
):
    """
    Interactive practice session with your saved vocabulary.
    """
    console.print(Panel("[bold magenta]Epiphany Practice Mode[/bold magenta]"))
    
    if mode == "chat":
        console.print("[italic]Agent is assuming the role of a librarian...[/italic]\n")
        # TODO: interactive loop fetching words from DB and sending to LLM
        while True:
            user_input = typer.prompt("You")
            if user_input.lower() in ["exit", "quit"]:
                break
            console.print(f"[bold cyan]Agent:[/bold cyan] (AI response logic here...)")

@app.command()
def export(
    output: Path = typer.Option("deck.apkg", help="Output filename")
):
    """
    Export processed words to an Anki (.apkg) file.
    """
    console.print(f"Generating Anki deck at [bold]{output}[/bold]...")
    # TODO: Call src.anki_generator.create_deck()
    console.print("[green]✔[/green] Export complete.")

if __name__ == "__main__":
    app()