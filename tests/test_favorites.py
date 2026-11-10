"""Behavioral tests for the favorites feature.

These pass on both the vulnerable PR code and the fixed code (parameterized
query + upgraded Pillow), so in CI the only red check on the demo PR is the
Polaris policy gate, and in Stage 5 the tests prove the fixes didn't break
anything.
"""
import io
import os
import sys
from unittest import mock

import pytest
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    flask_app.config.update(TESTING=True, FAVORITES_DB=str(tmp_path / "test.db"))
    with flask_app.test_client() as c:
        yield c


def _png_bytes(size=(800, 600)):
    buf = io.BytesIO()
    Image.new("RGB", size, (20, 40, 80)).save(buf, format="PNG")
    return buf.getvalue()


def _add(client, title, url="https://apod.nasa.gov/apod/image/test.jpg"):
    resp = client.post("/api/favorites", json={"title": title, "url": url})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_add_requires_title_and_url(client):
    assert client.post("/api/favorites", json={"title": "x"}).status_code == 400


def test_search_returns_matching_favorites(client):
    _add(client, "Pillars of Creation")
    _add(client, "Andromeda Galaxy")
    results = client.get("/api/favorites/search?q=Pillars").get_json()
    assert [r["title"] for r in results] == ["Pillars of Creation"]


def test_search_no_match_returns_empty(client):
    _add(client, "Andromeda Galaxy")
    assert client.get("/api/favorites/search?q=Nebula").get_json() == []


def test_thumbnail_is_png_and_resized(client):
    fav_id = _add(client, "Big image")
    fake = mock.Mock(content=_png_bytes(), raise_for_status=lambda: None)
    with mock.patch("favorites.requests.get", return_value=fake):
        resp = client.get(f"/api/favorites/{fav_id}/thumbnail")
    assert resp.status_code == 200
    assert resp.mimetype == "image/png"
    thumb = Image.open(io.BytesIO(resp.data))
    assert max(thumb.size) <= 256


def test_thumbnail_rejects_non_nasa_host(client):
    fav_id = _add(client, "Elsewhere", url="https://example.com/cat.png")
    assert client.get(f"/api/favorites/{fav_id}/thumbnail").status_code == 400


def test_thumbnail_unknown_id_404(client):
    assert client.get("/api/favorites/9999/thumbnail").status_code == 404
