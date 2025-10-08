"""
Module: update_romaji_titles.py
Description:
    Fills missing 'Romaji Title' values in Notion using AniList metadata with interactive disambiguation on ambiguous results.

Usage:
    python cli.py tools update-romaji-titles [--titles file.txt]

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * ANILIST_API_URL
        * FULL_CATALOG_DB_ID
        * NOTION_API_KEY
        * REQUEST_INTERVAL
    - Can optionally restrict scope via `utils/title_filter.py` using the `--titles` CLI argument or the `ANIME_TITLES_FILE` variable in `.env`.
"""

import requests
import os
import csv
import time
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from notion_client import Client

from utils.env import validate_env_vars
from utils.title_filter import load_selected_titles, filter_anime_list

console = Console(force_terminal=True, color_system="truecolor", soft_wrap=True)

# === Load environment ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
output_dir = base_path / "output"
output_dir.mkdir(parents=True, exist_ok=True)

load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY", "FULL_CATALOG_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

# === Notion and AniList config ===
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
FULL_CATALOG_DB_ID = os.getenv("FULL_CATALOG_DB_ID")
ANILIST_API_URL = os.getenv("ANILIST_API_URL", "https://graphql.anilist.co")
REQUEST_INTERVAL = float(os.getenv("REQUEST_INTERVAL", 60 / 28))

ANILIST_QUERY = """
query ($search: String, $year: Int) {
  Page(page: 1, perPage: 10) {
    media(search: $search, type: ANIME, seasonYear: $year) {
      id
      title {
        romaji
        english
      }
      format
      startDate {
        year
      }
      source
    }
  }
}
"""

notion = Client(auth=NOTION_API_KEY)

FORMAT_MAP_REVERSE = {
    "TV": "TV",
    "TV Short": "TV_SHORT",
    "Movie": "MOVIE",
    "OVA": "OVA",
    "ONA": "ONA",
    "Special": "SPECIAL",
}

SOURCE_MAP = {
    "MANGA": "Manga",
    "LIGHT_NOVEL": "Light Novel",
    "VISUAL_NOVEL": "Visual Novel",
    "WEB_NOVEL": "Web Novel",
    "NOVEL": "Novel",
    "ORIGINAL": "Original",
    "VIDEO_GAME": "Video Game",
    "GAME": "Game",
    "MULTIMEDIA_PROJECT": "Multimedia Project",
    "DOUJINSHI": "Doujinshi",
    "COMIC": "Comic",
    "OTHER": "Other",
}


def request_with_retry(url, headers, json_data=None, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=json_data)
            if response.status_code == 200:
                return response
            console.print(
                f"[bold red]Request failed ({attempt+1}): {response.status_code} - {response.text}[/bold red]"
            )
        except requests.RequestException as e:
            console.print(f"[bold red]Network error ({attempt+1}): {e}[/bold red]")
        time.sleep(delay)
    return None


def get_notion_anime():
    """Fetch Notion anime entries missing Romaji Title."""
    all_anime = []
    start_cursor = None

    while True:
        kwargs = {"database_id": FULL_CATALOG_DB_ID}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        results = notion.databases.query(**kwargs)

        for page in results.get("results", []):
            props = page["properties"]
            title_vals = props.get("English Title", {}).get("title", [])
            notion_title = title_vals[0].get("plain_text", "") if title_vals else ""
            romaji_vals = props.get("Romaji Title", {}).get("rich_text", [])
            notion_format = props.get("Format", {}).get("select", {}).get("name", "")
            debut_year = str(props.get("Debut Year", {}).get("number") or "")
            source_val = props.get("Source", {}).get("select")
            source = source_val.get("name", "") if source_val else ""

            if any(val.get("plain_text", "") for val in romaji_vals):
                continue  # Skip if Romaji Title already set

            all_anime.append(
                {
                    "id": page["id"],
                    "title": notion_title.strip(),
                    "format": notion_format.strip(),
                    "debut_year": debut_year.strip(),
                    "source": source.strip(),
                }
            )

        if not results.get("has_more"):
            break

        start_cursor = results.get("next_cursor")

    return all_anime


def update_romaji_title(page_id, romaji_title):
    try:
        notion.pages.update(
            page_id=page_id,
            properties={"Romaji Title": {"rich_text": [{"text": {"content": romaji_title}}]}},
        )
        console.print(f"[bold green]✅ Romaji title updated: {romaji_title}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to update Romaji title: {e}[/bold red]")


