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
    Add new anime entries to Notion by reading titles from 'anime_list.txt'.
    Each title is resolved via AniList and added with complete metadata.
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
    banner: bool = typer.Option(True, "--banner/--no-banner", help="Update banner images"),
    sources: bool = typer.Option(True, "--sources/--no-sources", help="Update sources"),
    studios: bool = typer.Option(True, "--studios/--no-studios", help="Check animation studios"),
    genres: bool = typer.Option(True, "--genres/--no-genres", help="Sync watched anime genres"),
    romaji: bool = typer.Option(True, "--romaji/--no-romaji", help="Update Romaji titles"),
    country: bool = typer.Option(
        True, "--country/--no-country", help="Update country from flag emojis"
    ),
):
    """
    Run multiple updaters in sequence (default runs all).
    """
    console.print("\n[bold white]🔄 Running AniList–Notion updaters...[/bold white]\n")

    try:
        if banner:
            console.rule("[cyan]Updating Banner Images")
            from tools.update_banner_images import main as run_banner_images

            run_banner_images()

        if sources:
            console.rule("[cyan]Updating Sources")
            from tools.update_sources import main as run_sources

            run_sources()

        if studios:
            console.rule("[cyan]Updating Animation Studios")
            from tools.update_animation_studios import main as run_studios

            run_studios()

        if genres:
            console.rule("[cyan]Syncing Watched Anime Genres")
            from tools.update_watched_anime_genres import main as run_genres

            run_genres()

        if romaji:
            console.rule("[cyan]Updating Romaji Titles")
            from tools.update_romaji_titles import main as run_romaji

            run_romaji()

        if country:
            console.rule("[cyan]Updating Country from Flags")
            from tools.update_country_from_flags import main as run_country

            run_country()

        console.print("\n[bold green]✅ All selected updates completed.[/bold green]\n")

    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import one of the updaters.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-studios")
def update_studios():
    """
    Populate the 'Studios' property in Notion using official data from AniList.
    Ensures accurate studio attribution for each anime.
    """
    try:
        from tools.update_animation_studios import main as run_studios

        run_studios()
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import studios updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-genres-watched")
def update_genres_watched():
    """
    Sync the 'Genres (Watched Anime)' property by copying genres from the main field.
    Applies only to entries marked as watched.
    """
    try:
        from tools.update_watched_anime_genres import main as run_genres

        run_genres()
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import genres updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-country")
def update_country():
    """
    Set the 'Country' property in Notion based on flag emojis (e.g., 🇯🇵 → Japan).
    Helps populate origin metadata based on emoji icons.
    """
    try:
        from tools.update_country_from_flags import main as run_country

        run_country()
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import country updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-romaji-titles")
def update_romaji_titles():
    """
    Fill in missing 'Romaji Title' values using AniList metadata.
    Unmatched entries are exported to a CSV file for manual review.
    """
    try:
        from tools.update_romaji_titles import main as run_romaji

        run_romaji()
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import romaji title updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-sources")
def update_sources():
    """
    Populate the 'Source' field for each anime using AniList's adaptation origin.
    Prompts user if source is unknown. Saves unmatched titles for review.
    """
    try:
        from tools.update_sources import main as run_sources

        run_sources()
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import source updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("update-banner-images")
def update_banner_images():
    """
    Sync Notion page covers with AniList banner images.
    Prompts on ambiguous matches; logs unmatched entries.
    """
    try:
        from tools.update_banner_images import main as run_banner_images

        run_banner_images()
    except ImportError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not import banner updater.\n[dim]Details: {e}[/dim]"
        )


@tools_app.command("count-anime")
def count_anime(
    retry: bool = typer.Option(
        False, "--retry", help="Retry only titles with previous no_response failures."
    )
):
    """
    Count all anime entries in Notion and check for matches on AniList.
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
    debug: bool = typer.Option(False, "--debug", help="Log raw OpenAI responses for debugging."),
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
