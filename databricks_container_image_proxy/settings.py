import typer
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from terminal.output import console

load_dotenv(find_dotenv())

# -------------------------------------------
# Global constant for chunked transfers
# ------------------------------------------
CHUNK_SIZE = 1024 * 1024


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    databricks_host: str
    databricks_token: str
    databricks_volume: str

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    """Validates and returns the application settings."""
    try:
        return Settings()
    except Exception as e:
        console.print(
            f"[bold red]Configuration Error:[/bold red] Missing or invalid environment variables.\n"
            f"Ensure DATABRICKS_HOST, DATABRICKS_TOKEN, and DATABRICKS_VOLUME are set in your .env file.\n"
            f"Details: {e}"
        )
        raise typer.Exit(code=1)
