"""Main screenshot watcher implementation."""

import io
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

import aw_client
import imagehash
from aw_core import Event
from PIL import Image

from .capture import ImageCapture
from .models import CaptureMode, ImageFormat, WatcherConfig, WindowInfo
from .utils import FileUtils, TimeUtils, cleanup_old_screenshots
from .window_detector import get_window_detector

LOG = logging.getLogger(__name__)


class ScreenshotWatcher:
    def __init__(self, config: WatcherConfig):
        self.config = config

        self.window_detector = None
        if config.detect_window_info:
            self.window_detector = get_window_detector()
            if self.window_detector is None:
                LOG.warning("Window detection not available. Running in screenshot-only mode.")

        self.image_capture = ImageCapture(config.image_format, config.image_quality)

        self.client = aw_client.ActivityWatchClient(
            "aw-watcher-screenshot", testing=config.testing_mode
        )
        self.bucket_id = f"{self.client.client_name}_{self.client.client_hostname}"

        # State
        self.last_window_key: Optional[Tuple] = None
        self.last_screenshot_time: Optional[datetime] = None
        self.last_phash: Optional[imagehash.ImageHash] = None
        self.pending_window_change: Optional[Tuple[datetime, Optional[WindowInfo]]] = None
        self._last_cleanup = 0.0

    def start(self) -> None:
        LOG.info(
            f"Starting (poll={self.config.poll_interval}s, "
            f"window_detection={self.window_detector is not None})"
        )

        self.client.wait_for_start()
        self.client.connect()
        self.client.create_bucket(self.bucket_id, "app.screenshot")

        if self.config.capture_on_start:
            window_info = None
            if self.window_detector:
                window_info = self.window_detector.get_active_window()
                if window_info:
                    self.last_window_key = window_info.get_key()
            self._capture_and_emit(window_info)

        self._run_loop()

    def _run_loop(self) -> None:
        while True:
            now = TimeUtils.now_utc()

            window_info = None
            if self.window_detector:
                window_info = self.window_detector.get_active_window()
                LOG.debug(f"Window: {window_info.get_key() if window_info else None}")

            current_key = window_info.get_key() if window_info else None
            window_changed = current_key != self.last_window_key and window_info is not None

            if window_changed:
                LOG.info(f"Window changed: {self.last_window_key} -> {current_key}")
                self.pending_window_change = (now, window_info)
                self.last_window_key = current_key

            if self.pending_window_change:
                change_time, pending_info = self.pending_window_change
                elapsed = (now - change_time).total_seconds()

                if elapsed >= self.config.screenshot_delay:
                    should_capture = True
                    if self.last_screenshot_time:
                        since_last = (now - self.last_screenshot_time).total_seconds()
                        if since_last < self.config.min_screenshot_interval:
                            should_capture = False
                            LOG.debug(f"Rate limited ({since_last:.1f}s < {self.config.min_screenshot_interval}s)")

                    if should_capture:
                        self._capture_and_emit(pending_info)
                        self.last_screenshot_time = now
                        self.pending_window_change = None

            # Periodic disk cleanup (every 60s)
            if time.monotonic() - self._last_cleanup > 60:
                self._cleanup()
                self._last_cleanup = time.monotonic()

            TimeUtils.sleep_aligned(self.config.poll_interval)

    def _capture_and_emit(self, window_info: Optional[WindowInfo]) -> None:
        timestamp = TimeUtils.now_utc()

        try:
            image_bytes, image_format = self.image_capture.capture()
        except Exception as e:
            LOG.error(f"Capture failed: {e}")
            return

        # Perceptual hash dedup
        try:
            img = Image.open(io.BytesIO(image_bytes))
            phash = imagehash.dhash(img)
            if self.last_phash is not None:
                distance = self.last_phash - phash
                if distance <= self.config.hash_threshold:
                    LOG.debug(f"Duplicate screen (dhash distance={distance}), skipping")
                    return
            self.last_phash = phash
        except Exception as e:
            LOG.warning(f"Perceptual hash failed: {e}")
            phash = None

        # Build filename
        timestamp_str = TimeUtils.to_filesystem_iso(timestamp)
        app_name = window_info.app if window_info else "unknown"
        title = window_info.title if window_info else ""

        filename = (
            f"{timestamp_str}_"
            f"{FileUtils.sanitize_filename(app_name)}_"
            f"{FileUtils.sanitize_filename(title)}"
            f".{image_format.value}"
        )
        filepath = self.config.screenshots_dir / filename

        try:
            FileUtils.write_atomic(filepath, image_bytes)
        except Exception as e:
            LOG.error(f"Failed to write screenshot: {e}")
            return

        # AW event with metadata
        event_data = {
            "app": window_info.app if window_info else "unknown",
            "title": window_info.title if window_info else "",
            "path": str(filepath.absolute()),
            "phash": str(phash) if phash else None,
        }

        event = Event(
            timestamp=timestamp,
            duration=timedelta(seconds=0),
            data=event_data,
        )

        try:
            self.client.insert_event(self.bucket_id, event)
            LOG.info(f"Captured {app_name} ({title}) -> {filepath.name}")
        except Exception as e:
            LOG.error(f"Failed to insert AW event: {e}")

    def _cleanup(self) -> None:
        try:
            cleanup_old_screenshots(
                self.config.screenshots_dir,
                self.config.max_screenshots,
                self.config.max_disk_mb,
            )
        except Exception as e:
            LOG.warning(f"Cleanup failed: {e}")
