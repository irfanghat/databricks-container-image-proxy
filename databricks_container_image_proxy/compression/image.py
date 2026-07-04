import gzip
import hashlib

from pathlib import Path

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from settings import CHUNK_SIZE
from terminal.output import console


def compress_file(
    input_path: Path, output_path: Path, description: str = "Compressing"
) -> str:
    """Compresses an archive using gzip and tracks progress. Returns SHA-256."""
    total_size = input_path.stat().st_size
    sha256_hash = hashlib.sha256()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=total_size)

        with (
            open(input_path, "rb") as f_in,
            gzip.open(output_path, "wb", compresslevel=6) as f_out,
        ):
            while True:
                chunk = f_in.read(CHUNK_SIZE)
                if not chunk:
                    break
                f_out.write(chunk)
                sha256_hash.update(chunk)
                progress.update(task, advance=len(chunk))

    return sha256_hash.hexdigest()


def decompress_file(
    input_path: Path, output_path: Path, description: str = "Decompressing"
) -> str:
    """Decompresses a gzip archive to disk, updates progress, and returns SHA-256."""
    sha256_hash = hashlib.sha256()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TransferSpeedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=None)

        with (
            gzip.open(input_path, "rb") as f_in,
            open(output_path, "wb") as f_out,
        ):
            while True:
                chunk = f_in.read(CHUNK_SIZE)
                if not chunk:
                    break
                f_out.write(chunk)
                sha256_hash.update(chunk)
                progress.update(task, advance=len(chunk))

    return sha256_hash.hexdigest()
