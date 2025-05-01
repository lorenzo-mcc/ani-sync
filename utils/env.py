import os
from rich.console import Console

console = Console()


def validate_env_vars(required_vars):
    """Ensure all required environment variables are set."""
    missing = [var for var in required_vars if os.getenv(var) is None]
    if missing:
        console.print(
            f"[bold red]❌ Missing required environment variables: {', '.join(missing)}[/bold red]"
        )
        exit(1)
