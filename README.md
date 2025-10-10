# aw-watcher-screenshot

ActivityWatch watcher that captures screenshots on window changes.

## Features

- 📸 **Screenshot on window change** - Automatically captures when you switch windows
- 🖼️ **Single screen capture** - Captures only your primary screen
- ⏱️ **Smart rate limiting** - Max 1 screenshot per 5 seconds by default
- ⏰ **Delay after change** - 5-second delay after window change (lets you settle in, no meaningless screenshots)
- 📊 **ActivityWatch integration** - Stores metadata in AW database

On macOS screenshots are stored in
`~/Library/Application Support/activitywatch/Screenshots`

## Installation

```bash
# Install dependencies
uv sync

# macOS users (for window detection):
pip install pyobjc

# Linux users (for window detection):
pip install python-xlib ewmh
```

## Quick Start

```bash
uv run python aw-watcher-screenshot.py
```

## Platform Support

Tested only on macOS

- ✅ **macOS**: Works enough for me (does not capture active window title)
- ✅ **Windows**: Should support
- ✅ **Linux**: Should support X11 (requires `python-xlib ewmh` or `xdotool`)
- ⚠️ **Wayland**: Limited (no native window detection)
