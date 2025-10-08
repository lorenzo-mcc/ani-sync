"""
Module: update_animation_studios.py
Description:
    Fetches animation studios from AniList and writes a normalized, de-duplicated list into the Notion 'Studios' field.

Usage:
    python cli.py tools update-studios [--titles file.txt]

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
import time
import csv
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from notion_client import Client

from utils.env import validate_env_vars
from utils.title_filter import load_selected_titles, filter_anime_list

console = Console()

# ====== LOAD .env ======
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
output_dir = base_path / "output"
output_dir.mkdir(parents=True, exist_ok=True)
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY", "FULL_CATALOG_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
notion = Client(auth=NOTION_API_KEY)
FULL_CATALOG_DB_ID = os.getenv("FULL_CATALOG_DB_ID")
ANILIST_API_URL = os.getenv("ANILIST_API_URL", "https://graphql.anilist.co")

# Optional throttling if you want to be gentle with AniList API
REQUEST_INTERVAL = float(os.getenv("REQUEST_INTERVAL", 60 / 28))

# ——— Reference maps ———
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

FORMAT_MAP_REVERSE = {
    "TV": "TV",
    "TV Short": "TV_SHORT",
    "Movie": "MOVIE",
    "OVA": "OVA",
    "ONA": "ONA",
    "Special": "SPECIAL",
}


def request_with_retry(url, headers, json_data=None, retries=3, delay=2):
    """POST with retry logic for transient errors."""
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=json_data)
            if response.status_code == 200:
                return response
            console.print(
                f"[bold red]Request failed (attempt {attempt+1}): {response.status_code} - {response.text}[/bold red]"
            )
        except requests.RequestException as e:
            console.print(f"[bold red]Network error: {e} (attempt {attempt+1})[/bold red]")
        time.sleep(delay)
    return None


def parse_rollup_genres(rollup_prop):
    """Extract genre names from a Notion rollup (if present)."""
    if rollup_prop.get("type") != "rollup":
        return []

    results = []
    for item in rollup_prop["rollup"].get("array", []):
        if item["type"] in {"title", "rich_text"}:
            for span in item[item["type"]]:
                txt = span.get("plain_text", "")
                if txt:
                    results.append(txt)
    return results


def get_notion_anime():
    """Collect minimal anime fields from Notion needed for studio sync."""
    all_anime = []
    start_cursor = None

    while True:
        kwargs = {"database_id": FULL_CATALOG_DB_ID}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        results = notion.databases.query(**kwargs)

        for page in results.get("results", []):
            props = page["properties"]
            eng_title_vals = props.get("English Title", {}).get("title", [])
            romaji_vals = props.get("Romaji Title", {}).get("rich_text", [])
            romaji_title = romaji_vals[0].get("plain_text", "") if romaji_vals else ""
            notion_format = props.get("Format", {}).get("select", {}).get("name", "")
            debut_year = str(props.get("Debut Year", {}).get("number") or "")
            studios_vals = props.get("Studios", {}).get("rich_text", [])
            studios_text = studios_vals[0].get("plain_text", "") if studios_vals else ""
            genres_rollup = props.get("Genre Names", {})
            genres = parse_rollup_genres(genres_rollup)
            source = props.get("Source", {}).get("select", {}).get("name", "")

            all_anime.append(
                {
                    "id": page["id"],
                    "eng_title": (eng_title_vals[0].get("plain_text", "") if eng_title_vals else ""),
                    "romaji_title": romaji_title,
                    "format": notion_format,
                    "debut_year": debut_year,
                    "genres": genres,
                    "studios": studios_text,
                    "source": source,
                }
            )

        if not results.get("has_more"):
            break

        start_cursor = results.get("next_cursor")

    return all_anime


def update_notion_studios(anime_id, studios_text):
    """Write normalized studios string to Notion 'Studios' rich_text property."""
    try:
        notion.pages.update(
            page_id=anime_id,
            properties={"Studios": {"rich_text": [{"text": {"content": studios_text}}]}},
        )
        console.print(f"[bold green]Updated studios: {studios_text}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to update studios: {e}[/bold red]")


def normalize_studios(studios_list):
    """De-duplicate while preserving order, then join with comma+space."""
    seen = set()
    unique_ordered = []
    for studio in studios_list:
        if studio not in seen:
            unique_ordered.append(studio)
            seen.add(studio)
    return ", ".join(unique_ordered)


def search_anilist(title, debut_year):
    """Query AniList for studios and related metadata by title/year."""
    query = """
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
          genres
          source
          studios {
            edges {
              node {
                name
                isAnimationStudio
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "search": title,
        "year": int(debut_year) if debut_year.isdigit() else None,
    }
    headers = {"Content-Type": "application/json"}

    # Be polite with API rate limits
    time.sleep(REQUEST_INTERVAL)
    resp = request_with_retry(
        ANILIST_API_URL, headers, json_data={"query": query, "variables": variables}
    )
    if not resp:
        return []
    data = resp.json().get("data", {})
    return data.get("Page", {}).get("media", [])


def is_perfect_match(notion_row, candidate):
    """Strict matching on format, year, romaji title, and source mapping."""
    format_match = candidate.get("format") == FORMAT_MAP_REVERSE.get(notion_row["format"])
    year_match = str(candidate.get("startDate", {}).get("year", "")) == notion_row["debut_year"]
    romaji_match = (candidate.get("title", {}).get("romaji", "") or "").strip().lower() == notion_row[
        "romaji_title"
    ].strip().lower()
    source_anilist = candidate.get("source")
    source_mapped = SOURCE_MAP.get(source_anilist, "Other") if source_anilist else ""
    source_match = source_mapped == notion_row["source"]
    return format_match and year_match and romaji_match and source_match


def main(titles_file: str | None = None):
    """
    Entry point for 'Studios' sync.

    Args:
        titles_file: Optional path to a .txt file with titles to process.
                     Overrides ANIME_TITLES_FILE from .env if provided.
    """
    console.print("[bold white]\n🔗 Studio Sync (AniList → Notion)\n[/bold white]")

    # Load selection (CLI > .env > None)
    selected = load_selected_titles(titles_file)

    # Fetch and optionally filter the Notion list
    notion_anime_list = get_notion_anime()
    notion_anime_list = filter_anime_list(notion_anime_list, selected)

    updated = 0
    total_checked = 0
    log_updated = []
    log_skipped = []

    for notion_anime in notion_anime_list:
        title = notion_anime["romaji_title"] or notion_anime["eng_title"]
        year = notion_anime["debut_year"]
        console.print(f"\n[bold blue]Processing:[/bold blue] {title} ({year})")

        candidates = search_anilist(title, year)
        if not candidates:
            console.print("[bold red]No AniList results found.[/bold red]")
            log_skipped.append(notion_anime)
            continue

        total_checked += 1
        matched = None
        for candidate in candidates:
            if is_perfect_match(notion_anime, candidate):
                matched = candidate
                break

        if matched:
            studios = [
                edge["node"]["name"]
                for edge in matched["studios"]["edges"]
                if edge["node"].get("isAnimationStudio", False)
            ]
            normalized = normalize_studios(studios)
            if normalized != notion_anime["studios"]:
                update_notion_studios(notion_anime["id"], normalized)
                updated += 1
                log_updated.append(
                    {
                        "title": notion_anime["eng_title"],
                        "year": year,
                        "studios": normalized,
                    }
                )
            continue

        log_skipped.append(notion_anime)

    # Export CSV logs
    if log_updated:
        with open(output_dir / "updated_studios.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "year", "studios"])
            writer.writeheader()
            writer.writerows(log_updated)

    if log_skipped:
        with open(output_dir / "skipped_studios.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["eng_title", "format", "debut_year"])
            writer.writeheader()
            for anime in log_skipped:
                writer.writerow(
                    {
                        "eng_title": anime["eng_title"],
                        "format": anime["format"],
                        "debut_year": anime["debut_year"],
                    }
                )

    console.print(f"\n[bold green]✅ Total checked: {total_checked}[/bold green]")
    console.print(f"[bold cyan]📝 Studios updated: {updated}[/bold cyan]")
    if updated == 0:
        console.print("[bold yellow]🔝 No updates needed.[/bold yellow]\n")


if __name__ == "__main__":
    main()
