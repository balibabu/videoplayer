# MX Player Server

A self-hosted local video streaming server with an MX Player style web UI. Point it at folders on the machine, and it scans them for videos, generates thumbnails and durations with ffmpeg, and streams everything to any browser on your LAN — with seek support, playlist controls, and keyboard shortcuts.

## Features

- Pick video folders from the browser — browse the server filesystem or type a path; folders are remembered across restarts (`.folders.json`)
- Folder library UI with tabs, search, per-folder view, and remove buttons
- Lazy thumbnail generation and duration probing (ffmpeg/ffprobe), cached on disk and in memory
- HTTP range streaming, so seeking works in the player
- Custom web player: prev/next, volume, speed, picture-in-picture, fullscreen, double-tap ±10s gestures, keyboard shortcuts
- Basic auth protection for every route

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- `ffmpeg` and `ffprobe` on `PATH` (thumbnails and durations silently degrade if missing)

## How It Works

The app is a Flask application factory split into small modules:

| Module | Responsibility |
|---|---|
| `run.py` | Entry point; creates the app and starts the dev server |
| `config.py` | `Config` class; loads all values from `.env` (with sane defaults) |
| `app/__init__.py` | `create_app()` factory; registers the blueprint |
| `app/auth.py` | Basic auth check, challenge, and `@requires_auth` decorator |
| `app/state.py` | Folder store persisted in `FOLDERS_FILE` (add/remove/list) |
| `app/video.py` | Library scanning, video IDs, ffprobe duration cache, ffmpeg thumbnails |
| `app/routes.py` | Page + JSON/streaming routes |
| `app/templates/index.html` | Tailwind dark UI, folder picker dialog, custom player |

Flow: on page load the server scans all configured folders and embeds the library as JSON in the page. Cards render instantly (name, size, type); the browser then lazily fetches `/api/thumb/<id>` (generates and caches a JPEG on first hit) and `/api/meta/<id>` (ffprobe duration, cached by mtime). Playback streams via `/stream/<id>` with range requests.

Videos are addressed by a short MD5 of their absolute path, so filenames with odd characters are never a problem. Thumbnails live in `THUMB_DIR` keyed by the same hash and are reused across restarts.

## Development

```bash
cp .env.example .env       # then edit credentials
uv sync
uv run python run.py
```

Open `http://localhost:8080` and sign in with `AUTH_USERNAME` / `AUTH_PASSWORD`. The dev server auto-reloads templates when `DEBUG=true`.

## Production

Use a WSGI server instead of the Flask dev server:

```bash
uv add gunicorn
uv run gunicorn --workers 2 --threads 8 --timeout 120 --bind 0.0.0.0:8080 run:app
```

Example systemd unit (`/etc/systemd/system/mxplayer.service`):

```ini
[Unit]
Description=MX Player Server
After=network.target

[Service]
User=youruser
WorkingDirectory=/opt/mxplayer
ExecStart=/opt/mxplayer/.venv/bin/gunicorn --workers 2 --threads 8 --timeout 120 --bind 0.0.0.0:8080 run:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now mxplayer
```

Notes:

- Set a strong, unique `AUTH_PASSWORD` before exposing the server beyond localhost.
- Basic auth travels as plain text; front it with a TLS reverse proxy (Caddy/nginx) if it leaves your machine.
- `/api/browse` lists directories to authenticated users — set `BROWSE_ROOT` to limit where browsing starts.

## Configuration

All values live in `.env` (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8080` | Listen port |
| `DEBUG` | `false` | Flask debug mode |
| `AUTH_USERNAME` / `AUTH_PASSWORD` | `admin` / `password123` | Basic auth credentials |
| `AUTH_REALM` | `MX Player Server Login` | Auth realm string |
| `VIDEO_DIR` | app directory | Seed folder used on first run |
| `THUMB_DIR` | `<VIDEO_DIR>/.thumbnails` | Thumbnail cache directory |
| `SUPPORTED_EXTENSIONS` | `.mp4,.mkv,...` | Comma-separated list of video extensions |
| `FOLDERS_FILE` | `.folders.json` | Persisted list of UI-added folders |
| `BROWSE_ROOT` | home directory | Starting directory of the folder picker |
| `THUMB_WIDTH` | `480` | Thumbnail width in px (height auto) |
| `THUMB_QUALITY` | `3` | JPEG quality (2 = best, 31 = worst) |

## API

All endpoints require basic auth.

| Endpoint | Description |
|---|---|
| `GET /` | Web UI |
| `GET /api/library` | Folders + videos as JSON |
| `GET /api/browse?path=…` | List subdirectories (with video counts) for the picker |
| `POST /api/folders` `{"path": "…"}` | Add a folder to the library |
| `DELETE /api/folders` `{"path": "…"}` | Remove a folder |
| `GET /api/meta/<id>` | Duration (seconds), via ffprobe |
| `GET /api/thumb/<id>` | Thumbnail JPEG (generated on demand) |
| `GET /stream/<id>` | Video stream with range support |

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / pause |
| `←` / `→` | Seek −5s / +5s |
| `↑` / `↓` | Volume up / down |
| `N` / `P` | Next / previous video |
| `F` | Fullscreen |
| `M` | Mute |
| `Esc` | Close player |
