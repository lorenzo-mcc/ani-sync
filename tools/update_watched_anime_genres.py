"""
Module: update_watched_anime_genres.py
Description:
    Copies genres from the main 'Genres' relation into the 'Genres (Watched Anime)' property for watched entries.

Usage:
    python cli.py tools update-genres-watched [--titles file.txt]

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * FULL_CATALOG_DB_ID
        * GENRES_SOURCE
        * GENRES_TARGET
        * NOTION_API_KEY
        * WATCHED_RELATION
    - Can optionally restrict scope via `utils/title_filter.py` using the `--titles` CLI argument or the `ANIME_TITLES_FILE` variable in `.env`.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client
from tqdm import tqdm
from rich.console import Console

from utils.env import validate_env_vars
from utils.title_filter import load_selected_titles, filter_anime_list

console = Console()

# === Load .env ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
output_dir = base_path / "output"
output_dir.mkdir(parents=True, exist_ok=True)

load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY", "FULL_CATALOG_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

notion = Client(auth=os.getenv("NOTION_API_KEY"))

# Full Catalog database ID
FULL_CATALOG_DB_ID = os.getenv("FULL_CATALOG_DB_ID")

# Property names (with defaults for flexibility)
WATCHED_RELATION = os.getenv("WATCHED_RELATION", "Anime Watched")
GENRES_SOURCE = os.getenv("GENRES_SOURCE", "Genres")
GENRES_TARGET = os.getenv("GENRES_TARGET", "Genres (Anime Watched)")


def get_watched_anime():
    """Fetch all Notion entries with WATCHED_RELATION not empty."""
    all_items = []
    start_cursor = None

    while True:
        response = notion.databases.query(
            database_id=FULL_CATALOG_DB_ID,
            filter={"property": WATCHED_RELATION, "relation": {"is_not_empty": True}},
            start_cursor=start_cursor,
            page_size=100,
        )

        for page in response["results"]:
            props = page["properties"]
            eng_title_vals = props.get("English Title", {}).get("title", [])
            eng_title = eng_title_vals[0].get("plain_text", "") if eng_title_vals else ""
            romaji_vals = props.get("Romaji Title", {}).get("rich_text", [])
            romaji_title = romaji_vals[0].get("plain_text", "") if romaji_vals else ""

            all_items.append(
                {
                    "id": page["id"],
                    "eng_title": eng_title,
                    "romaji_title": romaji_title,
                    "properties": props,
                }
            )

        if response.get("has_more"):
            start_cursor = response["next_cursor"]
        else:
            break

    return all_items


def main(titles_file: str | None = None):
    """
    Entry point for 'Genres (Watched Anime)' sync.

    Args:
        titles_file: Optional path to a .txt file with titles to process.
                     Overrides ANIME_TITLES_FILE from .env if provided.
    """
    console.print("[bold white]\n🌟 Anime Watched Genres Sync\n[/bold white]")

    # Load selection (CLI > .env > None)
    selected = load_selected_titles(titles_file)

    # Fetch and optionally filter
    watched_anime = get_watched_anime()
    watched_anime = filter_anime_list(watched_anime, selected)

    total_checked = len(watched_anime)
    updated_count = 0
    updated_titles = []

    console.print(
        f"[bold magenta]📂 Found {total_checked} Watched Anime to process.[/bold magenta]\n"
    )

    for anime in tqdm(watched_anime, desc="🔁 Updating genres"):
        anime_id = anime["id"]
        props = anime["properties"]

        source_genres = props.get(GENRES_SOURCE, {}).get("relation", [])
        source_ids = [g["id"] for g in source_genres]

        current_genres = props.get(GENRES_TARGET, {}).get("relation", [])
        current_ids = [g["id"] for g in current_genres]

        if set(source_ids) == set(current_ids):
            continue  # already synced

        updated_ids = sorted({*source_ids, *current_ids})

        try:
            notion.pages.update(
                page_id=anime_id,
                properties={GENRES_TARGET: {"relation": [{"id": id_} for id_ in updated_ids]}},
            )
            updated_titles.append(anime["eng_title"] or anime["romaji_title"] or "Unknown Title")
            updated_count += 1
        except Exception as e:
            console.print(f"[bold red]❌ Error updating anime {anime_id}[/bold red]\n{e}")

    # Save updated titles to log file
    log_path = output_dir / "genres_updated.log"
    with open(log_path, "w", encoding="utf-8") as f:
        for title in updated_titles:
            f.write(title + "\n")

    console.print(f"\n[bold green]✅ Total checked: {total_checked}[/bold green]")
    console.print(f"[bold cyan]📝 Anime updated: {updated_count}[/bold cyan]")
    if updated_count == 0:
        console.print("[bold yellow]🔝 No updates needed. Everything is already synced.[/bold yellow]\n")
    else:
        console.print(f"[dim]📁 Log saved to: {log_path}[/dim]\n")

    return updated_count


if __name__ == "__main__":
    main()
