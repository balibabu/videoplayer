from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
)

from app import state, video
from app.auth import requires_auth

bp = Blueprint("main", __name__)


@bp.route("/")
@requires_auth
def index():
    return render_template("index.html", library=video.library())


@bp.route("/api/library")
@requires_auth
def api_library():
    return jsonify(video.library())


@bp.route("/api/browse")
@requires_auth
def api_browse():
    raw = (request.args.get("path") or "").strip()
    try:
        if raw:
            current = Path(raw).expanduser().resolve()
        else:
            current = Path(current_app.config["BROWSE_ROOT"])
    except (OSError, RuntimeError, ValueError) as e:
        current_app.logger.warning("browse: cannot resolve %r: %s", raw, e)
        return jsonify({"error": f"Cannot resolve path: {e}"}), 400
    if not current.is_dir():
        current_app.logger.warning("browse: not a directory: %s", current)
        return jsonify({"error": f"Not a directory: {current}"}), 404
    exts = video.extensions()
    dirs = []
    try:
        entries = sorted(current.iterdir(), key=lambda p: p.name.lower())
    except OSError as e:
        current_app.logger.warning("browse: cannot list %s: %s", current, e)
        return jsonify({"error": f"Cannot list directory: {e}"}), 400
    for entry in entries:
        if entry.name.startswith("."):
            continue
        try:
            if not entry.is_dir():
                continue
            count = sum(
                1 for c in entry.iterdir() if c.is_file() and c.suffix.lower() in exts
            )
        except OSError:
            continue
        dirs.append({"name": entry.name, "path": str(entry), "count": count})
    parent = str(current.parent) if current.parent != current else None
    return jsonify({"path": str(current), "parent": parent, "dirs": dirs})


@bp.route("/api/folders", methods=["POST"])
@requires_auth
def api_add_folder():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "Path is required"}), 400
    _, error = state.add_folder(path)
    if error:
        status = 409 if error == "Already added" else 400
        return jsonify({"error": error}), status
    return jsonify(video.library()), 201


@bp.route("/api/folders", methods=["DELETE"])
@requires_auth
def api_remove_folder():
    data = request.get_json(silent=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "Path is required"}), 400
    if not state.remove_folder(path):
        return jsonify({"error": "Folder not found"}), 404
    return jsonify(video.library())


@bp.route("/api/meta/<vid>")
@requires_auth
def api_meta(vid):
    path = video.get_video(vid)
    if path is None:
        abort(404)
    return jsonify({"id": vid, "duration": video.probe_duration(path)})


@bp.route("/api/thumb/<vid>")
@requires_auth
def api_thumb(vid):
    path = video.get_video(vid)
    if path is None:
        abort(404)
    thumb = video.ensure_thumbnail(path)
    if thumb is None:
        abort(404)
    resp = send_file(thumb, mimetype="image/jpeg", conditional=True)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@bp.route("/stream/<vid>")
@requires_auth
def stream(vid):
    path = video.get_video(vid)
    if path is None:
        abort(404)
    return send_file(path, conditional=True)
