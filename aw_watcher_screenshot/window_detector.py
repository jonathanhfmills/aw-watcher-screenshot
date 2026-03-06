"""Window detection — Wayland-native via AW API, with X11 fallback."""

import logging
import socket
import subprocess
from typing import Optional, Protocol

import requests

from .models import WindowInfo

LOG = logging.getLogger(__name__)


class WindowDetector(Protocol):
    def get_active_window(self) -> Optional[WindowInfo]: ...


class AWAPIWindowDetector:
    """Query the running aw-watcher-window instance via the AW REST API.

    Works with any AW window watcher (aw-watcher-window-cosmic, aw-watcher-window, etc.)
    — zero compositor coupling.
    """

    def __init__(self, port: int = 5600):
        self._hostname = socket.gethostname()
        self._url = (
            f"http://127.0.0.1:{port}/api/0/buckets/"
            f"aw-watcher-window_{self._hostname}/events?limit=1"
        )
        self._session = requests.Session()

    def get_active_window(self) -> Optional[WindowInfo]:
        try:
            resp = self._session.get(self._url, timeout=2)
            resp.raise_for_status()
            events = resp.json()
            if not events:
                return None
            data = events[0].get("data", {})
            return WindowInfo(
                title=data.get("title", ""),
                app=data.get("app"),
            )
        except Exception as e:
            LOG.debug(f"AW API window detection failed: {e}")
            return None


class LinuxWindowDetector:
    """X11 fallback: xlib → xdotool."""

    def get_active_window(self) -> Optional[WindowInfo]:
        return self._try_xlib() or self._try_xdotool()

    def _try_xlib(self) -> Optional[WindowInfo]:
        try:
            from Xlib import X
            from ewmh import EWMH

            ewmh = EWMH()
            window = ewmh.getActiveWindow()
            if not window:
                return None

            title = ewmh.getWmName(window) or ""
            wm_class = window.get_wm_class()
            app = wm_class[0] if wm_class else None

            return WindowInfo(title=title, app=app)
        except Exception:
            return None

    def _try_xdotool(self) -> Optional[WindowInfo]:
        try:
            wid = (
                subprocess.check_output(
                    ["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL
                )
                .decode()
                .strip()
            )
            title = (
                subprocess.check_output(
                    ["xdotool", "getwindowname", wid], stderr=subprocess.DEVNULL
                )
                .decode()
                .rstrip()
            )

            # Get PID → app name from /proc
            app = None
            try:
                pid_output = subprocess.check_output(
                    ["xprop", "-id", wid, "_NET_WM_PID"],
                    stderr=subprocess.DEVNULL,
                ).decode()
                pid = int(pid_output.strip().split()[-1])
                with open(f"/proc/{pid}/comm") as f:
                    app = f.read().strip()
            except Exception:
                pass

            return WindowInfo(title=title, app=app)
        except Exception:
            return None


def get_window_detector() -> Optional[WindowDetector]:
    """Return the best available window detector.

    Order: AW API (Wayland-native) → xlib → xdotool
    """
    # Try AW API first — works on any compositor with an AW window watcher
    try:
        det = AWAPIWindowDetector()
        result = det.get_active_window()
        if result is not None:
            LOG.info("Window detection: AW API")
            return det
    except Exception:
        pass

    # Fall back to X11
    try:
        det = LinuxWindowDetector()
        result = det.get_active_window()
        if result is not None:
            LOG.info("Window detection: X11")
            return det
    except Exception:
        pass

    LOG.warning("No window detector available")
    return None
