"""Favorites: save APOD / Mars images and generate thumbnails.

DEMO NOTE: this module intentionally contains two security issues for the
Black Duck Polaris demo:
  1. SCA  - image decoding via Pillow (Image.open) makes the Pillow
            CVE-2023-4863 (libwebp, CISA KEV) finding reachable.
  2. SAST - search_favorites() builds SQL with an f-string (SQL injection).
"""
import io
import sqlite3
from urllib.parse import urlparse

import requests
from flask import Blueprint, current_app, jsonify, request, send_file
from PIL import Image

favorites_bp = Blueprint("favorites", __name__)

THUMB_SIZE = (256, 256)
ALLOWED_IMAGE_HOSTS = {
    "apod.nasa.gov",
    "mars.nasa.gov",
    "mars.jpl.nasa.gov",
    "images-assets.nasa.gov",
}


def get_db():
    conn = sqlite3.connect(current_app.config.get("FAVORITES_DB", "favorites.db"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS favorites ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " title TEXT NOT NULL,"
        " url TEXT NOT NULL)"
    )
    return conn


@favorites_bp.route("/api/favorites", methods=["POST"])
def add_favorite():
    data = request.get_json(silent=True) or {}
    title, url = data.get("title"), data.get("url")
    if not title or not url:
        return jsonify({"error": "title and url are required"}), 400

    conn = get_db()
    with conn:
        cur = conn.execute(
            "INSERT INTO favorites (title, url) VALUES (?, ?)", (title, url)
        )
    fav_id = cur.lastrowid
    conn.close()
    return jsonify({"id": fav_id, "title": title, "url": url}), 201


@favorites_bp.route("/api/favorites/search")
def search_favorites():
    q = request.args.get("q", "")
    conn = get_db()
    # Builds the query by string formatting -> SQL injection (demo SAST finding)
    rows = conn.execute(
        f"SELECT id, title, url FROM favorites WHERE title LIKE '%{q}%'"
    ).fetchall()
    conn.close()
    return jsonify([{"id": r[0], "title": r[1], "url": r[2]} for r in rows])


@favorites_bp.route("/api/favorites/<int:fav_id>/thumbnail")
def thumbnail(fav_id):
    conn = get_db()
    row = conn.execute("SELECT url FROM favorites WHERE id = ?", (fav_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "favorite not found"}), 404

    url = row[0]
    if urlparse(url).hostname not in ALLOWED_IMAGE_HOSTS:
        return jsonify({"error": "image host not allowed"}), 400

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502

    # Decodes a remote image (JPEG/PNG/WebP...) -> reachable Pillow/libwebp code path
    img = Image.open(io.BytesIO(resp.content))
    img.thumbnail(THUMB_SIZE, Image.LANCZOS)  # LANCZOS works on Pillow 8.x and 10+/11+

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG")
    out.seek(0)
    return send_file(out, mimetype="image/png")
