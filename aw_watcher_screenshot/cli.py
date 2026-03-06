"""CLI entry point (re-exported for pyproject.toml [project.scripts])."""

# The actual CLI is in the top-level aw-watcher-screenshot.py for direct invocation.
# This module re-exports main() so `pip install` / `nix build` can find it.

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from .models import ImageFormat, WatcherConfig
from .utils import FileUtils
from .watcher import ScreenshotWatcher

LOG = logging.getLogger("aw-watcher-screenshot")


@click.command()
@click.option("--poll", "poll_time", type=float, default=1.0, show_default=True, help="Polling interval in seconds.")
@click.option("--no-window-detection", is_flag=True, default=False, help="Disable window detection.")
@click.option("--capture-on-start", is_flag=True, default=False, help="Capture immediately on startup.")
@click.option("--screens-dir", type=click.Path(dir_okay=True, file_okay=False, writable=True), default=None, help="Screenshot directory.")
@click.option("--format", "image_format", type=click.Choice(["webp", "jpg", "png"], case_sensitive=False), default="webp", show_default=True, help="Image format.")
@click.option("--quality", type=int, default=70, show_default=True, help="Image quality for WebP/JPEG (1-100).")
@click.option("--min-interval", type=float, default=5.0, show_default=True, help="Minimum seconds between screenshots.")
@click.option("--screenshot-delay", type=float, default=5.0, show_default=True, help="Seconds to wait after window change.")
@click.option("--max-screenshots", type=int, default=5000, show_default=True, help="Max screenshots to keep (0=unlimited).")
@click.option("--max-disk-mb", type=int, default=2000, show_default=True, help="Max disk usage in MB (0=unlimited).")
@click.option("--hash-threshold", type=int, default=4, show_default=True, help="Perceptual hash distance threshold.")
@click.option("--testing", is_flag=True, default=False, help="AW testing mode.")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False), default="INFO", show_default=True)
def main(
    poll_time: float,
    no_window_detection: bool,
    capture_on_start: bool,
    screens_dir: Optional[str],
    image_format: str,
    quality: int,
    min_interval: float,
    screenshot_delay: float,
    max_screenshots: int,
    max_disk_mb: int,
    hash_threshold: int,
    testing: bool,
    log_level: str,
):
    """ActivityWatch screenshot watcher — Wayland-native."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    fmt_map = {"webp": ImageFormat.WEBP, "jpg": ImageFormat.JPEG, "png": ImageFormat.PNG}

    config = WatcherConfig(
        poll_interval=poll_time,
        capture_on_start=capture_on_start,
        screenshots_dir=Path(screens_dir) if screens_dir else FileUtils.get_default_screenshot_dir(),
        image_format=fmt_map[image_format.lower()],
        image_quality=quality,
        testing_mode=testing,
        log_level=log_level,
        min_screenshot_interval=min_interval,
        screenshot_delay=screenshot_delay,
        detect_window_info=not no_window_detection,
        max_screenshots=max_screenshots,
        max_disk_mb=max_disk_mb,
        hash_threshold=hash_threshold,
    )

    LOG.info("=" * 60)
    LOG.info("aw-watcher-screenshot (Wayland-native)")
    LOG.info("=" * 60)
    LOG.info(f"Mode: {'Screenshot-only' if no_window_detection else 'Window detection'}")
    LOG.info(f"Screenshots: {config.screenshots_dir}")
    LOG.info(f"Format: {config.image_format.value} (quality={quality})")
    LOG.info(f"Limits: {max_screenshots} files / {max_disk_mb}MB")
    LOG.info("=" * 60)

    try:
        watcher = ScreenshotWatcher(config)
        watcher.start()
    except KeyboardInterrupt:
        LOG.info("Exiting.")
        sys.exit(0)
    except Exception as e:
        LOG.exception(f"Fatal: {e}")
        sys.exit(1)
