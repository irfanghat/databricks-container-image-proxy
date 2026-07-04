import shutil
from datetime import datetime
from pathlib import Path

import httpx
import typer
from dotenv import load_dotenv
from rich.table import Table

from settings import get_settings, Settings
from terminal.output import console

from docker.process import (
    check_docker_available, image_exists_locally, docker_save, docker_load, docker_run
)
from parsing.image import image_to_filename, filename_to_image
from compression.image import compress_file, decompress_file
from databricks.api import upload_to_volume, download_from_volume, list_volume_contents

app = typer.Typer(
    help="Docker image shipping backed by Databricks Volumes.",
    no_args_is_help=True,
)


@app.command()
def push(
    image: str = typer.Argument(
        ...,
        help="Local image reference to push",
    ),
):
    """
    Saves, compresses, and uploads a local Docker image to Databricks Storage.
    """
    check_docker_available()
    settings = get_settings()

    if not image_exists_locally(image):
        console.print(f"[bold red]Error:[/bold red] Local image '{image}' not found.")
        raise typer.Exit(code=1)

    filename = image_to_filename(image)

    tmp_dir = Path("./.dbrx_registry_tmp")
    tmp_dir.mkdir(exist_ok=True)

    raw_tar = tmp_dir / f"{filename}.raw"
    compressed_tar = tmp_dir / filename

    try:
        console.print(f"[bold blue]Pushed Image Reference:[/bold blue] {image}")

        docker_save(image, raw_tar)
        compress_file(raw_tar, compressed_tar)
        upload_to_volume(settings, compressed_tar, filename)

        console.print(
            f"[bold green]Successfully pushed {image} "
            "to Databricks backend.[/bold green]"
        )

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.command()
def pull(
    image: str = typer.Argument(
        ...,
        help="Image reference to pull",
    ),
):
    """
    Downloads, decompresses, and loads a Docker image from Databricks Storage.
    """
    check_docker_available()
    settings = get_settings()

    filename = image_to_filename(image)

    tmp_dir = Path("./.dbrx_registry_tmp")
    tmp_dir.mkdir(exist_ok=True)

    compressed_tar = tmp_dir / filename
    raw_tar = tmp_dir / f"{filename}.raw"

    try:
        console.print(f"[bold blue]Pulling Image Reference:[/bold blue] {image}")

        download_from_volume(settings, compressed_tar, filename)
        decompress_file(compressed_tar, raw_tar)
        docker_load(raw_tar)

        console.print(
            f"[bold green]Successfully pulled and loaded {image}[/bold green]"
        )

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
def run(
    ctx: typer.Context,
    image: str = typer.Argument(
        ...,
        help="Image reference to run",
    ),
):
    """
    Executes an image locally, pulling it from the registry automatically
    if missing.
    """
    check_docker_available()

    if not image_exists_locally(image):
        console.print(
            f"[yellow]Image '{image}' not found locally. " "Triggering pull...[/yellow]"
        )
        pull(image)

    docker_run(image, ctx.args)


@app.command(name="list")
def list_images():
    """
    Lists all stored Docker images and tags within the configured
    Databricks Volume.
    """
    settings = get_settings()
    contents = list_volume_contents(settings)

    table = Table(title="Databricks Volume Images")
    table.add_column("Image Name", style="cyan")
    table.add_column("Tag", style="magenta")
    table.add_column("Size (MB)", justify="right", style="green")
    table.add_column("Last Modified", style="yellow")

    found_any = False

    for item in contents:
        if item.get("is_directory"):
            continue

        name = item.get("name", "")
        parsed = filename_to_image(name)

        if not parsed:
            continue

        found_any = True
        img_name, img_tag = parsed

        size_bytes = item.get("file_size", 0)
        size_mb = f"{size_bytes / (1024 * 1024):,.2f}"

        mtime_ms = item.get("last_modified", 0)
        mtime_str = "-"

        if mtime_ms:
            mtime_str = datetime.fromtimestamp(mtime_ms / 1000.0).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        table.add_row(
            img_name,
            img_tag,
            size_mb,
            mtime_str,
        )

    if found_any:
        console.print(table)
    else:
        console.print("[yellow]No registry images found in storage.[/yellow]")
