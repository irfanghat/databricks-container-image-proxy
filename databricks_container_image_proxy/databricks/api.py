from pathlib import Path
from typing import Generator, List

import httpx
import typer

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from settings import Settings, CHUNK_SIZE
from terminal.output import console


def get_http_client(settings: Settings) -> httpx.Client:
    """Initializes an HTTP client configured for Databricks API interaction."""
    clean_host = settings.databricks_host.rstrip("/")
    if not clean_host.startswith("http://") and not clean_host.startswith("https://"):
        clean_host = f"https://{clean_host}"

    headers = {
        "Authorization": f"Bearer {settings.databricks_token}",
        "Accept": "application/json",
    }
    return httpx.Client(
        base_url=clean_host, headers=headers, timeout=httpx.Timeout(60.0)
    )


def execute_with_retry(client_call_func) -> httpx.Response:
    import time

    backoff = 1.0
    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = client_call_func()
            if response.status_code in (500, 502, 503, 504):
                if attempt == max_retries - 1:
                    return response
                time.sleep(backoff)
                backoff *= 2
                continue
            return response
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
        ):
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2


class ProgressIterable:
    """A wrapper that yields streaming file data while updating Rich progress."""

    def __init__(self, filepath: Path, progress: Progress, task_id: TaskID):
        self.filepath = filepath
        self.progress = progress
        self.task_id = task_id

    def __iter__(self) -> Generator[bytes, None, None]:
        with open(self.filepath, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                yield chunk
                self.progress.update(self.task_id, advance=len(chunk))


def upload_to_volume(
    settings: Settings,
    local_path: Path,
    filename: str,
) -> None:
    """
    Streams a file directly from disk to the Databricks Volume
    using the Unity Catalog Files API.
    """
    target_path = (f"{settings.databricks_volume.rstrip('/')}/{filename}").lstrip("/")

    url_path = f"/api/2.0/fs/files/{target_path}"
    total_size = local_path.stat().st_size

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Uploading", total=total_size)
        iterable_body = ProgressIterable(local_path, progress, task)

        with get_http_client(settings) as client:

            def do_put():
                return client.put(
                    url_path,
                    params={"overwrite": "true"},
                    headers={
                        "Content-Type": "application/octet-stream",
                    },
                    content=iterable_body,
                )

            res = execute_with_retry(do_put)

            if res.status_code not in (200, 204):
                console.print(
                    f"\n[bold red]Upload Failure ({res.status_code}):[/bold red] "
                    f"{res.text}"
                )
                raise typer.Exit(code=1)


def download_from_volume(
    settings: Settings,
    local_path: Path,
    filename: str,
) -> None:
    """
    Streams a file directly from a Databricks Volume onto local storage.
    """
    target_path = (f"{settings.databricks_volume.rstrip('/')}/{filename}").lstrip("/")

    url_path = f"/api/2.0/fs/files/{target_path}"

    with get_http_client(settings) as client:
        with client.stream("GET", url_path) as response:

            if response.status_code != 200:
                console.print(
                    f"[bold red]Download Failure ({response.status_code}):[/bold red] "
                    "File may not exist in storage backend."
                )
                raise typer.Exit(code=1)

            total_size = int(response.headers.get("content-length", 0))

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Downloading",
                    total=total_size,
                )

                with open(local_path, "wb") as f:
                    for chunk in response.iter_bytes(
                        chunk_size=CHUNK_SIZE,
                    ):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))


def list_volume_contents(settings: Settings) -> List[dict]:
    """
    Lists files contained within the configured Unity Catalog volume path.
    """
    target_path = settings.databricks_volume.rstrip("/").lstrip("/")
    url_path = f"/api/2.0/fs/directories/{target_path}"

    with get_http_client(settings) as client:

        def do_list():
            return client.get(url_path)

        res = execute_with_retry(do_list)

        if res.status_code == 404:
            return []

        if res.status_code != 200:
            console.print(
                f"[bold red]API Failure ({res.status_code}):[/bold red] " f"{res.text}"
            )
            raise typer.Exit(code=1)

        data = res.json()
        return data.get("contents", [])
