import os
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


# Mars Rover Photos – latest from Curiosity
@app.route("/api/mars")
def mars():
    sol = request.args.get("sol", "1000")
    try:
        resp = requests.get(
            f"{NASA_BASE}/mars-photos/api/v1/rovers/curiosity/photos",
            params={"api_key": NASA_API_KEY, "sol": sol, "page": 1},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # Return just the first 12 photos to keep payload light
        photos = data.get("photos", [])[:12]
        return jsonify({"photos": photos, "sol": sol, "total": len(data.get("photos", []))})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


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
        resp = requests.get("https://api.open-notify.org/iss-now.json", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Also grab who's on the ISS
        crew_resp = requests.get("https://api.open-notify.org/astros.json", timeout=10)
        crew = crew_resp.json() if crew_resp.ok else {}
        return jsonify({**data, "crew": crew.get("people", [])})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(debug=True)
