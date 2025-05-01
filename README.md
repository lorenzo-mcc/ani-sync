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

This is a personal project built by **Kubitto** for portfolio purposes — combining image recognition, data enrichment, and Notion automation into one flexible toolkit for anime fans and tech-curious curators.


---

## 🔧 Features

AniSync is composed of three key components — each one focused on automating and enhancing your Notion-based anime database:

## ✨ See it in action

_A demo GIF showcasing **AniSync** in action will be added soon!_
_Stay tuned — this section will include a visual walkthrough of the main CLI features so you can see how the tool works directly from the README._

### 📦 `syncer/` – Main Sync Engine

The core logic of AniSync lives here.

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
- 🖼️ `update_banner_images.py`: Adds AniList banner images as Notion page covers.
- 📊 `count_anime.py`: Checks for missing titles in your Notion database compared to AniList.
- 🔁 `retry_no_response.py`: Retries AniList fetches for entries that previously failed.

### 🧰 `utils/` – Config & Environment Tools

Utility scripts used across the framework to manage configuration and ensure consistency.

- ✅ `env.py`: Validates environment variables and API credentials, and manages shared paths used across the project.


---

### 🧭 `cli.py` – Command-Line Interface

The unified entry point for AniSync. Powered by [Typer](https://typer.tiangolo.com/), it organizes all commands into subgroups:

- 📁 `notion` commands: for syncing new anime from `input/anime_list.txt` into your Notion database.
- 🛠 `tools` commands: utility scripts for maintaining, enriching, and validating the database.
- 📌 Supports flags like `--dry-run` and `--debug` for safer and smarter execution.
- 🧪 Ideal for integration into custom workflows, terminals, or automation scripts.

#### 🌱 CLI Usage

Run the main CLI entry point like this:

```bash
python cli.py [GROUP] [COMMAND] [OPTIONS]
```

### ⚔️ Available Commands

#### 📁 Notion Commands (defined in `syncer/` folder)

| Command               | Description                                        |
|-----------------------|----------------------------------------------------|
| `notion sync-anime`   | Sync new titles from `input/anime_list.txt` to Notion    |

##### ⚡ Syncer Optional Flag

| Flag        | Description                                      |
|-------------|--------------------------------------------------|
| `--force`   | Overwrites existing entries in Notion if the title already exists. |

#### ⚙️ Tools Commands (defined in `tools/` folder)

| Command                            | Description                                                                 |
|------------------------------------|-----------------------------------------------------------------------------|
| `tools update-all`                 | Runs multiple Notion updaters in sequence                                   |
| `tools extract-anime-titles`       | Uses GPT-4 Vision to extract anime titles from screenshots                  |
| `tools update-studios`             | Updates studio information for anime entries in Notion                      |
| `tools update-genres-watched`      | Syncs secondary genres for anime marked as watched                          |
| `tools update-country`             | Sets the country field based on flag emojis                                 |
| `tools count-anime`                | Checks that all anime in Notion exist on AniList                            |
| `tools update-banner-images`       | Updates Notion page covers using AniList banner images                      |
| `tools update-romaji-titles`       | Fetches and sets Romaji titles for anime in Notion                          |
| `tools update-sources`             | Sets the original source of adaptation for each anime in Notion             |

##### ⚡ `tools update-all` Optional Flags

| Flag                        | Description                                        |
|-----------------------------|----------------------------------------------------|
| `--banner \ --no-banner`	  | Update banner images (default: enabled)            |       
| `--sources \ --no-sources`  |	Update sources (default: enabled)                  |
| `--studios \ --no-studios`  | Update animation studios (default: enabled)        |
| `--genres \ --no-genres`	  | Update watched genres (default: enabled)           |
| `--romaji \--no-romaji`     |	Update Romaji titles (default: enabled)            |
|  `--country \ --no-country` |	Update country from flag emojis (default: enabled) |

##### ⚡ `tools extract-anime-titles` Optional Flags

| Flag        | Description                                      |
|-------------|--------------------------------------------------|
| `--debug`   | Enable detailed logging (e.g. GPT raw responses) |
| `--dry-run` | Simulate execution without API calls or writes   |

##### ⚡ `tools count-anime` Optional Flag

| Flag        | Description                                            |
|-------------|--------------------------------------------------------|
| `--retry`   | Retry only titles that previously had no AniList match |

### 🚀 Sample Workflow

```bash
# Extract titles from screenshots (dry run with debug)
python cli.py tools extract-anime-titles --dry-run --debug

# Retry missing AniList matches
python cli.py tools count-anime --retry

# Sync cleaned list to Notion
python cli.py notion sync-anime
```


---

## ⚡ Requirements & Setup

### ⬇️ Clone the repository
```bash
git clone https://github.com/lorenzo-mcc/ani-sync.git
cd ani-sync
```

### 📂 Install Dependencies

Use `pip` to install all required libraries:

```bash
pip install -r requirements.txt
```

Contents of `requirements.txt`:
```text
notion_client==2.3.0
openai==1.75.0
python-dotenv==1.1.0
Requests==2.32.3
rich==14.0.0
tqdm==4.67.1
typer==0.15.2
```

### 🔢 Setup Environment Variables

Copy the provided `.env.example` file and update your API credentials and config:

```bash
cp .env.example .env
```

### 📄 Example `.env` File

```env
# Required environment variables
ACCESS_TOKEN=your-access-token
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
FULL_CATALOGUE_DB_ID=your-notion-db-id
GENRES_DB_ID=your-genres-db-id
NOTION_API_KEY=your-notion-api-key
OPENAI_API_KEY=your-openai-api-key

# ===== Default =====
# OpenAI settings
OPENAI_MODEL=gpt-4o
PROMPT="You will receive a batch of images. Each image is a screenshot from Instagram Reels. These may include comments, descriptions, or visual frames from anime-related content. Your task is to extract the names of anime referenced in each image. Titles may appear in text or be visually implied. Follow these rules: (1) Extract only anime titles. (2) Extract all titles if more than one is present. (3) Remove duplicates, even across languages or formats. (4) Transliterate Japanese titles into Latin characters (romaji). (5) Partial or fuzzy matches are acceptable if the anime is recognizable. (6) Include only real anime, even if unreleased. Your output must be: a plain text list of unique titles, one per line, with no formatting, bullets, or numbering."

# Notion settings
GENRES_SOURCE=Genres
GENRES_TARGET="Genres (Watched Anime)"
WATCHED_RELATION="Watched Anime"

# AniList settings
ANILIST_API_URL=https://graphql.anilist.co
TOKEN_URL=https://anilist.co/api/v2/oauth/token

# Script behavior & toggles
DEBUG_OUTPUT=True
DELAY_SECONDS=2
REQUEST_INTERVAL=2.14
USE_CACHE=True
VERBOSE=True

# Paths & files
INPUT_FOLDER=input
OUTPUT_FILE=anime_titles.txt
OUTPUT_FOLDER=output
```

> ⚠️ **Note:** Make sure you replace placeholder values in the Required environment variables section with your real API keys, access tokens or database ids. Never commit your `.env` file to a public repository!


---

## 🏛️ File Structure

```
ani-sync/
├── assets/                               # Project assets (media used in README)
│   ├── banner.png
│   ├── kubitto-logo.png
│   ├── demo.gif
│
├── syncer/                               # Main syncing logic (Notion + AniList)
│   ├── input/                            # Input files for sync (e.g., anime list)
│   │   ├── anime_list.txt                # Source list of anime titles (one per line)
│   │   ├── anime_list.tmp                # Temporary processed file (ignored in git)
│   ├── output/                           # Output folder for syncer results (auto-generated)
│   ├── anilist_fetcher.py                # Handles AniList GraphQL queries
│   ├── formatter.py                      # Cleans and formats AniList data for Notion
│   ├── get_access_token.py               # Retrieves AniList access token
│   ├── main.py                           # Entry point for syncing anime to Notion
│   ├── notion_updater.py                 # Creates and updates pages in Notion
│
├── tools/                                # Helper scripts for database management
│   ├── input/                            # Input folder for tool scripts (auto-generated)
│   ├── output/                           # Output folder for tool scripts (auto-generated)
│   ├── count_anime.py                    # Verifies that Notion entries exist on AniList
│   ├── extract_titles.py                 # Uses GPT-4 Vision to extract titles from images
│   ├── retry_no_response.py              # Retries AniList fetches that previously failed
│   ├── update_animation_studios.py       # Updates animation studio data in Notion
│   ├── update_banner_images.py           # Syncs Notion page covers with AniList banners
│   ├── update_country_from_flags.py      # Sets country fields based on flag emojis
│   ├── update_romaji_titles.py           # Adds Romaji titles to Notion entries
│   ├── update_sources.py                 # Sets original source/adaptation in Notion
│   ├── update_watched_anime_genres.py    # Syncs secondary genre field for watched anime
│
├── utils/                                # Shared helper utilities
│   ├── env.py                            # Validates env vars and paths across modules
│
├── .env                                  # Local environment config (excluded from git)
├── .env.example                          # Example environment config for setup
├── .flake8                               # Flake8 config file for linting rules
├── .gitignore                            # Git ignore rules
├── cli.py                                # Typer-based CLI entry point for all commands
├── CHANGELOG.md                          # Project changelog (version history)
├── LICENSE                               # Project license file
├── pyproject.toml                        # Project config (for black, isort, etc.)
├── README.md                             # Main project documentation
├── requirements.txt                      # Python dependencies
```


---

## 🎨 Customization

AniSync is designed to adapt to your personal anime tracking needs:

- **Update your anime list**  
  Edit `syncer/input/anime_list.txt` to include your anime titles — one per line. Add season markers like `(S2)` to indicate you've already watched previous seasons.

- **Customize formatting logic**  
  Modify `syncer/formatter.py` if you need to change how metadata (titles, seasons, tags) is cleaned and formatted before sending it to Notion.

- **Tweak GPT-4 Vision behavior**  
  Adjust the prompt inside `tools/extract_titles.py` if you want different output styles or instruction rules for OpenAI Vision extraction.

- **Adapt your Notion schema**  
  Make sure your Notion database uses the expected properties (e.g., `Genres`, `Studios`, `Country`, `Anime Watched`). The syncing logic in `syncer/notion_updater.py` assumes a specific structure.

- **Modify utility behaviors**  
  Update scripts inside `tools/` to match your preferred logic for post-processing, studio updates, country flags, and genre syncing.


---

## 🧪 Testing Strategy

AniSync is still evolving, but basic functional testing has been implemented manually by running key commands like:

```bash
python cli.py tools extract-anime-titles --dry-run
python cli.py notion sync-anime
```


---

## 🗺️ Roadmap

Here’s the planned development roadmap for future releases:

- [ ] Create an animated demo (.gif) to showcase AniSync in action directly in the README for easier onboarding.
- [ ] Add lightweight unit tests for API calls and formatting logic using `pytest`.
- [ ] Link the Notion template in the README (to be published on the Notion Creators shop).
- [ ] Modify the syncer module to handle anime statuses directly from AniList when creating entries.
- [ ] Create a dedicated updater module to sync anime statuses in line with other updater tools.
- [ ] Build three separate syncers:
  - [ ] AniList → for Japanese anime
  - [ ] MyAnimeList (MAL) → for Eastern anime excluding Japanese media (e.g., Chinese, Korean)
  - [ ] TMDB → for Western and European animated series


---

## 🤝 Contributing

Contributions, ideas, and improvements are welcome!  
If you'd like to report a bug, suggest a feature, or improve functionality, feel free to open an issue or submit a pull request.

### 🛡️ Coding Guidelines

To ensure a clean and consistent codebase, please follow these guidelines:

- **Code style:**  
  Use [Black](https://black.readthedocs.io/) for auto-formatting Python code. Run:  
  ```bash
  black .
  ```

- **Linting:**  
  Check for basic issues using [Flake8](https://flake8.pycqa.org/):  
  ```bash
  flake8 .
  ```

- **Naming conventions:**  
  - Files and modules → `snake_case.py`  
  - Classes → `PascalCase`  
  - Functions and variables → `snake_case`

- **Commit messages:**  
  Write clear, descriptive commit messages (e.g., `Fix bug in update_sources`, `Add unit tests for formatter`).

### 🧪 Local Testing Before PR

Before submitting a pull request, please:

1. Run core CLI commands locally to ensure no critical errors:  
   ```bash
   python cli.py tools extract-anime-titles --dry-run
   python cli.py tools update-all --no-banner --no-sources
   ```

2. (Optional) Run manual tests or mock small `.env` setups for specific edge cases.

3. Confirm that README changes (if any) are clear and correctly formatted.


> Thank you for helping improve AniSync! Every contribution is appreciated 💛


---

## 📖 Acknowledgments

- 🔗 [AniList API](https://docs.anilist.co/) – for providing detailed anime metadata
- 🔗 [Notion API](https://developers.notion.com/) – for workspace integration
- 🔗 [OpenAI GPT-4 Vision](https://platform.openai.com/docs/overview) – for extracting anime titles from images
- 🔗 [Typer](https://typer.tiangolo.com/) – for powering the elegant CLI interface
- 🔗 [Rich](https://rich.readthedocs.io/en/stable/index.html#) – for beautifully formatted console output
- 🔗 [tqdm](https://tqdm.github.io/) – for easy and clean progress tracking in loops
Inspired by the need for better anime tracking and Notion automation tools


---

## 📜 Changelog

All changes and version history are documented in the [CHANGELOG.md](CHANGELOG.md) file.


---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Made with ❤️ by 
    <img src="assets/kubitto-logo.png" alt="Kubitto" width="20" style="vertical-align: -2px; padding-left: 4px;padding-right: 2px;"/> 
    <strong>Kubitto</strong>
  </sub>
</div>
