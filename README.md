<div align="center">
  <img src="assets/banner.png" alt="AniSync Banner" style="width: 100%; height: auto;"/>
</div>

# 🎌 AniSync

<div align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white"/>
  <img alt="License" src="https://img.shields.io/github/license/lorenzo-mcc/ani-sync?cacheSeconds=0"/>
  <img alt="Typer" src="https://img.shields.io/badge/CLI%20Powered%20by-Typer-4a9683?logo=typer&logoColor=white"/>
  <img alt="Notion API" src="https://img.shields.io/badge/Notion%20API-Integrated-white?logo=notion"/>
  <img alt="AniList API" src="https://img.shields.io/badge/AniList%20API-Connected-02a9ff?logo=anilist"/>
  <img alt="OpenAI Vision" src="https://img.shields.io/badge/GPT--4%20Vision-Enabled-black?logo=openai&logoColor=black"/>
</div>

**AniSync** is a CLI framework designed to automate the creation and synchronization of a Notion anime database.  
It uses GPT-4 Vision to extract anime titles from images (like Instagram Reels or screenshots), enriches them via the AniList API, and updates a Notion database with structured metadata.

This is a personal project built for portfolio purposes, combining image recognition, data enrichment, and Notion automation into a flexible toolkit for anime fans and tech-curious curators.


---

## 🔧 Features

AniSync is composed of three key components — each one focused on automating and enhancing your Notion-based anime database:

### 📦 `syncer/` – Main Sync Engine
- ✅ Reads anime titles from `input/anime_list.txt` (one per line).
- 🧠 Supports special notation like `Title (S2)` to indicate watched seasons.
- 🔍 Uses the AniList API to fetch accurate metadata.
- 👤 Lets you choose the correct title if multiple matches are found.
- 🧼 Cleans and formats titles for Notion.
- 🧾 Creates Notion pages with enriched metadata.
- 🔐 Includes `get_access_token.py` for generating and refreshing AniList tokens.

### 🛠 `tools/` – Notion Enhancers & Utilities
A collection of CLI tools to keep your Notion database clean, accurate, and rich in metadata.

- 🤖 `extract_titles.py`: Uses **GPT-4 Vision** to extract anime titles from screenshots or Instagram Reels.
- 🏢 `update_animation_studios.py`: Fills the **"Studios"** property with data from AniList.
- 🎭 `update_watched_anime_genres.py`: Syncs the **"Genres (Watched Anime)"** property from main genre tags.
- 🗾 `update_country_from_flags.py`: Maps country flag emojis to the **"Country"** property.
- 🔤 `update_romaji_titles.py`: Sets the **"Romaji Title"** property using AniList data.
- 📕 `update_sources.py`: Updates the **"Source"** property with adaptation info from AniList.
- 🖼️ `update_images.py`: Syncs Notion page **header cover** (`bannerImage`) and property **Cover (Files & media)** (`coverImage.extraLarge`).
- 📊 `count_anime.py`: Checks for missing titles in your Notion database compared to AniList.
- 🔁 `retry_no_response.py`: Retries AniList fetches for entries that previously failed.

### 🧰 `utils/` – Config & Helpers
- ✅ `env.py`: Validates environment variables and API credentials, and manages shared paths used across the project.
- ✅ `title_filter.py`: Handles filtering of anime subsets via CLI (`--titles`) or `.env` (`ANIME_TITLES_FILE`).


---

## ✨ CLI Usage

