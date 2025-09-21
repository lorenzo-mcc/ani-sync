"""
Module: anilist_fetcher.py
Description:
    Low-level AniList integration helpers for fetching metadata (GraphQL).

Usage:
    Imported by other modules; not intended to be executed directly.

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * ACCESS_TOKEN
        * ANILIST_API_URL
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from rich.console import Console
from utils.env import validate_env_vars

console = Console()

# === Load .env ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["ACCESS_TOKEN"]
validate_env_vars(REQUIRED_ENV_VARS)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ANILIST_API_URL = os.getenv("ANILIST_API_URL", "https://graphql.anilist.co")


def fetch_anime_info(title):
    """
    Fetches anime information from AniList using the provided title.
    """
    api_url = ANILIST_API_URL
    query = """
    query ($search: String) {
      Page(page: 1, perPage: 10) {
        media(search: $search, type: ANIME) {
          title {
            english
            romaji
          }
          synonyms
          source
          countryOfOrigin
          status
          format
          genres
          coverImage {
            extraLarge
          }
          bannerImage
          startDate {
            year
          }
          airingSchedule {
            nodes {
              episode
              timeUntilAiring
            }
          }
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
    variables = {"search": title}
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.post(
            api_url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]❌ Request failed: {e}[/red]")
        return None

    data = response.json().get("data", {}).get("Page", {}).get("media", [])
    if not data:
        return None

    return data
