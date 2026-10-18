import os
import traceback
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from . import paths
from .models import ApiKey, Shot, db
from .shot.api import bp
from .shot.cache import cache_key, get, put
from .shot.capture import capture

paths.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)


def build_app():
    """Build the application: configuration, database, then routes."""
    app = Flask(
        __name__, template_folder=str(paths.TEMPLATES_DIR), instance_path=str(paths.INSTANCE_DIR)
    )
    app.secret_key = os.environ.get("SECRET_KEY", "shotapi-dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(paths.INSTANCE_DIR / "shotapi.db")
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(bp)

    @app.context_processor
    def _ctx():
        return {"app_name": "\U0001f4f8 shotapi"}

    def _cache_dir():
        from .shot import cache as _c

        return _c._CACHE_DIR

    def _cache_entries():
        d = _cache_dir()
        out = []
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                p = os.path.join(d, name)
                if not os.path.isfile(p):
                    continue
                st = os.stat(p)
                out.append(
                    {
                        "name": name,
                        "size": st.st_size,
                        "mtime": datetime.utcfromtimestamp(st.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                )
        return out

    def _cache_bytes():
        return sum(e["size"] for e in _cache_entries())

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "shotapi", "version": "0.1.0"})

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            key_count=ApiKey.query.count(),
            shot_count=Shot.query.count(),
            used_total=db.session.query(db.func.coalesce(db.func.sum(ApiKey.used), 0)).scalar()
            or 0,
            quota_total=db.session.query(db.func.coalesce(db.func.sum(ApiKey.quota), 0)).scalar()
            or 0,
            cache_files=len(_cache_entries()),
            cache_bytes=_cache_bytes(),
            cache_dir=_cache_dir(),
            recent=Shot.query.order_by(Shot.id.desc()).limit(10).all(),
        )

    def _form_defaults():
        return {
            "url": "https://example.com",
            "format": "png",
            "width": 1280,
            "height": 800,
            "full": False,
        }

    @app.route("/playground", methods=["GET", "POST"])
    def playground():
        form = _form_defaults()
        result = None
        error = None
        if request.method == "POST":
            form["url"] = (request.form.get("url") or "").strip()
            form["format"] = request.form.get("format") or "png"
            try:
                form["width"] = int(request.form.get("width") or 1280)
            except ValueError:
                form["width"] = 1280
            try:
                form["height"] = int(request.form.get("height") or 800)
            except ValueError:
                form["height"] = 800
            form["full"] = (request.form.get("full") or "false") == "true"

            if not form["url"]:
                flash("A target URL is required.", "err")
            else:
                viewport = (form["width"], form["height"])
                ck = cache_key(form["url"], form["format"], viewport, form["full"])
                data = get(ck)
                cached = data is not None
                if data is None:
                    try:
                        data = capture(form["url"], form["format"], viewport, form["full"])
                        put(ck, data)
                    except Exception:
                        # Chromium cannot start in this sandbox; the API answers 502 here.
                        error = traceback.format_exc(limit=8)
                if error is None:
                    db.session.add(
                        Shot(
                            key_id=None,
                            url=form["url"],
                            format=form["format"],
                            size=len(data),
                            cached=1 if cached else 0,
                        )
                    )
                    db.session.commit()
                    result = {
                        "cached": cached,
                        "size": len(data),
                        "content_type": "image/" + form["format"],
                        "cache_key": ck,
                    }
                    flash(
                        "Captured %d bytes (%s)."
                        % (len(data), "cache hit" if cached else "cache miss"),
                        "ok",
                    )

        return render_template(
            "playground.html",
            form=form,
            result=result,
            error=error,
            entries=_cache_entries(),
            cache_files=len(_cache_entries()),
            cache_bytes=_cache_bytes(),
            cache_dir=_cache_dir(),
        )

    @app.route("/keys", methods=["GET", "POST"])
    def keys_page():
        import secrets

        new_key = None
        if request.method == "POST":
            try:
                quota = int(request.form.get("quota") or 1000)
            except ValueError:
                quota = 1000
            k = ApiKey(key="sk_" + secrets.token_urlsafe(24), quota=quota)
            db.session.add(k)
            db.session.commit()
            new_key = k.key
            flash("Key #%d created." % k.id, "ok")
        return render_template(
            "keys.html", rows=ApiKey.query.order_by(ApiKey.id.desc()).all(), new_key=new_key
        )

    @app.get("/k/<int:kid>")
    def key_detail(kid):
        k = ApiKey.query.get_or_404(kid)
        return render_template(
            "key.html",
            k=k,
            remaining=max(0, (k.quota or 0) - (k.used or 0)),
            shots=Shot.query.filter_by(key_id=k.id).order_by(Shot.id.desc()).limit(50).all(),
        )

    @app.post("/k/<int:kid>/reset")
    def key_reset(kid):
        k = ApiKey.query.get_or_404(kid)
        k.used = 0
        db.session.commit()
        flash("Usage counter reset for key #%d." % k.id, "ok")
        return redirect(url_for("key_detail", kid=k.id))

    @app.get("/docs")
    def api_docs():
        rules = []
        for r in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
            methods = ",".join(
                sorted(m for m in r.methods if m in {"GET", "POST", "PUT", "PATCH", "DELETE"})
            )
            if not methods:
                continue
            rules.append({"methods": methods, "rule": str(r), "endpoint": r.endpoint})
        return render_template("api_docs.html", rules=rules)

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))

    return app


app = build_app()
