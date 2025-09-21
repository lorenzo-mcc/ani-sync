"""
Module: formatter.py
Description:
    Formatting helpers to transform AniList/Notion payloads into normalized records.

Usage:
    Imported by other modules; not intended to be executed directly.

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * None
"""

import re
import langdetect


def parse_season_from_name(anime_name: str) -> int | None:
    """
    Extracts the season number from the anime title if it contains '(S#)'.
    Returns the season number - 1, or None if not found.
    """
    season_regex = r"\(S(\d+)\)"  # Matches (S1), (S2), etc.
    match = re.search(season_regex, anime_name)
    if match:
        try:
            season_num = int(match.group(1))
            return season_num - 1
        except ValueError:
            return None
    return None


def is_english_ascii(s, min_length=3):
    if not s.isascii():
        return False
    if len(s.strip()) < min_length:
        return False
    try:
        lang = langdetect.detect(s)
        return lang == "en"
    except langdetect.lang_detect_exception.LangDetectException:
        # Happens if string is too short or undetectable
        return False


def format_data_for_notion(anime_info: dict, full_title: str = "") -> dict:

    allowed_genres = [
        "Action",
        "Adventure",
        "Comedy",
        "Drama",
        "Ecchi",
        "Fantasy",
        "Horror",
        "Mecha",
        "Mystery",
        "Music",
        "Psychological",
        "Romance",
        "Sci-Fi",
        "Slice of Life",
        "Sports",
        "Supernatural",
        "Thriller",
    ]

    season_value = 0
    season_match = re.search(r"\(S(\d+)\)", full_title)
    if season_match:
        try:
            season_value = int(season_match.group(1)) - 1
        except ValueError:
            season_value = 0

    banner = anime_info.get("bannerImage")
    cover = anime_info.get("coverImage", {}).get("extraLarge")

    title_data = anime_info.get("title", {})
    english = title_data.get("english")
    romaji = title_data.get("romaji")
    synonyms = anime_info.get("synonyms", [])

    # Prefer English, then check synonyms for ASCII-only string, then Romaji, then fallback
    synonym_fallback = next((s for s in synonyms if is_english_ascii(s)), None)

    english_title = (english or synonym_fallback or romaji or full_title or "Unknown").strip()

    raw_format = anime_info.get("format", "N/A")
    format_map = {
        "TV": "TV",
        "TV_SHORT": "TV Short",
        "MOVIE": "Movie",
        "OVA": "OVA",
        "ONA": "ONA",
        "SPECIAL": "Special",
    }
    formatted_format = format_map.get(raw_format, raw_format)

    year = anime_info.get("startDate", {}).get("year")
    formatted_year = year if isinstance(year, int) else None

    studios = {
        edge.get("node", {}).get("name", "N/A")
        for edge in anime_info.get("studios", {}).get("edges", [])
        if edge.get("node", {}).get("isAnimationStudio", False)
    }
    formatted_studios = ", ".join(sorted(studios)) if studios else ""

    genres = anime_info.get("genres", [])
    filtered_genres = [g for g in genres if g in allowed_genres]
    formatted_genres = ", ".join(filtered_genres)

    country_code = anime_info.get("countryOfOrigin", "")
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
    country_names = {
        "JP": "Japan",
        "KR": "South Korea",
        "CN": "China",
        "TW": "Taiwan",
        "US": "USA",
        "CA": "Canada",
        "GB": "United Kingdom",
        "FR": "France",
    }
    icon_emoji = country_flags.get(country_code, "🌐")
    formatted_country = country_names.get(country_code, "N/A")

    # Source mapping
    source_raw = anime_info.get("source")
    source_map = {
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
    source = source_map.get(source_raw, "Other") if source_raw else "N/A"

    return {
        "English Title": english_title,
        "Romaji Title": (romaji or "").strip(),
        "Source": source,
        "Cover": cover,
        "Banner": banner,
        "Country": formatted_country,
        "Format": formatted_format,
        "Debut Year": formatted_year,
        "Studios": formatted_studios,
        "Genres": formatted_genres,
        "Seasons Watched": season_value,
        "Icon": icon_emoji,
    }
