# aw-watcher-screenshot

ActivityWatch watcher that captures screenshots on window changes.

## Features

- 📸 **Screenshot on window change** - Automatically captures when you switch windows
- ⚡ **Fast mode** - Optional `--no-window-detection` for minimal overhead
- 🖼️ **Single screen capture** - Captures only your primary screen (configurable)
- ⏱️ **Smart rate limiting** - Max 1 screenshot per 5 seconds by default
- ⏰ **Delay after change** - 5-second delay after window change (lets you settle in)
- 🎨 **PNG or JPEG** - Choose your preferred format
- ✂️ **Optional cropping** - Crop to active window bounds (when enabled)
- 📊 **ActivityWatch integration** - Stores metadata in AW database

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# macOS users (for window detection):
pip install pyobjc

# Linux users (for window detection):
pip install python-xlib ewmh

# Optional: for JPEG support
pip install Pillow
```

## Quick Start

### Fast Mode (Recommended)

Fastest performance, no window detection overhead:

```bash
python aw-watcher-screenshot.py --no-window-detection
```

### Window Detection Mode

Captures window metadata (app name, title):

```bash
python aw-watcher-screenshot.py
```

## Usage

```bash
# Basic usage (window detection enabled)
python aw-watcher-screenshot.py

# Fast mode (screenshot-only, no window detection)
python aw-watcher-screenshot.py --no-window-detection

# Capture all screens instead of just screen 1
python aw-watcher-screenshot.py --screen 0

# Use JPEG instead of PNG
python aw-watcher-screenshot.py --jpeg --quality 85

# Custom screenshot directory
python aw-watcher-screenshot.py --screens-dir ~/my-screenshots

# Faster screenshots (2 second intervals)
python aw-watcher-screenshot.py --min-interval 2.0 --screenshot-delay 2.0

# Enable cropping to active window
python aw-watcher-screenshot.py --crop-active-window
```

## Platform Support

- ✅ **macOS**: Full support (requires `pyobjc` for window detection)
- ✅ **Windows**: Full support
- ✅ **Linux**: X11 support (requires `python-xlib ewmh` or `xdotool`)
- ⚠️ **Wayland**: Limited (no native window detection)
