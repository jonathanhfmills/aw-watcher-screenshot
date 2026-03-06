# aw-watcher-screenshot

ActivityWatch watcher that captures screenshots on window changes. Wayland-native — works on COSMIC, wlroots compositors, GNOME, and X11.

Forked from [Srakai/aw-watcher-screenshot](https://github.com/Srakai/aw-watcher-screenshot) with Wayland support, perceptual dedup, and disk management.

## How it works

1. Polls for window changes via the ActivityWatch API (reads from your running `aw-watcher-window` instance)
2. On window change, waits 5s then captures a screenshot via your compositor's native tool
3. Computes a perceptual hash (dHash) — skips the screenshot if the screen looks the same
4. Saves as WebP (3x smaller than PNG) and emits an ActivityWatch event with app, title, path, and hash
5. Cleans up old screenshots when count or disk limits are exceeded

## Screenshot backends

Detected automatically in order:

| Backend | Compositor | Notes |
|---------|-----------|-------|
| `cosmic-screenshot` | COSMIC | Silent capture, no portal needed |
| `grim` | wlroots (Sway, Hyprland, etc.) | |
| `gnome-screenshot` | GNOME | |

## Installation

```bash
pip install .
# or
uv pip install .
```

### NixOS

A Nix package and systemd user service are provided in the author's dotfiles. See `dotfiles/pkgs/aw-watcher-screenshot/default.nix`.

## Usage

```bash
# Default: WebP, window detection via AW API, 5s delay, 5000 file / 2GB limit
aw-watcher-screenshot

# Debug mode
aw-watcher-screenshot --log-level DEBUG

# JPEG output, lower quality
aw-watcher-screenshot --format jpg --quality 50

# Tighter limits
aw-watcher-screenshot --max-screenshots 1000 --max-disk-mb 500

# No window detection (timer-only mode — not very useful)
aw-watcher-screenshot --no-window-detection --capture-on-start
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--format` | `webp` | Image format: `webp`, `jpg`, `png` |
| `--quality` | `70` | WebP/JPEG quality (1-100) |
| `--poll` | `1.0` | Polling interval in seconds |
| `--screenshot-delay` | `5.0` | Seconds to wait after window change |
| `--min-interval` | `5.0` | Minimum seconds between screenshots |
| `--max-screenshots` | `5000` | Max files to keep (0=unlimited) |
| `--max-disk-mb` | `2000` | Max disk usage in MB (0=unlimited) |
| `--hash-threshold` | `4` | dHash distance threshold for dedup |
| `--screens-dir` | `~/.local/share/activitywatch/screenshots` | Screenshot directory |
| `--testing` | off | AW testing mode |

## Dependencies

- `aw-client`, `aw-core` — ActivityWatch integration
- `click` — CLI
- `pillow` — Image format conversion
- `imagehash` — Perceptual hashing (dHash)
- `requests` — AW API queries for window detection
- One of: `cosmic-screenshot`, `grim`, `gnome-screenshot` — screenshot capture

## License

MIT
