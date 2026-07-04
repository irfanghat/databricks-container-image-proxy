import re
from typing import Tuple, Optional


def parse_image_name(image_ref: str) -> Tuple[str, str]:
    """Splits an image reference into name and tag. Defaults tag to 'latest'."""
    if ":" in image_ref:
        name, tag = image_ref.rsplit(":", 1)
        if "/" in tag:
            return image_ref, "latest"
        return name, tag
    return image_ref, "latest"


def image_to_filename(image_ref: str) -> str:
    """Converts a Docker image reference into a filesystem-safe filename."""
    name, tag = parse_image_name(image_ref)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    safe_tag = re.sub(r"[^a-zA-Z0-9_-]", "_", tag)
    return f"{safe_name}__{safe_tag}.tar.gz"


def filename_to_image(filename: str) -> Optional[Tuple[str, str]]:
    """Reconstructs original image and tag from a registry filename layout."""
    if not filename.endswith(".tar.gz"):
        return None
    base = filename[:-7]
    if "__" not in base:
        return None
    safe_name, safe_tag = base.rsplit("__", 1)
    return safe_name, safe_tag