The unified entry point for AniSync is `cli.py`, powered by [Typer](https://typer.tiangolo.com/).

```bash
python cli.py [GROUP] [COMMAND] [OPTIONS]
```

### 📁 Notion Commands

| Command             | Description                                             |
|---------------------|---------------------------------------------------------|
| `notion sync-anime` | Sync new titles from `input/anime_list.txt` to Notion   |

**Optional Flag**  
| Flag      | Description                                      |
|-----------|--------------------------------------------------|
| `--force` | Overwrites existing entries in Notion if the title already exists. |

### ⚙️ Tools Commands

| Command                      | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `tools update-all`           | Runs multiple Notion updaters in sequence                                   |
| `tools update-images`        | Syncs Notion covers (`bannerImage` + `coverImage.extraLarge`)               |
| `tools update-sources`       | Updates adaptation sources in Notion                                        |
| `tools update-studios`       | Updates studio information in Notion                                        |
| `tools update-genres-watched`| Syncs watched anime genres                                                  |
| `tools update-country`       | Updates country field from flag emojis                                      |
| `tools update-romaji-titles` | Adds Romaji titles to Notion entries                                        |
| `tools extract-anime-titles` | Uses GPT-4 Vision to extract titles from images                             |
| `tools count-anime`          | Verifies AniList matches for Notion entries                                 |
| `tools retry-no-response`    | Retries failed AniList queries                                              |

#### ⚡ Filtering Anime

Every updater command supports **optional filtering** via:
- `--titles path/to/file.txt` → Load titles from file (highest priority)
- `.env → ANIME_TITLES_FILE=...` → Default filter file
- If neither is set, **all anime are processed**.

Example:

```bash
python cli.py tools update-images --titles tools/input/anime_list.txt
```

#### ⚡ Common Flags

| Command / Flag         | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `tools update-all`     | Runs all updaters (supports selective `--no-*` flags)                       |
| `tools extract-anime-titles --debug` | Logs raw GPT responses for debugging                           |
| `tools extract-anime-titles --dry-run` | Simulates execution without API calls or writes              |
| `tools count-anime --retry` | Retry only titles with previous `no_response` failures                 |


---

## ⚡ Requirements & Setup

### ⬇️ Clone the repository
```bash
git clone https://github.com/lorenzo-mcc/ani-sync.git
cd ani-sync
```

### 📂 Install Dependencies

```bash
pip install -r requirements.txt
```

### 🔢 Setup Environment Variables

Copy the provided `.env.example` file and update your API credentials and config:

```bash
cp .env.example .env
```

### 📄 Example `.env` File

```env
# Required variables
NOTION_API_KEY=your-notion-api-key
FULL_CATALOG_DB_ID=your-fullcatalog-db-id
GENRES_DB_ID=your-genres-db-id
ANILIST_API_URL=https://graphql.anilist.co
OPENAI_API_KEY=your-openai-api-key

# Behavior
DEBUG_OUTPUT=True
VERBOSE=True
USE_CACHE=True
REQUEST_INTERVAL=2.14

# Paths
ANIME_TITLES_FILE=tools/input/anime_list.txt
INPUT_FOLDER=input
OUTPUT_FOLDER=output
OUTPUT_FILE=anime_titles.txt
```

---

## 🏛️ File Structure

```
ani-sync/
├── assets/
│   ├── banner.png
│   ├── demo.gif
│
├── syncer/
│   ├── input/
│   │   ├── anime_list.txt
│   ├── main.py
│   ├── formatter.py
│   ├── notion_updater.py
│
├── tools/
│   ├── update_images.py
│   ├── update_sources.py
│   ├── update_animation_studios.py
│   ├── update_romaji_titles.py
│   ├── update_country_from_flags.py
│   ├── update_watched_anime_genres.py
│   ├── count_anime.py
│   ├── extract_titles.py
│   ├── retry_no_response.py
│
├── utils/
│   ├── env.py
│   ├── title_filter.py
│
├── cli.py
├── requirements.txt
├── .env / .env.example
├── README.md
```


---

## 📖 Acknowledgments

- [AniList API](https://docs.anilist.co/) – detailed anime metadata  
- [Notion API](https://developers.notion.com/) – workspace integration  
- [OpenAI GPT-4 Vision](https://platform.openai.com/docs/overview) – title extraction from images  
- [Typer](https://typer.tiangolo.com/) – CLI framework  
- [Rich](https://rich.readthedocs.io/) – styled console output  
- [tqdm](https://tqdm.github.io/) – progress bars  

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