def search_anilist(title, debut_year):
    variables = {
        "search": title,
        "year": int(debut_year) if debut_year.isdigit() else None,
    }
    headers = {"Content-Type": "application/json"}

    time.sleep(REQUEST_INTERVAL)
    resp = request_with_retry(
        ANILIST_API_URL,
        headers,
        json_data={"query": ANILIST_QUERY, "variables": variables},
    )
    if not resp:
        return []
    data = resp.json().get("data", {})
    return data.get("Page", {}).get("media", [])


def display_match_options(notion_anime, candidates):
    for idx, candidate in enumerate(candidates, start=1):
        title_data = candidate.get("title") or {}
        source_raw = candidate.get("source")
        source_clean = SOURCE_MAP.get(source_raw, "Other") if source_raw else "N/A"

        table = Table(title=f"[{idx}] AniList Match", expand=True)
        table.add_column("Field", style="cyan", justify="center")
        table.add_column("Notion", style="green", overflow="fold")
        table.add_column("AniList", style="yellow", overflow="fold")

        table.add_row(
            "Title",
            notion_anime["title"],
            f"{title_data.get('english', '—')} / {title_data.get('romaji', '')}",
        )
        table.add_row("Format", notion_anime["format"], candidate.get("format", "N/A"))
        table.add_row(
            "Debut Year",
            notion_anime["debut_year"],
            str(candidate.get("startDate", {}).get("year", "")),
        )
        table.add_row("Source", notion_anime["source"], source_clean)

        console.print(table)


def main(titles_file: str | None = None):
    """
    Entry point for Romaji Title sync.

    Args:
        titles_file: Optional path to a .txt file with titles to process.
                     Overrides ANIME_TITLES_FILE from .env if provided.
    """
    console.print("\n[bold white]🔗 Romaji Title Sync[/bold white]\n")

    # Load selection (CLI > .env > None)
    selected = load_selected_titles(titles_file)

    # Fetch and optionally filter
    anime_list = get_notion_anime()
    anime_list = filter_anime_list(anime_list, selected, keys=["title"])

    updated = 0
    not_matched = []

    for idx, anime in enumerate(anime_list, start=1):
        title = anime["title"]
        year = anime["debut_year"]
        format_notion = anime["format"]
        source_notion = anime["source"]

        console.print(f"[bold blue]{idx}/{len(anime_list)} ➔  Processing:[/bold blue] {title}")

        candidates = search_anilist(title, year)
        if not candidates:
            console.print(f"[bold red]No AniList results found for:[/bold red] {title}")
            not_matched.append(anime)
            continue

        desired_format = FORMAT_MAP_REVERSE.get(format_notion, None)

        perfect_matches = []
        for c in candidates:
            title_data = c.get("title") or {}
            english = (title_data.get("english") or "").strip().lower()
            anilist_format = c.get("format", "")
            anilist_year = str(c.get("startDate", {}).get("year", ""))
            anilist_source_raw = c.get("source")
            anilist_source = (
                SOURCE_MAP.get(anilist_source_raw, "Other") if anilist_source_raw else "N/A"
            )

            if (
                english == title.lower()
                and anilist_format == desired_format
                and anilist_year == year
                and anilist_source == source_notion
            ):
                perfect_matches.append(c)

        if len(perfect_matches) == 1:
            matched = perfect_matches[0]
            romaji = matched.get("title", {}).get("romaji", "").strip()
            console.print(
                f"[bold green]Auto-matched:[/bold green] {title} → [italic]{romaji}[/italic]"
            )
            update_romaji_title(anime["id"], romaji)
            updated += 1
            continue

        display_match_options(anime, candidates)
        choice_str = Prompt.ask(
            "Select the correct match (0 to skip)",
            choices=[str(i) for i in range(len(candidates) + 1)],
        )
        choice = int(choice_str)

        if choice == 0:
            console.print("[red]❌ Skipped this anime.[/red]")
            not_matched.append(anime)
            continue

        selected = candidates[choice - 1]
        romaji = selected.get("title", {}).get("romaji", "").strip()
        update_romaji_title(anime["id"], romaji)
        updated += 1

    if not_matched:
        csv_path = output_dir / "unmatched_romaji_titles.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["title", "debut_year", "format", "source"])
            writer.writeheader()
            for anime in not_matched:
                writer.writerow(
                    {
                        "title": anime["title"],
                        "debut_year": anime["debut_year"],
                        "format": anime["format"],
                        "source": anime["source"],
                    }
                )
        console.print(f"\n[bold yellow]📄 Unmatched titles saved to:[/bold yellow] {csv_path}")

    console.print(f"\n[bold green]✅ Total updated: {updated}[/bold green]\n")


if __name__ == "__main__":
    main()
