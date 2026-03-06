"""Utility functions for file operations, time handling, and disk management."""

import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG = logging.getLogger(__name__)


class FileUtils:
    _SANITIZE_RE = re.compile(r"[^A-Za-z0-9._-]+")

    @staticmethod
    def sanitize_filename(text: str, max_length: int = 64) -> str:
        if not text:
            return "unknown"
        text = text.strip().replace(" ", "-")
        text = FileUtils._SANITIZE_RE.sub("-", text)
        text = re.sub(r"-{2,}", "-", text).strip("-")
        return text[:max_length] or "x"

    @staticmethod
    def write_atomic(path: Path, data: bytes) -> None:
        temp_path = path.with_suffix(f".tmp.{uuid.uuid4().hex}")
        try:
            with open(temp_path, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            temp_path.replace(path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    @staticmethod
    def get_default_screenshot_dir() -> Path:
        home = Path.home()
        base = (
            Path(os.getenv("XDG_DATA_HOME", home / ".local" / "share"))
            / "activitywatch"
            / "screenshots"
        )
        base.mkdir(parents=True, exist_ok=True)
        return base


class TimeUtils:
    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(tz=timezone.utc)

    @staticmethod
    def to_filesystem_iso(dt: datetime) -> str:
        return dt.isoformat(timespec="milliseconds").replace(":", "-")

    @staticmethod
    def sleep_aligned(interval: float) -> None:
        now = time.time()
        sleep_duration = interval - (now % interval)
        if sleep_duration < 0 or sleep_duration > interval:
            sleep_duration = max(0.0, min(interval, sleep_duration))
        time.sleep(sleep_duration)


def cleanup_old_screenshots(
    screenshots_dir: Path, max_screenshots: int, max_disk_mb: int
) -> None:
    """Delete oldest screenshots when count or disk usage exceeds limits."""
    exts = {".webp", ".jpg", ".jpeg", ".png"}
    files = sorted(
        (f for f in screenshots_dir.iterdir() if f.suffix.lower() in exts),
        key=lambda f: f.stat().st_mtime,
    )

    # Enforce count limit
    if max_screenshots > 0:
        while len(files) > max_screenshots:
            victim = files.pop(0)
            LOG.debug(f"Cleanup (count): removing {victim.name}")
            victim.unlink(missing_ok=True)

    # Enforce disk limit
    if max_disk_mb > 0:
        max_bytes = max_disk_mb * 1024 * 1024
        total = sum(f.stat().st_size for f in files)
        while total > max_bytes and files:
            victim = files.pop(0)
            total -= victim.stat().st_size
            LOG.debug(f"Cleanup (disk): removing {victim.name}")
            victim.unlink(missing_ok=True)
