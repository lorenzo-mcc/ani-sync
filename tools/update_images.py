"""
Module: update_images.py
Description:
    Syncs AniList banner and cover images into Notion; updates page header cover and the 'Cover' (Files & media) property.

Usage:
    python cli.py tools update-images [--titles file.txt]

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * ANILIST_API_URL
        * FULL_CATALOG_DB_ID
        * NOTION_API_KEY
        * OVERWRITE_HEADER_COVER
        * OVERWRITE_PROPERTY_COVER
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

# Overwrite behaviours
OVERWRITE_HEADER_COVER = os.getenv("OVERWRITE_HEADER_COVER", "true").lower() == "true"
OVERWRITE_PROPERTY_COVER = os.getenv("OVERWRITE_PROPERTY_COVER", "true").lower() == "true"

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
      bannerImage
      coverImage {
        extraLarge
        large
      }
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


def request_with_retry(url, headers, json_data=None, retries=3, delay=2):
    """Perform a POST request with retries in case of network/server errors."""
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
    """Fetch anime entries from the Notion database."""
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
            eng_title = eng_title_vals[0].get("plain_text", "") if eng_title_vals else ""
            romaji_vals = props.get("Romaji Title", {}).get("rich_text", [])
            romaji_title = romaji_vals[0].get("plain_text", "") if romaji_vals else ""
            notion_format = props.get("Format", {}).get("select", {}).get("name", "")
            debut_year = str(props.get("Debut Year", {}).get("number") or "")

            header_has_cover = bool(page.get("cover"))
            files_prop = props.get("Cover")
            files_prop_exists = files_prop is not None and files_prop.get("type") == "files"
            files_prop_has_value = files_prop_exists and bool(files_prop.get("files", []))

            all_anime.append(
                {
                    "id": page["id"],
                    "eng_title": eng_title.strip(),
                    "romaji_title": romaji_title.strip(),
                    "format": notion_format.strip(),
                    "debut_year": debut_year.strip(),
                    "header_has_cover": header_has_cover,
                    "files_prop_exists": files_prop_exists,
                    "files_prop_has_value": files_prop_has_value,
                }
            )

        if not results.get("has_more"):
            break
        start_cursor = results.get("next_cursor")

    return all_anime


def update_page_header_cover(page_id, banner_url):
    """Update the Notion page cover (banner image)."""
    try:
        notion.pages.update(
            page_id=page_id,
            cover={"type": "external", "external": {"url": banner_url}},
        )
        console.print("[bold green]✅ Header cover (page.cover) updated[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to update header cover: {e}[/bold red]")


def update_property_files_cover(page_id, file_url):
    """Update the Notion 'Cover' property (Files & media) with AniList cover image."""
    files_payload = [
        {
            "type": "external",
            "name": "AniList Cover",
            "external": {"url": file_url},
        }
    ]
    try:
        notion.pages.update(
            page_id=page_id,
            properties={"Cover": {"type": "files", "files": files_payload}},
        )
        console.print("[bold green]✅ Property Cover (files) updated[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to update property 'Cover': {e}[/bold red]")


def search_anilist(title, debut_year):
    """Search AniList for a given anime title and debut year."""
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
    """Render a comparison table between Notion entry and AniList candidates."""
    for idx, candidate in enumerate(candidates, start=1):
        title_data = candidate.get("title") or {}
        cov = candidate.get("coverImage") or {}
        banner = candidate.get("bannerImage") or "—"
        table = Table(title=f"[{idx}] AniList Match", expand=True)
        table.add_column("Field", style="cyan", justify="center")
        table.add_column("Notion", style="green", overflow="fold")
        table.add_column("AniList", style="yellow", overflow="fold")

        table.add_row(
            "Title",
            f"{notion_anime['eng_title']} / {notion_anime['romaji_title']}",
            f"{title_data.get('english', '—')} / {title_data.get('romaji', '')}",
        )
        table.add_row("Format", notion_anime["format"], candidate.get("format", "N/A"))
        table.add_row(
            "Debut Year",
            notion_anime["debut_year"],
            str(candidate.get("startDate", {}).get("year", "")),
        )
        table.add_row("bannerImage", "—", banner or "—")
        table.add_row(
            "coverImage.extraLarge",
            "—",
            cov.get("extraLarge") or cov.get("large") or "—",
        )

        console.print(table)


def main(titles_file: str | None = None):
    """
    Entry point for updating Notion covers.

    Args:
        titles_file: Optional path to a .txt file containing titles to process.
                     Overrides ANIME_TITLES_FILE from .env if provided.
    """
    console.print("\n[bold white]🖼️  Banner + Files Cover Sync (AniList → Notion)[/bold white]\n")

    # Load selected titles (CLI > .env > None)
    selected = load_selected_titles(titles_file)

    # Fetch and filter anime list
    anime_list = get_notion_anime()
    anime_list = filter_anime_list(anime_list, selected)

    updated_header = 0
    updated_files = 0
    not_matched = []

    for idx, anime in enumerate(anime_list, start=1):
        title = anime["romaji_title"] or anime["eng_title"] or "Untitled"
        year = anime["debut_year"]
        format_notion = anime["format"]

        console.print(f"[bold blue]{idx}/{len(anime_list)} ➔  Processing:[/bold blue] {title}")

        needs_header = (not anime["header_has_cover"]) or OVERWRITE_HEADER_COVER
        needs_files = (
            anime["files_prop_exists"]
            and (OVERWRITE_PROPERTY_COVER or not anime["files_prop_has_value"])
        )

        if not (needs_header or needs_files):
            console.print("[dim]Nothing to do (already set, overwrite disabled).[/dim]")
            continue

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
            romaji = (title_data.get("romaji") or "").strip().lower()
            anilist_format = c.get("format", "")
            anilist_year = str(c.get("startDate", {}).get("year", ""))

            if (
                (english == anime["eng_title"].lower() or romaji == anime["romaji_title"].lower())
                and (desired_format is None or anilist_format == desired_format)
                and (not year or anilist_year == year)
            ):
                perfect_matches.append(c)

        selected_match = None
        if len(perfect_matches) == 1:
            selected_match = perfect_matches[0]
            console.print(f"[bold green]Auto-matched:[/bold green] {title}")
        else:
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
            selected_match = candidates[choice - 1]

        banner_url = selected_match.get("bannerImage")
        cover_block = selected_match.get("coverImage") or {}
        cover_url = cover_block.get("extraLarge") or cover_block.get("large")

        if needs_header and banner_url:
            console.print(f"[dim]Setting header cover from bannerImage:[/dim] {banner_url}")
            update_page_header_cover(anime["id"], banner_url)
            updated_header += 1

        if needs_files and cover_url:
            console.print(
                f"[dim]Setting Files & media Cover from coverImage.extraLarge:[/dim] {cover_url}"
            )
            update_property_files_cover(anime["id"], cover_url)
            updated_files += 1

    console.print(
        f"\n[bold green]✅ Updated header covers:[/bold green] {updated_header}   "
        f"[bold green]✅ Updated Files & media covers:[/bold green] {updated_files}\n"
    )


if __name__ == "__main__":
    main()
