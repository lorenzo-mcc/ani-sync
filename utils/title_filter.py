"""
Utility functions for filtering anime lists based on user-provided titles.

This module provides two main helpers:
- load_selected_titles: loads a set of titles from CLI or .env
- filter_anime_list: filters a Notion anime list against the selected titles

Priority of selection:
1. CLI argument (--titles)
2. .env variable (ANIME_TITLES_FILE)
3. None (process ALL anime)
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, List, Optional, Set, Dict, Any


def _normalize(s: str) -> str:
    """Normalize a string for comparison: trim spaces + lowercase."""
    return (s or "").strip().lower()


def load_selected_titles(cli_file: Optional[str] = None) -> Optional[Set[str]]:
    """
    Load titles from a .txt file (one per line).
    - CLI argument (--titles) overrides .env
    - If both are missing, return None (no filter → process all anime)

    Returns:
        Set of normalized titles (lowercased, stripped), or None if no file.
    """
    file_path = cli_file or os.getenv("ANIME_TITLES_FILE")
    if not file_path:
        return None

    p = Path(file_path)

    if not p.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        p = (project_root / p).resolve()

    if not p.exists():
        raise FileNotFoundError(f"Titles file not found: {p}")

    titles: Set[str] = set()
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            titles.add(_normalize(line))

    return titles or None


def filter_anime_list(
    anime_list: Iterable[Dict[str, Any]],
    selected_titles: Optional[Set[str]],
    *,
    keys: List[str] = ("eng_title", "romaji_title"),
) -> List[Dict[str, Any]]:
    """
    Filter a list of anime dictionaries based on selected titles.
    If selected_titles is None → return the entire list.

    Args:
        anime_list: Iterable of dict objects (e.g. from Notion)
        selected_titles: Set of normalized titles, or None
        keys: Keys inside dicts to compare against (default: English + Romaji titles)

    Returns:
        Filtered list of anime dicts (preserves original order).
    """
    if not selected_titles:
        return list(anime_list)

    filtered: List[Dict[str, Any]] = []
    for a in anime_list:
        for k in keys:
            val = _normalize(a.get(k, ""))
            if val and val in selected_titles:
                filtered.append(a)
                break
    return filtered
