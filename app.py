import os
import random
import requests
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()

app = Flask(__name__)
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
NASA_BASE = "https://api.nasa.gov"

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# APOD – Astronomy Picture of the Day
@app.route("/api/apod")
def apod():
    query_date = request.args.get("date", date.today().isoformat())
    try:
        resp = requests.get(
            f"{NASA_BASE}/planetary/apod",
            params={"api_key": NASA_API_KEY, "date": query_date},
            timeout=10,
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


# Random NASA Photo – pulls from NASA's public Image and Video Library
# (images-api.nasa.gov, no API key needed) since it has no native "random"
# endpoint of its own: pick a broad topic, search it, return one random hit
RANDOM_PHOTO_TOPICS = [
    "nebula", "galaxy", "saturn", "jupiter", "mars surface", "earth from space",
    "astronaut spacewalk", "aurora", "supernova", "black hole", "milky way",
    "hubble deep field", "solar eclipse", "moon surface", "comet",
]


@app.route("/api/random-photo")
def random_photo():
    query = random.choice(RANDOM_PHOTO_TOPICS)
    try:
        resp = requests.get(
            "https://images-api.nasa.gov/search",
            params={"q": query, "media_type": "image"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("collection", {}).get("items", [])
        if not items:
            return jsonify({"error": f"No results for '{query}', try again."}), 502

        item = random.choice(items)
        meta = (item.get("data") or [{}])[0]
        links = item.get("links") or []
        thumbnail = links[0].get("href") if links else None

        return jsonify({
            "title": meta.get("title", ""),
            "description": meta.get("description", ""),
            "date_created": meta.get("date_created", ""),
            "center": meta.get("center", ""),
            "keywords": meta.get("keywords", []),
            "thumbnail": thumbnail,
            "nasa_id": meta.get("nasa_id", ""),
            "topic": query,
        })
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Unexpected response shape from NASA's image library: {e}"}), 502


# Mars Rover Photos – latest raw images straight from NASA's own mission feed
# (api.nasa.gov/mars-photos is a community-run mirror that's been unreliable for
# years and never added Perseverance; mars.nasa.gov/rss/api is what NASA's own
# raw-image galleries use, stays current, needs no API key, and covers both
# active rovers)
MARS_ROVER_CATEGORIES = {"curiosity": "msl", "perseverance": "mars2020"}


def _extract_mars_photo(image):
    files = image.get("image_files") or {}
    img_src = files.get("medium") or files.get("large") or files.get("full_res") or files.get("small")
    camera = image.get("camera") or {}
    return {
        "img_src": img_src,
        "sol": image.get("sol"),
        "date_taken": image.get("date_taken"),
        "camera": {
            "name": camera.get("instrument") or camera.get("camera_type") or "Unknown",
            "full_name": camera.get("camera_type") or camera.get("instrument") or "",
        },
        "caption": image.get("caption") or image.get("title") or "",
    }


@app.route("/api/mars")
def mars():
    rover = request.args.get("rover", "curiosity")
    page = request.args.get("page", "0")
    category = MARS_ROVER_CATEGORIES.get(rover)
    if not category:
        return jsonify({"error": f"Unknown rover '{rover}'. Choose curiosity or perseverance."}), 400

    images = []
    try:
        resp = requests.get(
            "https://mars.nasa.gov/rss/api/",
            params={
                "feed": "raw_images",
                "category": category,
                "feedtype": "json",
                "num": 12,
                "page": page,
                "order": "sol desc",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        images = data.get("images", [])
        photos = [_extract_mars_photo(img) for img in images]
        return jsonify({
            "rover": rover,
            "page": int(page),
            "photos": photos,
            "total": data.get("total_results", len(photos)),
        })
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502
    except (KeyError, TypeError, ValueError) as e:
        sample_keys = list(images[0].keys()) if images else []
        return jsonify({
            "error": f"Unexpected response shape from NASA's raw image feed: {e}",
            "sample_keys": sample_keys,
        }), 502


# Near Earth Objects – asteroids for today
@app.route("/api/neo")
def neo():
    today = date.today().isoformat()
    try:
        resp = requests.get(
            f"{NASA_BASE}/neo/rest/v1/feed",
            params={"api_key": NASA_API_KEY, "start_date": today, "end_date": today},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        objects = data.get("near_earth_objects", {}).get(today, [])
        # Sort by closest approach distance
        objects.sort(
            key=lambda x: float(
                x["close_approach_data"][0]["miss_distance"]["kilometers"]
            )
        )
        return jsonify({"date": today, "count": len(objects), "objects": objects[:10]})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


# ISS Current Location
@app.route("/api/iss")
def iss():
    try:
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Also grab who's on the ISS
        crew_resp = requests.get("http://api.open-notify.org/astros.json", timeout=10)
        crew = crew_resp.json() if crew_resp.ok else {}
        return jsonify({**data, "crew": crew.get("people", [])})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(debug=True)
