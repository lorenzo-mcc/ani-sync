from notion_client import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
notion = Client(auth=os.getenv('NOTION_API_KEY'))


def get_genre_ids(genre_names, genre_database_id):
    """
    Retrieves the IDs of genre pages from the related database in Notion.

    :param genre_names: List of genre names (e.g., ["Action", "Adventure"]).
    :param genre_database_id: ID of the related database for genres.
    :return: List of IDs for the corresponding genre pages.
    """
    try:
        genre_ids = []
        for genre_name in genre_names:
            query = notion.databases.query(
                **{
                    "database_id": genre_database_id,
                    "filter": {
                        "property": "Name",  # Name of the genre property in the database
                        "rich_text": {
                            "equals": genre_name
                        }
                    }
                }
            )
            results = query.get("results", [])
            if results:
                genre_ids.append(results[0]["id"])  # Get the ID of the first match
            else:
                print(f"Warning: The genre '{genre_name}' was not found in the related database.")
        return genre_ids
    except Exception as e:
        print(f"Error while retrieving genre IDs: {e}")
        return []


def create_notion_page(database_id, properties, genre_database_id):
    """
    Creates a new page in the Notion database, including handling relations for genres.

    :param database_id: ID of the main Notion database.
    :param properties: Data formatted for the page from the formatter.
    :param genre_database_id: ID of the related database for genres.
    """
    try:
        # Retrieve genre IDs from the related database
        genre_names = properties.get("Genres", "").split(", ")
        genre_ids = get_genre_ids(genre_names, genre_database_id)

        # Determine if "Watched Seasons" and "Watched Episodes" should be included
        format_excluded = ["Movie", "Special"]

        # Prepare properties for the new page
        notion_properties = {
            "Title": {"title": [{"text": {"content": properties.get("Title", "Unknown")}}]},
            "Cover": {
                "files": [{
                    "type": "external",
                    "name": "Cover",
                    "external": {"url": properties.get("Cover", "")}
                }]
            },
            "Format": {"select": {"name": properties.get("Format", "N/A")}},
            "Debut Year": {"rich_text": [{"text": {"content": properties.get("Debut Year", "")}}]},
            "Studios": {"rich_text": [{"text": {"content": properties.get("Studios", "")}}]},
            "Genres": {"relation": [{"id": genre_id} for genre_id in genre_ids]}
        }

        # Include "Watched Seasons" and "Watched Episodes" only when "Format" is neither "Movie" nor "Special"
        if properties.get("Format") not in format_excluded:
            notion_properties["Watched Seasons"] = {"number": properties.get("Watched Seasons", 0)}
            notion_properties["Watched Episodes"] = {"number": properties.get("Watched Episodes", 0)}
        
        # Set the page cover if a banner is provided
        banner_url = properties.get("Banner", None)

        # Create the page in Notion
        notion.pages.create(
            parent={"database_id": database_id},
            icon={"type": "emoji", "emoji": properties.get("Icon", "🌐")},  # Use the icon provided or default
            cover={"type": "external", "external": {"url": banner_url}} if banner_url else None,
            properties=notion_properties
        )
        print(f"\033[42mPage successfully created for '{properties.get('Title', 'Unknown')}'.\033[0m")

    except Exception as e:
        print(f"\033[41mError while creating the page in Notion: {e}.\033[0m")
