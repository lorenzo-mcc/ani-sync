import os
from notion_client import Client
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from utils.env import validate_env_vars

console = Console()

# === Load .env ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY", "FULL_CATALOGUE_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

notion = Client(auth=os.getenv("NOTION_API_KEY"))

# Full Catalogue database ID
FULL_CATALOGUE_DB_ID = os.getenv("FULL_CATALOGUE_DB_ID")

# Property names
WATCHED_RELATION = os.getenv("WATCHED_RELATION", "Anime Watched")
GENRES_SOURCE = os.getenv("GENRES_SOURCE", "Genres")
GENRES_TARGET = os.getenv("GENRES_TARGET", "Genres (Anime Watched)")


# Get all anime with "Anime Watched" not empty
def get_watched_anime():
    all_items = []
    start_cursor = None

    while True:
        response = notion.databases.query(
            database_id=FULL_CATALOGUE_DB_ID,
            filter={"property": WATCHED_RELATION, "relation": {"is_not_empty": True}},
            start_cursor=start_cursor,
            page_size=100,
        )

        all_items.extend(response["results"])

        if response.get("has_more"):
            start_cursor = response["next_cursor"]
        else:
            break

    return all_items


# ====== MAIN FUNCTION ======
def main():
    console.print("[bold white]\n🌟 Anime Watched Genres Sync\n[/bold white]")

    watched_anime = get_watched_anime()
    total_checked = len(watched_anime)
    updated_count = 0
    updated_titles = []

    console.print(
        f"[bold magenta]📂 Found {total_checked} Watched Anime in the Database.[/bold magenta]\n"
    )

    for anime in tqdm(watched_anime, desc="🔁 Updating genres"):
        anime_id = anime["id"]

        source_genres = anime["properties"].get(GENRES_SOURCE, {}).get("relation", [])
        source_ids = [g["id"] for g in source_genres]

        current_genres = anime["properties"].get(GENRES_TARGET, {}).get("relation", [])
        current_ids = [g["id"] for g in current_genres]

        if set(source_ids) == set(current_ids):
            continue  # genres already synchronized

        updated_ids = sorted({*source_ids, *current_ids})

        try:
            notion.pages.update(
                page_id=anime_id,
                properties={GENRES_TARGET: {"relation": [{"id": id_} for id_ in updated_ids]}},
            )
            title_vals = anime["properties"].get("English Title", {}).get("title", [])
            if title_vals:
                updated_titles.append(
                    next(
                        (t.get("plain_text") for t in title_vals if "plain_text" in t),
                        "Unknown Title",
                    )
                )

            updated_count += 1
        except Exception as e:
            console.print(f"[bold red]❌ Error updating anime {anime_id}[/bold red]\n{e}")

    # Save updated titles to log file
    output_dir = base_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "genres_updated.log"
    with open(log_path, "w", encoding="utf-8") as f:
        for title in updated_titles:
            f.write(title + "\n")

    console.print(f"\n[bold green]✅ Total checked: {total_checked}[/bold green]")
    console.print(f"[bold cyan]📝 Anime updated: {updated_count}[/bold cyan]")
    if updated_count == 0:
        console.print(
            "[bold yellow]🔝 No updates were needed. Everything is already synced.[/bold yellow]\n"
        )
    else:
        console.print(f"[dim]📁 Log saved to: {log_path}[/dim]\n")

    return updated_count


if __name__ == "__main__":
    main()
