# **Ani-Sync**

An efficient Python tool for managing and synchronizing anime lists between a local text file and a Notion database. This project leverages the **AniList API** for fetching detailed anime information and the **Notion API** for database integration.

---

## **Features**

- Syncs a local list of anime titles (`anime_list.txt`) with a Notion database.
- Fetches detailed anime data, such as format, airing dates, and studios, from AniList.
- Automatically normalizes and cleans anime titles to ensure consistency.
- Identifies missing titles in the Notion database and generates a `missing_titles.txt` file for easy review.
- Designed to handle complex formatting, including season annotations (e.g., `(S1)`).

---

## **Requirements**

1. Python 3.8 or later.
2. A **Notion API Key** (stored in a `.env` file).
3. An **AniList API Token** for fetching anime data.

---

## **Setup**

### 1. Clone the Repository
```bash
git clone https://github.com/lorenzo-mcc/ani-sync.git
cd synched_anime_tracker
```

### 2. Install Dependencies
Use `pip` to install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root and add your Notion and AniList tokens:
```
NOTION_API_KEY=your_notion_api_token
ACCESS_TOKEN=your_anilist_api_token
```

---

## **Usage**

### 1. Prepare Your Local List
Create or edit the `script/anime_list.txt` file. Each anime title should be on a new line. Leave a blank line between titles, if necessary. Titles may contain `(Sn)` for seasons, which will be cleaned automatically.

Example:
```
Attack on Titan (S1)

Demon Slayer (S2)

One Piece
```

### 2. Run the Main Script
Run the main Python script to compare your local list with the Notion database:
```bash
python main.py
```

### 3. Outputs
- The script will print any missing titles in the console.
- Missing titles will also be saved to `missing_titles.txt` in the project directory.

---

## **File Structure**

```
ani-sync/
├── config/
│   └── settings.json           # Configuration file (optional).
├── script/
│   ├── anime_list.txt          # Your local anime title list.
│   ├── anilist_fetcher.py      # Fetches anime data from AniList API.
│   ├── formatter.py            # Normalizes and formats anime data.
│   ├── notion_updater.py       # Updates the Notion database.
│   ├── get_access_token.py     # Helper for getting tokens (optional).
├── .env                        # Stores API tokens (not included in repo).
├── .gitignore                  # Excludes sensitive files.
├── main.py                     # Entry point for the script.
├── README.md                   # Project documentation.
├── requirements.txt            # Python dependencies.
```

---

## **Customization**

- Update `script/anime_list.txt` with your own anime titles.
- Modify the `formatter.py` script if you need to adjust how titles are normalized.
- Customize the Notion database schema to fit your needs.

---

## **Contributing**

Contributions are welcome! If you have suggestions for new features or improvements, feel free to open an issue or create a pull request.

---

## **Acknowledgments**

- **AniList API**: For providing anime data.
- **Notion API**: For database integration.
- Inspired by the need for better anime tracking tools.
