import os
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client
from rich.console import Console
from utils.env import validate_env_vars

console = Console()

# === Load .env ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY", "FULL_CATALOGUE_DB_ID"]
validate_env_vars(REQUIRED_ENV_VARS)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
FULL_CATALOGUE_DB_ID = os.getenv("FULL_CATALOGUE_DB_ID")

notion = Client(auth=os.getenv("NOTION_API_KEY"))

# === Flag to country map ===
FLAG_COUNTRY_MAP = {
    "🇯🇵": "Japan",
    "🇰🇷": "South Korea",
    "🇨🇳": "China",
    "🇹🇼": "Taiwan",
    "🇺🇸": "USA",
    "🇨🇦": "Canada",
    "🇬🇧": "United Kingdom",
    "🇫🇷": "France",
}


def get_all_anime():
    all_anime = []
    start_cursor = None

    while True:
        kwargs = {"database_id": FULL_CATALOGUE_DB_ID}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        results = notion.databases.query(**kwargs)

        for page in results.get("results", []):
            props = page["properties"]
            title = props.get("English Title", {}).get("title", [])
            title_text = title[0]["plain_text"] if title else ""
            country = props.get("Country", {}).get("select", {}).get("name", "")
            emoji_icon = page.get("icon", {}).get("emoji", "")
            all_anime.append(
                {
                    "id": page["id"],
                    "title": title_text,
                    "country": country,
                    "flag": emoji_icon,
                }
            )

        if not results.get("has_more"):
            break

        start_cursor = results.get("next_cursor")

    return all_anime


def update_country_property(page_id, correct_country):
    try:
        notion.pages.update(
            page_id=page_id,
            properties={"Country": {"select": {"name": correct_country}}},
        )
        return True
    except Exception as e:
        console.print(f"[red]❌ Error updating {page_id}: {e}[/red]")
        return False


# ====== MAIN FUNCTION ======
def main():
    console.print("[bold white]\n🔗 Country Sync\n[/bold white]")

    anime_list = get_all_anime()
    updated = 0
    total_checked = 0

    for anime in anime_list:
        flag = anime["flag"]
        notion_country = anime["country"]
        title = anime["title"]
        page_id = anime["id"]

        if not flag:
            continue  # No icon, skip

        correct_country = FLAG_COUNTRY_MAP.get(flag)
        if not correct_country:
            continue  # Flag not in map

        total_checked += 1

        if notion_country != correct_country:
            console.print(
                f"\n[yellow]Updating '{title}' → {notion_country or '(blank)'} -> {correct_country}[/yellow]"
            )
            success = update_country_property(page_id, correct_country)
            if success:
                updated += 1
            else:
                console.print(f"[red]Failed to update {title}[/red]")

    console.print(f"\n[bold green]✅ Total checked: {total_checked}[/bold green]")
    console.print(f"[bold cyan]📝 Country updated: {updated}[/bold cyan]")
    if updated == 0:
        console.print("[bold yellow]🗑️ No updates needed.[/bold yellow]\n")


if __name__ == "__main__":
    main()
