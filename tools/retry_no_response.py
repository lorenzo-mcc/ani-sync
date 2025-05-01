import os
import requests
import json
import time
import csv
from pathlib import Path
from rich.console import Console
from tqdm import tqdm
from dotenv import load_dotenv

console = Console()

# === Setup paths and environment ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
output_dir = base_path / "output"
debug_path = output_dir / "unresolved_debug.json"
csv_path = output_dir / "unresolved.csv"

load_dotenv(dotenv_path=env_path)

VERBOSE = os.getenv("VERBOSE", "True")


def request_with_retry(url, headers, json_data=None, retries=3, delay=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, headers=headers, json=json_data, timeout=10)
            if response.status_code in (200, 429):
                return response
        except requests.RequestException as e:
            if VERBOSE:
                console.log(f"[retry:{attempt}] Request error: {e}")
        time.sleep(delay)
    return None


def main():
    if not debug_path.exists():
        console.print("[red]❌ Debug file not found! Run the main script first.[/red]")
        return

    with open(debug_path, "r", encoding="utf-8") as f:
        debug_entries = json.load(f)

    no_response_entries = [e for e in debug_entries if e.get("reason") == "no_response"]

    if not no_response_entries:
        console.print("[green]✅ No 'no_response' entries to retry![/green]")
        return

    remaining = []
    updated_csv_rows = []

    progress_bar = tqdm(
        no_response_entries, desc="🔁 Retrying", unit="anime", ncols=console.size.width
    )

    for entry in progress_bar:
        title = entry["english"]
        year = entry["year"]
        fmt = entry.get("format", "")
        short_title = title if len(title) <= 40 else title[:37] + "…"
        progress_bar.set_postfix_str(short_title)

        query_data = {
            "query": entry["query"]["query"],
            "variables": entry["query"]["variables"],
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

        while True:
            resp = request_with_retry("https://graphql.anilist.co", headers, json_data=query_data)
            if resp and resp.status_code == 429:
                progress_bar.write(f"⏳ Rate limited for '{title}' → waiting 60s")
                time.sleep(60)
                continue
            break

        if resp and resp.status_code == 200:
            data = resp.json()
            results = data.get("data", {}).get("Page", {}).get("media", [])
            if results:
                continue  # Found!

        remaining.append(entry)
        updated_csv_rows.append(
            {"Title": title, "Year": year, "Format": fmt, "Reason": "no_response"}
        )

        time.sleep(1)

    # === Update files ===
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(remaining, f, indent=2, ensure_ascii=False)

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Title", "Year", "Format", "Reason"])
        writer.writeheader()
        writer.writerows(updated_csv_rows)

    console.print("\n[bold white]📊 Retry Summary[/bold white]")
    console.print(
        f"[green]✅ Recovered entries: {len(no_response_entries) - len(remaining)}[/green]"
    )
    console.print(f"[yellow]❌ Still no response: {len(remaining)}[/yellow]")
    console.print(f"[dim]📝 Files updated: {csv_path.name}, {debug_path.name}[/dim]\n")


if __name__ == "__main__":
    main()
