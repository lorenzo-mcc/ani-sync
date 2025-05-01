from notion_client import Client
import os
from pathlib import Path
from rich.console import Console
from dotenv import load_dotenv
from utils.env import validate_env_vars

console = Console()

# === Load .env ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["NOTION_API_KEY"]
validate_env_vars(REQUIRED_ENV_VARS)

notion = Client(auth=os.getenv("NOTION_API_KEY"))


def get_page_id_by_title(database_id, title_to_check):
    try:
        query = notion.databases.query(
            database_id=database_id,
            filter={"property": "English Title", "title": {"equals": title_to_check}},
        )
        for result in query.get("results", []):
            notion_title = result["properties"]["English Title"]["title"][0]["text"]["content"]
            if notion_title.strip().lower() == title_to_check.strip().lower():
                return result["id"]
        return None
    except Exception as e:
        console.print(f"[red]❌ Error while retrieving page ID: {e}[/red]")
        return None


def get_genre_ids(genre_names, genre_database_id):
    try:
        genre_ids = []
        for genre_name in genre_names:
            query = notion.databases.query(
                database_id=genre_database_id,
                filter={"property": "Name", "rich_text": {"equals": genre_name}},
            )
            results = query.get("results", [])
            if results:
                genre_ids.append(results[0]["id"])
        return genre_ids
    except Exception as e:
        console.print(f"[red]❌ Error while retrieving genre IDs: {e}[/red]")
        return []


def create_notion_page(database_id, properties, genre_database_id, force=False):
    try:
        title_to_check = properties.get("English Title", "").strip()
        existing_page_id = get_page_id_by_title(database_id, title_to_check)

        if existing_page_id:
            if not force:
                console.print(
                    f"\n[yellow]⚠️  Skipping duplicate:[/yellow] [bold]{title_to_check}[/bold] already exists in Notion"
                )
                return False, "skipped"
            else:
                console.print(f"🔁 Updating existing Notion page: '[bold]{title_to_check}[/bold]'")

        genre_names = properties.get("Genres", "").split(", ")
        genre_ids = get_genre_ids(genre_names, genre_database_id)

        format_excluded = ["Movie", "Special"]

        notion_properties = {
            "English Title": {"title": [{"text": {"content": title_to_check or "Unknown"}}]},
            "Romaji Title": {
                "rich_text": [{"text": {"content": properties.get("Romaji Title", "Unknown")}}]
            },
            "Source": {"select": {"name": properties.get("Source", "N/A")}},
            "Cover": {
                "files": [
                    {
                        "type": "external",
                        "name": "Cover",
                        "external": {"url": properties.get("Cover", "")},
                    }
                ]
            },
            "Country": {"select": {"name": properties.get("Country", "N/A")}},
            "Format": {"select": {"name": properties.get("Format", "N/A")}},
            "Debut Year": {"number": properties.get("Debut Year", None)},
            "Studios": {"rich_text": [{"text": {"content": properties.get("Studios", "")}}]},
            "Genres": {"relation": [{"id": genre_id} for genre_id in genre_ids]},
        }

        if properties.get("Format") not in format_excluded:
            notion_properties["Watched Seasons"] = {"number": properties.get("Watched Seasons", 0)}
            notion_properties["Watched Episodes"] = {
                "number": properties.get("Watched Episodes", 0)
            }

        banner_url = properties.get("Banner", None)

        if existing_page_id and force:
            notion.pages.update(
                page_id=existing_page_id,
                icon={"type": "emoji", "emoji": properties.get("Icon", "🌐")},
                cover=(
                    {"type": "external", "external": {"url": banner_url}} if banner_url else None
                ),
                properties=notion_properties,
            )
            return True, "updated"
        else:
            notion.pages.create(
                parent={"database_id": database_id},
                icon={"type": "emoji", "emoji": properties.get("Icon", "🌐")},
                cover=(
                    {"type": "external", "external": {"url": banner_url}} if banner_url else None
                ),
                properties=notion_properties,
            )
            return True, "created"

    except Exception as e:
        console.print(f"[red]❌ Notion sync failed: {e}[/red]")
        return False, "error"
