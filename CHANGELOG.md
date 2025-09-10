# 🕑 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Initial project creation: set up CLI structure, core sync commands, and modular tools.
- Integrated GPT-4 Vision for anime title extraction.
- Added AniList and Notion API connectors.

## [2025-09-11]

### Changed
- Updated Notion API to `2025-09-03` (breaking change: introduced **Data sources** separated from Databases).
- Set `NOTION_VERSION` in `.env` and passed to Notion client.
- Locked dependency `notion-client==2.3.0` in `requirements.txt` to ensure compatibility.

### Notes
- Endpoints `/v1/databases` now only manage database containers; schema/properties are handled via new `/v1/data_sources` endpoints.
- Existing scripts still work if using single-source databases, but new features require migration.
