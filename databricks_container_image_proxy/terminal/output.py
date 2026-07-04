import logging
import os
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.logging import RichHandler


console = Console()


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, show_path=False)],
)
logger = logging.getLogger("dbrx_registry")

# --------------------------------------
# 1MB blocks for I/O operations
# --------------------------------------
CHUNK_SIZE = 1024 * 1024


def handle_ctrl_c() -> None:
    """Configures graceful exit handling for keyboard interrupts."""
    import signal

    def signal_handler(sig, frame):
        console.print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")
        sys.exit(130)

    signal.signal(signal.SIGINT, signal_handler)
