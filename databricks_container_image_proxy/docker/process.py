import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List
import typer

from terminal.output import console


def check_docker_available() -> None:
    """Verifies that the Docker daemon is accessible."""
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(
            "[bold red]Docker Error:[/bold red] Cannot connect to Docker daemon. Is Docker running?"
        )
        raise typer.Exit(code=1)


def image_exists_locally(image_ref: str) -> bool:
    """Checks if a given image reference exists in the local Docker daemon."""
    result = subprocess.run(
        ["docker", "image", "inspect", image_ref],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def docker_save(image_ref: str, output_path: Path) -> None:
    """Saves a local Docker image to an uncompressed tar archive on disk."""
    try:
        subprocess.run(
            ["docker", "save", "-o", str(output_path), image_ref],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Docker Save Failed:[/bold red] {e.stderr.strip()}")
        raise typer.Exit(code=e.returncode)


def docker_load(input_path: Path) -> None:
    """Loads a Docker image from an uncompressed tar archive on disk."""
    try:
        subprocess.run(
            ["docker", "load", "-i", str(input_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Docker Load Failed:[/bold red] {e.stderr.strip()}")
        raise typer.Exit(code=e.returncode)


def docker_run(image_ref: str, passthrough_args: List[str]) -> None:
    """Executes docker run, transparently forwarding arguments and exit codes."""
    cmd = ["docker", "run"] + passthrough_args + [image_ref]
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except FileNotFoundError:
        console.print("[bold red]Execution Error:[/bold red] docker CLI not found.")
        sys.exit(1)
