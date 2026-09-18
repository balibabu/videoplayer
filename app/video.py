import hashlib
import subprocess
from pathlib import Path

from flask import current_app

from app import state

_meta_cache = {}
_paths = {}


def extensions():
    return set(current_app.config["SUPPORTED_EXTENSIONS"])


def video_id(path):
    return hashlib.md5(str(path).encode("utf-8")).hexdigest()[:16]


def format_size(num):
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


def probe_duration(path):
    key = str(path)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    cached = _meta_cache.get(key)
    if cached and cached[0] == mtime:
        return cached[1]
    duration = None
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
    except Exception:
        duration = None
    _meta_cache[key] = (mtime, duration)
    return duration


def ensure_thumbnail(path):
    thumb_dir = Path(current_app.config["THUMB_DIR"])
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = thumb_dir / (video_id(path) + ".jpg")
    if thumb_path.exists():
        return thumb_path
    duration = probe_duration(path) or 0.0
    seek_pos = max(1.0, duration / 2.0) if duration > 2 else 0.0
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(seek_pos),
        "-i", str(path),
        "-vframes", "1",
        "-vf", f"scale={current_app.config['THUMB_WIDTH']}:-2",
        "-q:v", str(current_app.config["THUMB_QUALITY"]),
        str(thumb_path),
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    except Exception:
        return None
    return thumb_path if thumb_path.exists() else None


def library():
    _paths.clear()
    videos = []
    exts = extensions()
    for folder in state.get_folders():
        try:
            files = sorted(folder.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue
        for f in files:
            if not f.is_file() or f.suffix.lower() not in exts:
                continue
            try:
                size = format_size(f.stat().st_size)
            except OSError:
                continue
            cached = _meta_cache.get(str(f))
            vid = video_id(f)
            _paths[vid] = f
            videos.append(
                {
                    "id": vid,
                    "name": f.name,
                    "folder": folder.name or str(folder),
                    "path": str(folder),
                    "ext": f.suffix.lstrip(".").upper() or "VIDEO",
                    "size": size,
                    "duration": cached[1] if cached else None,
                }
            )
    videos.sort(key=lambda v: (v["folder"].lower(), v["name"].lower()))
    folders = [
        {
            "name": p.name or str(p),
            "path": str(p),
            "count": sum(1 for v in videos if v["path"] == str(p)),
        }
        for p in state.get_folders()
    ]
    return {"videos": videos, "folders": folders}


def get_video(vid):
    path = _paths.get(vid)
    if path is None:
        library()
        path = _paths.get(vid)
    return path if path and path.is_file() else None
