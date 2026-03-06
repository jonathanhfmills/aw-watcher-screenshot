"""Screenshot capture via compositor tools, with Pillow format conversion."""

import io
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

from .models import ImageFormat

LOG = logging.getLogger(__name__)


class ImageCapture:
    """Captures screenshots via compositor-native tools and converts to the target format."""

    def __init__(self, image_format: ImageFormat, image_quality: int = 70):
        self.image_format = image_format
        self.image_quality = image_quality
        self._backend = _detect_backend()
        if self._backend is None:
            raise RuntimeError(
                "No screenshot backend available. "
                "Install one of: cosmic-screenshot, grim, gnome-screenshot"
            )
        LOG.info(f"Screenshot backend: {self._backend}")

    def capture(self) -> Tuple[bytes, ImageFormat]:
        """Capture a screenshot and return (encoded_bytes, format)."""
        png_path = _capture_png(self._backend)
        try:
            image = Image.open(png_path)
            buf = io.BytesIO()

            if self.image_format == ImageFormat.WEBP:
                image.save(buf, format="WEBP", quality=self.image_quality)
            elif self.image_format == ImageFormat.JPEG:
                image = image.convert("RGB")
                image.save(buf, format="JPEG", quality=self.image_quality)
            else:
                image.save(buf, format="PNG")

            return buf.getvalue(), self.image_format
        finally:
            png_path.unlink(missing_ok=True)


def _detect_backend() -> Optional[str]:
    """Find the first available screenshot tool."""
    for tool in ("cosmic-screenshot", "grim", "gnome-screenshot"):
        if shutil.which(tool):
            return tool
    return None


def _capture_png(backend: str) -> Path:
    """Invoke the backend tool and return a Path to the resulting PNG."""
    tmpdir = Path(tempfile.mkdtemp(prefix="aw-screenshot-"))

    if backend == "cosmic-screenshot":
        subprocess.run(
            [
                "cosmic-screenshot",
                "--interactive=false",
                "--modal=false",
                "--notify=false",
                f"--save-dir={tmpdir}",
            ],
            check=True,
            capture_output=True,
        )
    elif backend == "grim":
        out = tmpdir / "screenshot.png"
        subprocess.run(["grim", str(out)], check=True, capture_output=True)
    elif backend == "gnome-screenshot":
        out = tmpdir / "screenshot.png"
        subprocess.run(
            ["gnome-screenshot", "-f", str(out)],
            check=True,
            capture_output=True,
        )

    # Find the PNG file the tool wrote
    pngs = list(tmpdir.glob("*.png"))
    if not pngs:
        tmpdir.rmdir()
        raise RuntimeError(f"{backend} produced no output file")

    return pngs[0]
