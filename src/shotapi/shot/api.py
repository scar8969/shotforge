from ..models import ApiKey, Shot, db
from .cache import cache_key, get, put
from .capture import capture
from .quota import hit

from flask import Blueprint, jsonify, request, send_file, abort
import io

bp = Blueprint("shot", __name__)

def _auth():
    k = request.headers.get("x-api-key", "")
    return ApiKey.query.filter_by(key=k).first()

@bp.get("/api/shot")
def shot():
    key = _auth()
    if not key:
        return jsonify({"error": "unauthorized"}), 401
    if not hit(key.id):
        return jsonify({"error": "quota exceeded"}), 429
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "url required"}), 400
    fmt = request.args.get("format", "png")
    full = request.args.get("full", "false") == "true"
    viewport = (request.args.get("width", 1280, type=int), request.args.get("height", 800, type=int))
    ck = cache_key(url, fmt, viewport, full)
    data = get(ck)
    cached = True
    if data is None:
        try:
            data = capture(url, fmt, viewport, full)
        except Exception:
            return jsonify({"error": "capture failed"}), 502
        put(ck, data)
        cached = False
    db.session.add(Shot(key_id=key.id, url=url, format=fmt, size=len(data), cached=1 if cached else 0))
    db.session.commit()
    return send_file(io.BytesIO(data), mimetype=f"image/{fmt}")

@bp.post("/api/keys")
def add_key():
    import secrets
    payload = request.get_json(force=True, silent=True) or {}
    k = ApiKey(key="sk_" + secrets.token_urlsafe(24), quota=payload.get("quota", 1000))
    db.session.add(k)
    db.session.commit()
    return jsonify({"key": k.key})  # shown once

@bp.get("/api/keys/<int:kid>/usage")
def usage(kid):
    k = ApiKey.query.get_or_404(kid)
    return jsonify({"used": k.used, "quota": k.quota})
