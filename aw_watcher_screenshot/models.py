"""Data types and models for the screenshot watcher."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple


class CaptureMode(Enum):
    """Screenshot capture modes."""

    FULL = "full"
    CROP = "crop"


class ImageFormat(Enum):
    """Supported image formats."""

    WEBP = "webp"
    JPEG = "jpg"
    PNG = "png"


@dataclass
class BoundingBox:
    """Window bounding box coordinates."""

    left: int
    top: int
    right: int
    bottom: int

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)

    def to_list(self) -> list[int]:
        return [self.left, self.top, self.right, self.bottom]

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass
class WindowInfo:
    """Information about an active window."""

    title: str = ""
    app: Optional[str] = None

    def get_key(self) -> Tuple[Optional[str], str]:
        """Get unique identifier for window state comparison."""
        return (self.app, self.title)


@dataclass
class WatcherConfig:
    """Configuration for the screenshot watcher."""

    poll_interval: float
    capture_on_start: bool
    screenshots_dir: Path
    image_format: ImageFormat
    image_quality: int
    testing_mode: bool
    log_level: str
    min_screenshot_interval: float
    screenshot_delay: float
    detect_window_info: bool
    max_screenshots: int
    max_disk_mb: int
    hash_threshold: int

    def __post_init__(self):
        self.screenshots_dir = Path(self.screenshots_dir)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
