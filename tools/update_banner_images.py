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

console = Console(force_terminal=True, color_system="truecolor", soft_wrap=True)

# === Load environment ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
output_dir = base_path / "output"
output_dir.mkdir(parents=True, exist_ok=True)

load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY", "FULL_CATALOGUE_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

# === Notion and AniList config ===
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
FULL_CATALOGUE_DB_ID = os.getenv("FULL_CATALOGUE_DB_ID")
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
      bannerImage
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
    all_anime = []
    start_cursor = None

    while True:
        kwargs = {"database_id": FULL_CATALOGUE_DB_ID}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        results = notion.databases.query(**kwargs)

        for page in results.get("results", []):
            if page.get("cover"):  # Skip if cover already set
                eng_title_vals = page["properties"].get("English Title", {}).get("title", [])
                eng_title = (
                    eng_title_vals[0].get("plain_text", "") if eng_title_vals else "Untitled"
                )
                console.print(f"[dim]Skipping '{eng_title}': cover already set[/dim]")
                continue

            props = page["properties"]
            eng_title_vals = props.get("English Title", {}).get("title", [])
            eng_title = eng_title_vals[0].get("plain_text", "") if eng_title_vals else ""
            romaji_vals = props.get("Romaji Title", {}).get("rich_text", [])
            romaji_title = romaji_vals[0].get("plain_text", "") if romaji_vals else ""
            notion_format = props.get("Format", {}).get("select", {}).get("name", "")
            debut_year = str(props.get("Debut Year", {}).get("number") or "")

            all_anime.append(
                {
                    "id": page["id"],
                    "eng_title": eng_title.strip(),
                    "romaji_title": romaji_title.strip(),
                    "format": notion_format.strip(),
                    "debut_year": debut_year.strip(),
                }
            )

        if not results.get("has_more"):
            break

        start_cursor = results.get("next_cursor")

    return all_anime


def update_page_cover(page_id, banner_url):
    try:
        notion.pages.update(
            page_id=page_id, cover={"type": "external", "external": {"url": banner_url}}
        )
        console.print("[bold green]✅ Cover updated[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to update cover: {e}[/bold red]")


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

        console.print(table)


def main():
    console.print("\n[bold white]🖼️  Banner Cover Sync[/bold white]\n")

    anime_list = get_notion_anime()
    updated = 0
    not_matched = []

    for idx, anime in enumerate(anime_list, start=1):
        title = anime["romaji_title"] or anime["eng_title"]
        year = anime["debut_year"]
        format_notion = anime["format"]

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
            romaji = (title_data.get("romaji") or "").strip().lower()
            anilist_format = c.get("format", "")
            anilist_year = str(c.get("startDate", {}).get("year", ""))

            if (
                (english == anime["eng_title"].lower() or romaji == anime["romaji_title"].lower())
                and anilist_format == desired_format
                and anilist_year == year
            ):
                perfect_matches.append(c)

        if len(perfect_matches) == 1:
            matched = perfect_matches[0]
            banner_url = matched.get("bannerImage")
            if banner_url:
                console.print(
                    f"[bold green]Auto-matched:[/bold green] {title} → [italic]{banner_url}[/italic]"
                )
                update_page_cover(anime["id"], banner_url)
                updated += 1
            else:
                console.print(f"[bold yellow]No banner image found for:[/bold yellow] {title}")
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
        banner_url = selected.get("bannerImage")
        if banner_url:
            update_page_cover(anime["id"], banner_url)
            updated += 1
        else:
            console.print("[bold yellow]No banner image found for selected match.[/bold yellow]")

    if not_matched:
        csv_path = output_dir / "unmatched_covers.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["eng_title", "format", "debut_year"])
            writer.writeheader()
            for anime in not_matched:
                writer.writerow(
                    {
                        "eng_title": anime["eng_title"],
                        "format": anime["format"],
                        "debut_year": anime["debut_year"],
                    }
                )
        console.print(f"\n[bold yellow]📄 Unmatched titles saved to:[/bold yellow] {csv_path}")

    console.print(f"\n[bold green]✅ Total updated covers: {updated}[/bold green]\n")


if __name__ == "__main__":
    main()
