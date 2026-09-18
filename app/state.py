import json
from pathlib import Path

from flask import current_app


def _load():
    file = Path(current_app.config["FOLDERS_FILE"])
    if file.exists():
        try:
            data = json.loads(file.read_text())
            return [Path(p) for p in data.get("folders", [])]
        except Exception:
            pass
    return [Path(current_app.config["VIDEO_DIR"])]


def _save(folders):
    file = Path(current_app.config["FOLDERS_FILE"])
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"folders": [str(f) for f in folders]}, indent=2))


def get_folders():
    folders = []
    seen = set()
    for f in _load():
        if f.is_dir() and str(f) not in seen:
            seen.add(str(f))
            folders.append(f)
    return folders


def add_folder(path):
    try:
        path = Path(path).expanduser().resolve()
    except (OSError, ValueError):
        return None, "Invalid path"
    if not path.is_dir():
        return None, "Not a directory"
    folders = _load()
    if any(str(f) == str(path) for f in folders):
        return None, "Already added"
    folders.append(path)
    _save(folders)
    return path, None


def remove_folder(path):
    try:
        target = str(Path(path).expanduser().resolve())
    except (OSError, ValueError):
        return False
    folders = _load()
    remaining = [f for f in folders if str(f) != target]
    if len(remaining) == len(folders):
        return False
    _save(remaining)
    return True
