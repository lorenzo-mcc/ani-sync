"""
Module: extract_titles.py
Description:
    Extracts anime titles from images/reels via OpenAI and writes a deduplicated list to a text file.

Usage:
    python cli.py tools extract-anime-titles [--dry-run] [--debug]

Notes:
    Reads configuration from `.env`.
    - Required/used env vars:
        * DELAY_SECONDS
        * INPUT_FOLDER
        * OPENAI_API_KEY
        * OPENAI_MODEL
        * OUTPUT_FILE
        * OUTPUT_FOLDER
        * PROMPT
"""

import os
import base64
import time
import logging
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from utils.env import validate_env_vars

console = Console()

# === Setup paths and environment ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["OPENAI_API_KEY"]
validate_env_vars(REQUIRED_ENV_VARS)

# ====== CONFIG ======
INPUT_FOLDER = os.getenv("INPUT_FOLDER", "input")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "anime_titles.txt")
DELAY_SECONDS = int(os.getenv("DELAY_SECONDS", 2))

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
PROMPT = os.getenv(
    "PROMPT",
    (
        "You will receive a batch of images. Each image is a screenshot from Instagram Reels. "
        "These may include comments, descriptions, or visual frames from anime-related content. "
        "Your task is to extract the names of anime referenced in each image. Titles may appear in text "
        "or be visually implied. Follow these rules: (1) Extract only anime titles. (2) Extract all titles "
        "if more than one is present. (3) Remove duplicates, even across languages or formats. "
        "(4) Transliterate Japanese titles into Latin characters (romaji). (5) Partial or fuzzy matches "
        "are acceptable if the anime is recognizable. (6) Include only real anime, even if unreleased. "
        "Your output must be: a plain text list of unique titles, one per line, with no formatting, bullets, "
        "or numbering."
    ),
)

client = OpenAI(api_key=OPENAI_API_KEY)

# ====== PATHS ======
input_path = Path(base_path / INPUT_FOLDER)
output_path = Path(base_path / OUTPUT_FOLDER)
input_path.mkdir(parents=True, exist_ok=True)
output_path.mkdir(parents=True, exist_ok=True)

output_file = output_path / OUTPUT_FILE
found_titles = set()


# ====== PROCESS SINGLE IMAGE ======
def process_image(image_path: Path, dry_run: bool) -> str:
    if dry_run:
        return "dry-run-title-1\ndry-run-title-2\ndry-run-title-3"

    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here's the image:"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                        },
                    ],
                },
            ],
            max_tokens=1000,
        )
        content = response.choices[0].message.content.strip()

        logging.debug(f"[{image_path.name}]\n{content}\n{'='*40}")
        return content

    except Exception as e:
        logging.error(f"❌ ERROR processing {image_path.name}:\n{str(e)}\n{'='*40}")
        print(f"❌ Error processing image {image_path.name}:\n{e}\n")
        return ""


# ====== CLEAN AND STORE TITLES ======
def clean_and_add_titles(raw_response):
    for line in raw_response.strip().splitlines():
        title = line.strip()
        if title and title.lower() not in (t.lower() for t in found_titles):
            found_titles.add(title)


# ====== MAIN FUNCTION ======
def main(dry_run=False, debug_output=False):
    # Set logging level dynamically based on debug flag
    os.environ["DEBUG_OUTPUT"] = "True" if debug_output else "False"

    log_level = logging.DEBUG if debug_output else logging.INFO
    log_file_path = output_path / "debug_log.txt"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    console.print("[bold white]\n🔎 Anime Title Extractor | OpenAI Vision[/bold white]\n")

    images = sorted(
        set(input_path.glob("*.png"))
        | set(input_path.glob("*.jpg"))
        | set(input_path.glob("*.jpeg"))
    )

    if not images:
        console.print(
            f"[bold yellow]⚠️  No images found in '{INPUT_FOLDER}/'. "
            f"Please add some and run the script again.[/bold yellow]"
        )
        return

    total_checked = 0
    total_titles = 0

    console.print(
        f"[bold magenta]📂 Found {len(images)} images in folder '{INPUT_FOLDER}'[/bold magenta]\n"
    )

    log_file = output_path / "anime_log.txt"
    processed_images = set()

    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as log:
            for line in log:
                if ":" in line:
                    img_name = line.split(":")[0].strip()
                    processed_images.add(img_name.lower())

    for img in tqdm(images, desc="📥 Extracting anime titles"):
        if img.name.lower() in processed_images:
            continue

        attempts = 0
        joined_titles = "❌"

        while attempts < 2:
            response = process_image(img, dry_run)
            response = response.replace("\r\n", "\n")  # Normalize line endings
            raw_lines = [line.strip() for line in response.split("\n") if line.strip()]
            if raw_lines:
                joined_titles = ", ".join(raw_lines)
                clean_and_add_titles(response)
                total_titles += len(raw_lines)
                break
            attempts += 1
            time.sleep(DELAY_SECONDS)

        total_checked += 1

        if not dry_run:
            with open(log_file, "a", encoding="utf-8") as log:
                log.write(f"{img.name}: {joined_titles}\n")
                log.flush()

        time.sleep(DELAY_SECONDS)

    if not dry_run:
        with open(output_file, "w", encoding="utf-8") as f:
            for title in sorted(found_titles, key=str.casefold):
                f.write(title + "\n")

    console.print(f"\n[bold green]✅ Total images processed: {total_checked}[/bold green]")
    console.print(f"[bold cyan]📝 Unique anime titles found: {len(found_titles)}[/bold cyan]")

    if len(found_titles) == 0:
        console.print("[bold yellow]🔝 No titles were extracted.[/bold yellow]\n")
    elif not dry_run:
        console.print(f"[bold green]📄 Output saved to:[/bold green] {output_file}")


if __name__ == "__main__":
    main()
