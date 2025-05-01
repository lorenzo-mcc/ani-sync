import requests
import os
import time
import csv
import json
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from datetime import datetime
from notion_client import Client
from utils.env import validate_env_vars

console = Console()

# === Setup paths and environment ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
output_dir = base_path / "output"
output_dir.mkdir(parents=True, exist_ok=True)

load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY", "FULL_CATALOGUE_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
notion = Client(auth=os.getenv("NOTION_API_KEY"))
FULL_CATALOGUE_DB_ID = os.getenv("FULL_CATALOGUE_DB_ID")

VERBOSE = os.getenv("VERBOSE", "True")
DEBUG_OUTPUT = os.getenv("DEBUG_OUTPUT", "True")
USE_CACHE = os.getenv("USE_CACHE", "True")

REQUEST_INTERVAL = float(os.getenv("REQUEST_INTERVAL", 60 / 28))  # Keep to 28 requests per minute

ANILIST_QUERY = """
query ($search: String, $year: Int) {
  Page(page: 1, perPage: 10) {
    media(search: $search, type: ANIME, seasonYear: $year) {
      id
    }
  }
}
"""


def request_with_retry(url, headers, json_data=None, method="post", retries=3, delay=3):
    for attempt in range(1, retries + 1):
        try:
            if method == "post":
                response = requests.post(url, headers=headers, json=json_data, timeout=10)
            else:
                response = requests.patch(url, headers=headers, json=json_data, timeout=10)

            if response.status_code in (200, 429):
                return response

            if VERBOSE:
                console.log(f"[retry:{attempt}] Unexpected status: {response.status_code}")
        except requests.RequestException as e:
            if VERBOSE:
                console.log(f"[retry:{attempt}] Request error: {e}")

        time.sleep(delay)
    return None


def get_notion_anime() -> list[dict]:
    anime_list = []

    try:
        results = notion.databases.query(database_id=FULL_CATALOGUE_DB_ID)
        while True:
            for page in results.get("results", []):
                props = page["properties"]
                eng_vals = props.get("English Title", {}).get("title", [])
                romaji_vals = props.get("Romaji Title", {}).get("rich_text", [])
                eng_title = eng_vals[0].get("plain_text", "") if eng_vals else ""
                romaji_title = romaji_vals[0].get("plain_text", "") if romaji_vals else ""
                debut_year = props.get("Debut Year", {}).get("number")
                format_val = props.get("Format", {}).get("select", {}).get("name", "")
                if romaji_title and debut_year:
                    anime_list.append(
                        {
                            "romaji": romaji_title,
                            "english": eng_title,
                            "year": int(debut_year),
                            "format": format_val,
                        }
                    )

            if not results.get("has_more"):
                break

            results = notion.databases.query(
                database_id=FULL_CATALOGUE_DB_ID,
                start_cursor=results.get("next_cursor"),
            )

    except Exception as e:
        console.print(f"[red]❌ Error querying Notion: {e.__class__.__name__} - {e}[/red]")

    return anime_list


def search_anilist(title: str, year: int) -> tuple[list[dict], requests.Response | None]:
    query = ANILIST_QUERY

    variables = {"search": title, "year": int(year)}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    url = "https://graphql.anilist.co"
    resp = request_with_retry(url, headers, json_data={"query": query, "variables": variables})
    if not resp:
        return [], None
    return resp.json().get("data", {}).get("Page", {}).get("media", []), resp


def main() -> None:
    console.print("[bold white]\n🔁 Full Anime Title Checker[/bold white]\n")

    notion_anime_list = get_notion_anime()
    console.print(
        f"[bold magenta]📦 Loaded {len(notion_anime_list)} anime from Notion[/bold magenta]\n"
    )

    unresolved_rows = []
    debug_entries = []
    total_found = 0
    skipped_count = 0
    rate_limit_hits = 0

    cache_file = output_dir / "resolved_cache.json"
    if USE_CACHE and cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            resolved_cache = set(json.load(f))
    else:
        resolved_cache = set()

    terminal_width = console.size.width
    progress_bar = tqdm(
        notion_anime_list, desc="🔍 AniList Lookup", unit="anime", ncols=terminal_width
    )
    last_request_time = datetime.min

    for anime in progress_bar:
        romaji = anime["romaji"]
        eng_title = anime["english"]
        year = anime["year"]
        fmt = anime["format"]
        short_title = (
            romaji if len(romaji) <= terminal_width - 50 else romaji[: terminal_width - 52] + "…"
        )

        if USE_CACHE and romaji in resolved_cache:
            progress_bar.set_postfix_str(f"{short_title} (cached)")
            continue

        now = datetime.now()
        elapsed = (now - last_request_time).total_seconds()
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        last_request_time = datetime.now()

        progress_bar.set_postfix_str(f"{short_title}")

        if not year:
            skipped_count += 1
            continue

        while True:
            results, resp = search_anilist(romaji, year)
            if resp and resp.status_code == 429:
                rate_limit_hits += 1
                progress_bar.write(f"⏳ Rate limit for '{romaji}' → waiting 60s")
                time.sleep(60)
                continue
            break

        if results:
            total_found += 1
            if USE_CACHE:
                resolved_cache.add(romaji)
        else:
            reason = "not_found" if resp else "no_response"
            unresolved_rows.append(
                {"Title": eng_title, "Year": year, "Format": fmt, "Reason": reason}
            )
            if not resp or not results:
                debug_entries.append(
                    {
                        "romaji": romaji,
                        "english": eng_title,
                        "year": year,
                        "format": fmt,
                        "reason": reason,
                        "query": {
                            "query": ANILIST_QUERY,
                            "variables": {"search": romaji, "year": year},
                        },
                    }
                )

    csv_file_path = output_dir / "unresolved.csv"
    json_debug_path = output_dir / "unresolved_debug.json"
    json_debug_flat_path = output_dir / "unresolved_debug_flat.json"

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Title", "Year", "Format", "Reason"])
        writer.writeheader()
        writer.writerows(unresolved_rows)

    if DEBUG_OUTPUT:
        with open(json_debug_path, "w", encoding="utf-8") as jsonfile:
            json.dump(debug_entries, jsonfile, indent=2, ensure_ascii=False)

        with open(json_debug_flat_path, "w", encoding="utf-8") as jsonfile:
            json.dump(
                debug_entries,
                jsonfile,
                indent=None,
                separators=(",", ":"),
                ensure_ascii=False,
            )

        console.print(f"[dim]📝 Debug JSON saved: {json_debug_path}[/dim]")
        console.print(f"[dim]📝 Flat JSON saved: {json_debug_flat_path}[/dim]")
    else:
        console.print("[dim]ℹ️ Debug JSON output skipped[/dim]")

    if USE_CACHE:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(sorted(resolved_cache), f, indent=2, ensure_ascii=False)

    console.print("\n[bold white]📊 Final Report[/bold white]")
    console.print(f"[bold green]✅ Titles found: {total_found}[/bold green]")
    console.print(f"[bold cyan]⏭️  Titles skipped (no year): {skipped_count}[/bold cyan]")
    console.print(f"[bold yellow]❌ Titles not found: {len(unresolved_rows)}[/bold yellow]")
    console.print(f"[bold red]🚩 Rate limit hits: {rate_limit_hits}[/bold red]")
    console.print(f"[dim]📁 CSV saved: {csv_file_path}[/dim]")


if __name__ == "__main__":
    main()
