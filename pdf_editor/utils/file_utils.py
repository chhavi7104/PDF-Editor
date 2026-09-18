"""Small, dependency-free filesystem helpers shared across the app."""

from __future__ import annotations

from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
PDF_EXTENSION = ".pdf"


def is_pdf(path: str | Path) -> bool:
    return Path(path).suffix.lower() == PDF_EXTENSION


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def unique_path(path: str | Path) -> Path:
    """Return `path` if free, otherwise append (1), (2), ... until free."""
    p = Path(path)
    if not p.exists():
        return p
    stem, suffix, parent = p.stem, p.suffix, p.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def parse_page_ranges(spec: str, max_pages: int) -> list[int]:
    """
    Parse a human page spec like "1-3,5,8-10" into a sorted list of
    0-indexed page numbers, validated against `max_pages` (1-indexed count).

    Raises ValueError on malformed input or out-of-range pages.
    """
    if not spec or not spec.strip():
        raise ValueError("Page range is empty.")

    pages: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            parts = chunk.split("-")
            if len(parts) != 2:
                raise ValueError(f"Invalid range segment: '{chunk}'")
            start_s, end_s = parts
            start, end = int(start_s), int(end_s)
            if start < 1 or end < 1 or start > end:
                raise ValueError(f"Invalid range: '{chunk}'")
            if end > max_pages:
                raise ValueError(f"Page {end} exceeds document length ({max_pages}).")
            pages.update(range(start - 1, end))
        else:
            n = int(chunk)
            if n < 1 or n > max_pages:
                raise ValueError(f"Page {n} is out of range (1-{max_pages}).")
            pages.add(n - 1)

    return sorted(pages)
