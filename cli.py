"""
Module: cli.py
Description:
    Typer-based command-line interface orchestrating all AniSync tools and Notion/AniList workflows.

Usage:
    python cli.py [subcommand] [options]

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * None
    - Forwards `--titles` to updaters where supported.
"""

import typer
from rich.console import Console

console = Console()

app = typer.Typer(help="AniSync CLI – Your anime automation toolkit.")

# === Sub-apps ===
notion_app = typer.Typer(help="Commands related to importing new anime entries into Notion.")
tools_app = typer.Typer(help="Utility scripts for managing and syncing anime data.")

app.add_typer(notion_app, name="notion")
app.add_typer(tools_app, name="tools")


# === NOTION COMMANDS ===
@notion_app.command("sync-anime")
def add_anime(
    force: bool = typer.Option(
        False, help="Overwrite existing entries if the title already exists."
    )
):
    """
    Import new anime entries into Notion from 'anime_list.txt'.
    Each title is resolved via AniList and inserted with full metadata.
    """
    try:
        from syncer.main import main as run_sync
        run_sync(force=force)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import anime syncer.\n[dim]Details: {e}[/dim]"
        )


# === TOOLS COMMANDS ===
@tools_app.command("update-all")
def update_all(
    images: bool = typer.Option(True, "--images/--no-images", help="Update covers and images."),
    sources: bool = typer.Option(True, "--sources/--no-sources", help="Update sources."),
    studios: bool = typer.Option(True, "--studios/--no-studios", help="Update animation studios."),
    genres: bool = typer.Option(True, "--genres/--no-genres", help="Sync watched anime genres."),
    romaji: bool = typer.Option(True, "--romaji/--no-romaji", help="Update Romaji titles."),
    country: bool = typer.Option(True, "--country/--no-country", help="Update country from flags."),
    titles: str = typer.Option(
        None,
        "--titles",
        help="Optional path to a .txt file with titles to update. "
             "Overrides ANIME_TITLES_FILE from .env. "
             "If both are missing, updates ALL anime."
    ),
):
    """
    Run multiple AniList → Notion updaters in sequence.
    By default runs all modules. Use flags to disable specific ones.
    """
    console.print("\n[bold white]🔄 Running AniList–Notion updaters...[/bold white]\n")

    try:
        if images:
            console.rule("[cyan]Updating Images")
            from tools.update_images import main as run_images
            run_images(titles_file=titles)

        if sources:
            console.rule("[cyan]Updating Sources")
            from tools.update_sources import main as run_sources
            run_sources(titles_file=titles)

        if studios:
            console.rule("[cyan]Updating Animation Studios")
            from tools.update_animation_studios import main as run_studios
            run_studios(titles_file=titles)

        if genres:
            console.rule("[cyan]Syncing Watched Anime Genres")
            from tools.update_watched_anime_genres import main as run_genres
            run_genres(titles_file=titles)

        if romaji:
            console.rule("[cyan]Updating Romaji Titles")
            from tools.update_romaji_titles import main as run_romaji
            run_romaji(titles_file=titles)

        if country:
            console.rule("[cyan]Updating Country from Flags")
            from tools.update_country_from_flags import main as run_country
            run_country(titles_file=titles)

        console.print("\n[bold green]✅ All selected updates completed.[/bold green]\n")

    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import one of the updaters.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-studios")
def update_studios(
    titles: str = typer.Option(
        None, "--titles", help="Limit update to titles from file (.txt). Defaults to .env or ALL."
    ),
):
    """Populate the 'Studios' property in Notion using AniList official data."""
    try:
        from tools.update_animation_studios import main as run_studios
        run_studios(titles_file=titles)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import studios updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-genres-watched")
def update_genres_watched(
    titles: str = typer.Option(
        None, "--titles", help="Limit update to titles from file (.txt). Defaults to .env or ALL."
    ),
):
    """Sync 'Genres (Watched Anime)' property with the main 'Genres' field."""
    try:
        from tools.update_watched_anime_genres import main as run_genres
        run_genres(titles_file=titles)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import genres updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-country")
def update_country(
    titles: str = typer.Option(
        None, "--titles", help="Limit update to titles from file (.txt). Defaults to .env or ALL."
    ),
):
    """Set 'Country' property in Notion based on emoji flag (🇯🇵 → Japan, etc.)."""
    try:
        from tools.update_country_from_flags import main as run_country
        run_country(titles_file=titles)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import country updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-romaji-titles")
def update_romaji_titles(
    titles: str = typer.Option(
        None, "--titles", help="Limit update to titles from file (.txt). Defaults to .env or ALL."
    ),
):
    """Fill missing 'Romaji Title' values using AniList metadata."""
    try:
        from tools.update_romaji_titles import main as run_romaji
        run_romaji(titles_file=titles)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import romaji title updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-sources")
def update_sources(
    titles: str = typer.Option(
        None, "--titles", help="Limit update to titles from file (.txt). Defaults to .env or ALL."
    ),
):
    """Populate 'Source' property (Manga, Light Novel, Original, etc.) from AniList."""
    try:
        from tools.update_sources import main as run_sources
        run_sources(titles_file=titles)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import source updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-images")
def update_images(
    titles: str = typer.Option(
        None, "--titles", help="Limit update to titles from file (.txt). Defaults to .env or ALL."
    ),
):
    """Sync Notion page covers (banner + Files & media) with AniList images."""
    try:
        from tools.update_images import main as run_images
        run_images(titles_file=titles)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import images updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("count-anime")
def count_anime(
    retry: bool = typer.Option(
        False, "--retry", help="Retry only titles with previous no_response failures."
    )
):
    """
    Count all anime entries in Notion and check for AniList matches.
    Use --retry to only retry entries that previously failed.
    """
    try:
        if retry:
            from tools.retry_no_response import main as run_retry
            run_retry()
        else:
            from tools.count_anime import main as run_counter
            run_counter()
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import anime checker.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("extract-anime-titles")
def extract_titles(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simulate without calling OpenAI or writing files."
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Log raw OpenAI responses for debugging."
    ),
):
    """
    Extract anime titles from screenshots or Instagram Reels using GPT-4o.
    Saves unique titles to a plain text file for processing.
    """
    try:
        from tools.extract_titles import main as run_extractor
        run_extractor(dry_run=dry_run, debug_output=debug)
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import titles extractor.\n[dim]Details: {e}[/dim]"
        )


# === ENTRY POINT ===
if __name__ == "__main__":
    app()
