import re
from datetime import datetime, timedelta

def parse_season_from_name(anime_name: str) -> int | None:
    """
    Extracts the season number from the anime title if it contains '(S#)'.
    Returns the season number - 1, or None if not found.
    """
    season_regex = r"\(S(\d+)\)"  # Matches (S1), (S2), etc.
    match = re.search(season_regex, anime_name)
    if match:
        try:
            season_num = int(match.group(1))  # Extracts "2" from "(S2)"
            return season_num - 1
        except ValueError:
            return None
    return None

def format_data_for_notion(anime_info: dict, searched_title: str) -> dict:
    """
    Formats anime data from AniList into a structure compatible with Notion.
    """
    # Allowed genres for filtering
    allowed_genres = [
        "Action", "Adventure", "Comedy", "Drama", "Ecchi", "Fantasy",
        "Horror", "Mecha", "Mystery", "Music", "Psychological", "Romance",
        "Sci-Fi", "Slice of Life", "Sports", "Supernatural", "Thriller"
    ]

    # Extract season from title
    season_value = parse_season_from_name(searched_title)

    # Extract cover and banner
    banner = anime_info.get('bannerImage')
    cover = anime_info.get('coverImage', {}).get('extraLarge', None)

    # Extract title
    title = anime_info.get('title', {}).get('english') or anime_info.get('title', {}).get('romaji') or "Unknown"

    # Map format
    raw_format = anime_info.get('format', 'N/A')
    format_map = {
        "TV": "TV",
        "MOVIE": "Movie",
        "TV_SHORT": "TV Short",
        "OVA": "OVA",
        "ONA": "ONA",
        "SPECIAL": "Special"
    }
    formatted_format = format_map.get(raw_format, raw_format)

    # Extract other fields
    start_date = anime_info.get('startDate', {})
    year = start_date.get('year', '')
    formatted_year = str(year) if year else ""

    studio_edges = anime_info.get('studios', {}).get('edges', [])
    studios_filtered = {
        edge.get('node', {}).get('name', 'N/A')
        for edge in studio_edges
        if edge.get('node', {}).get('isAnimationStudio', False)
    }
    formatted_studios = ", ".join(studios_filtered) if studios_filtered else ""

    # Handle airing schedule
    """
    next_episode = None
    airing_at = None
    if formatted_format == "TV" and anime_info.get('status') == "RELEASING":
        airing_schedule = anime_info.get('airingSchedule', {}).get('nodes', [])
        future_episodes = [ep for ep in airing_schedule if ep.get('timeUntilAiring', -1) > 0]
        if future_episodes:
            next_ep_data = future_episodes[0]
            next_episode = next_ep_data.get('episode', None)
            time_until_airing = next_ep_data.get('timeUntilAiring', None)
            if time_until_airing and isinstance(time_until_airing, int):
                airing_date = datetime.now() + timedelta(seconds=time_until_airing)
                airing_at = airing_date.isoformat()
    """
    genres = anime_info.get('genres', [])
    filtered_genres = [genre for genre in genres if genre in allowed_genres]
    formatted_genres = ", ".join(filtered_genres) if filtered_genres else ""

    country_code = anime_info.get('countryOfOrigin', '')
    country_flags = {
        "JP": "🇯🇵",
        "KR": "🇰🇷",
        "CN": "🇨🇳",
        "TW": "🇹🇼",
        "US": "🇺🇸",
        "CA": "🇨🇦",
        "GB": "🇬🇧",
        "FR": "🇫🇷",
    }

    icon_emoji = country_flags.get(country_code, "🌐")

    return {
        "Title": title,
        "Cover": cover,
        "Banner": banner,
        "Format": formatted_format,
        "Debut Year": formatted_year,
        "Studios": formatted_studios,
        "Genres": formatted_genres,
        # "Watched Seasons": season_value,
        "Icon": icon_emoji
    }
