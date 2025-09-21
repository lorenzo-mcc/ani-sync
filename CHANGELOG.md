# 🕑 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Initial project creation: set up CLI structure, core sync commands, and modular tools.
- Integrated GPT-4 Vision for anime title extraction.
- Added AniList and Notion API connectors.

## [2025-09-21]

### Added
- Introduced `utils/title_filter.py` module for centralized anime title filtering.
  - Supports selection via CLI flag `--titles` or `.env` variable `ANIME_TITLES_FILE`.
  - Falls back to processing **all anime** if no filter is set.
- Added support in all updaters (`update_images`, `update_sources`, `update_animation_studios`, etc.) and CLI (`cli.py`) for selective updates.
- New unified **docstrings** across all scripts for consistent enterprise-style documentation.
- Updated `update_images.py` to:
  - Sync both **Notion page banners** and **Cover (Files & media property)**.
  - Controlled via `.env` flags `OVERWRITE_HEADER_COVER` and `OVERWRITE_PROPERTY_COVER`.

### Changed
- Refactored CLI (`cli.py`):
  - Added `--titles` option to relevant `tools` commands for selective execution.
  - Updated `tools update-all` to forward `--titles` to subcommands.
- Updated `.env.example`:
  - Added `ANIME_TITLES_FILE` variable under **Script behavior & toggles**.
  - Added overwrite flags for image behavior.
- Standardized documentation style (docstrings + README).
- Cleaned up README:
  - Replaced references to deprecated `update_banner_images.py` with `update_images.py`.
  - Unified tables of CLI commands and optional flags.

### Fixed
- Consistent handling of relative and absolute paths for `ANIME_TITLES_FILE`.
- Prevented crashes when titles file is missing or empty.

## [2025-09-11]

### Changed
- Updated Notion API to `2025-09-03` (breaking change: introduced **Data sources** separated from Databases).
- Set `NOTION_VERSION` in `.env` and passed to Notion client.
- Locked dependency `notion-client==2.3.0` in `requirements.txt` to ensure compatibility.

### Notes
- Endpoints `/v1/databases` now only manage database containers; schema/properties are handled via new `/v1/data_sources` endpoints.
- Existing scripts still work if using single-source databases, but new features require migration.
