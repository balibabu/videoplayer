import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_EXTENSIONS = (".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v")


def _parse_extensions(value):
    if not value:
        return DEFAULT_EXTENSIONS
    return tuple(
        ext.strip().lower() if ext.strip().startswith(".") else f".{ext.strip().lower()}"
        for ext in value.split(",")
        if ext.strip()
    )


def _as_bool(value, default=False):
    return (value or str(default)).strip().lower() in ("1", "true", "yes", "on")


def _browse_root():
    raw = (os.getenv("BROWSE_ROOT") or "").strip()
    if not raw:
        try:
            return Path.home().resolve()
        except (RuntimeError, OSError):
            return Path("/")
    try:
        path = Path(raw).expanduser().resolve()
        return path if path.is_dir() else Path("/")
    except (RuntimeError, OSError, ValueError):
        return Path("/")


class Config:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8080"))
    DEBUG = _as_bool(os.getenv("DEBUG"))

    AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "password123")
    AUTH_REALM = os.getenv("AUTH_REALM", "MX Player Server Login")

    VIDEO_DIR = Path(os.getenv("VIDEO_DIR", str(BASE_DIR))).expanduser().resolve()
    THUMB_DIR = Path(os.getenv("THUMB_DIR", str(VIDEO_DIR / ".thumbnails"))).expanduser().resolve()
    SUPPORTED_EXTENSIONS = _parse_extensions(os.getenv("SUPPORTED_EXTENSIONS"))

    FOLDERS_FILE = Path(os.getenv("FOLDERS_FILE", str(BASE_DIR / ".folders.json"))).expanduser().resolve()
    BROWSE_ROOT = _browse_root()

    THUMB_WIDTH = int(os.getenv("THUMB_WIDTH", "480"))
    THUMB_QUALITY = int(os.getenv("THUMB_QUALITY", "3"))
