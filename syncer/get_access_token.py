import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from utils.env import validate_env_vars

console = Console()

# === Load .env ===
base_path = Path(__file__).resolve().parent
env_path = base_path.parent / ".env"
load_dotenv(dotenv_path=env_path)

REQUIRED_ENV_VARS = ["CLIENT_ID", "CLIENT_SECRET"]
validate_env_vars(REQUIRED_ENV_VARS)

TOKEN_URL = os.getenv("TOKEN_URL", "https://anilist.co/api/v2/oauth/token")


def get_access_token():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token_url = TOKEN_URL

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        console.print(f"[bold green]✅ Access token obtained:[/bold green] {access_token}")
        return access_token
    else:
        console.print(f"[bold red]❌ Error {response.status_code}:[/bold red] {response.text}")
        return None


if __name__ == "__main__":
    get_access_token()
