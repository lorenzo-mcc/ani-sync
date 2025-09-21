"""
Module: main.py
Description:
    High-level sync entry point that reads titles and creates/upserts Notion entries.

Usage:
    python cli.py notion sync-anime

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * FULL_CATALOGUE_DB_ID
        * GENRES_DB_ID
"""

from syncer.anilist_fetcher import fetch_anime_info
from syncer.formatter import format_data_for_notion
from syncer.notion_updater import create_notion_page
import re
import os
from dotenv import load_dotenv
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from utils.env import validate_env_vars

console = Console()

# === Load .env ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["FULL_CATALOGUE_DB_ID", "GENRES_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

FULL_CATALOGUE_DB_ID = os.getenv("FULL_CATALOGUE_DB_ID")
GENRES_DB_ID = os.getenv("GENRES_DB_ID")


def split_title_and_season(title: str):
    match = re.match(r"^(.*?)\s*(\((.*?)\))?$", title.strip())
    if match:
        main_title = match.group(1).strip()
        return main_title, title.strip()
    return title.strip(), title.strip()


def main(force=False):
    console.print("[bold white]\n📚 AniList → Notion | Anime Importer[/bold white]\n")

    database_id = FULL_CATALOGUE_DB_ID
    genre_database_id = GENRES_DB_ID

    input_file = Path(__file__).resolve().parent / "input" / "anime_list.txt"
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    unmatched_file = output_dir / "unmatched_anime.txt"
    unmatched_titles = []

    try:
        with open(input_file, "r", encoding="utf-8") as file:
            anime_data = [split_title_and_season(line.strip()) for line in file if line.strip()]
    except FileNotFoundError:
        console.print(f"[bold red]❌ Error: The file '{input_file}' was not found.[/bold red]")
        return

    total_titles = len(anime_data)
    added_count = 0
    not_found_count = 0
    already_exists_count = 0

    for main_title, full_title in anime_data:
        console.print(f"\n[bold white]🔎 Searching for:[/bold white] {main_title}")
        anime_results = fetch_anime_info(main_title)

        if not anime_results:
            console.print(f"[yellow]⚠️  No results found for '{main_title}'.[/yellow]")
            not_found_count += 1
            unmatched_titles.append(main_title)
            continue

        console.print("\n[bold green]✅ Results found:[/bold green]")
        anime_results_sorted = sorted(
            anime_results,
            key=lambda x: (
                0 if (x.get("format") or "").upper() == "TV" else 1,
                x.get("startDate", {}).get("year") or float("inf"),
            ),
        )

        for i, anime in enumerate(anime_results_sorted, start=1):
            title_romaji = anime.get("title", {}).get("romaji", "Unknown")
            title_english = anime.get("title", {}).get("english", "Unknown")
            start_year = anime.get("startDate", {}).get("year", "Unknown")
            anime_format = anime.get("format", "Unknown")
            status = anime.get("status", "Unknown")
            console.print(
                f"[cyan]{i}.[/cyan] {title_romaji} / {title_english} — "
                f"[dim]Format:[/dim] {anime_format}, [dim]Status:[/dim] {status}, "
                f"[dim]Year:[/dim] {start_year}"
            )

        choice = Prompt.ask("\nSelect a number (or type 'skip' to skip)", default="skip")
        if choice.lower() == "skip":
            unmatched_titles.append(main_title)
            continue

        try:
            choice = int(choice)
            if choice < 1 or choice > len(anime_results_sorted):
                console.print("[bold red]❌ Invalid selection.[/bold red]")
                unmatched_titles.append(main_title)
                continue

            selected_anime = anime_results_sorted[choice - 1]
            formatted_data = format_data_for_notion(selected_anime, full_title)

            console.print("\n[bold green]📦 Data prepared for Notion:[/bold green]")
            for key, value in formatted_data.items():
                console.print(f"[dim]{key}[/dim]: {value}")

            success, result = create_notion_page(
                database_id, formatted_data, genre_database_id, force=force
            )

            if result == "created":
                added_count += 1
                console.print(
                    f"[bold green]✅ Added:[/bold green] {formatted_data['English Title']}"
                )
            elif result == "updated":
                added_count += 1
                console.print(
                    f"[bold blue]🔁 Updated:[/bold blue] {formatted_data['English Title']}"
                )
            elif result == "skipped":
                already_exists_count += 1
                unmatched_titles.append(main_title)
            elif result == "error":
                console.print(
                    f"[bold red]❌ Failed to sync:[/bold red] {formatted_data['English Title']}"
                )
                unmatched_titles.append(main_title)

        except ValueError:
            console.print("[bold red]❌ Please enter a valid number.[/bold red]")
            unmatched_titles.append(main_title)
            continue

    # Write unmatched titles to file
    if unmatched_titles:
        with open(unmatched_file, "w", encoding="utf-8") as f:
            for title in unmatched_titles:
                f.write(f"{title}\n")
        console.print(
            f"\n[bold yellow]⚠️  Unmatched titles saved to: {unmatched_file}[/bold yellow]"
        )

    console.print(f"\n[bold green]✅ Total titles processed: {total_titles}[/bold green]")
    console.print(f"[bold cyan]📝 Titles added to Notion: {added_count}[/bold cyan]")
    console.print(f"[bold purple]🔁 Titles already in Notion: {already_exists_count}[/bold purple]")
    console.print(f"[bold yellow]❌ Titles not found or skipped: {not_found_count}[/bold yellow]\n")


if __name__ == "__main__":
    main()
