import os
import requests
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from datetime import datetime, date

from src.astrology import chart as astrology_chart
from src.astrology import storage as astrology_storage

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
        resp = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Also grab who's on the ISS
        crew_resp = requests.get("http://api.open-notify.org/astros.json", timeout=10)
        crew = crew_resp.json() if crew_resp.ok else {}
        return jsonify({**data, "crew": crew.get("people", [])})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 502


# Astrology – natal chart calculation + optional save-for-later
@app.route("/api/astrology/chart", methods=["POST"])
def astrology_calculate():
    data = request.get_json(silent=True) or {}

    chart_type = "in_depth" if data.get("chart_type") == "in_depth" else "basic"
    required = ["birth_date", "birth_time", "latitude", "longitude", "utc_offset"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    if chart_type == "in_depth" and not data.get("email"):
        return jsonify({"error": "An email is required for an in-depth chart."}), 400

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        utc_offset = float(data["utc_offset"])
        result = astrology_chart.calculate_chart(
            data["birth_date"], data["birth_time"], latitude, longitude, utc_offset, chart_type
        )
    except (ValueError, KeyError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    nickname = data.get("nickname")
    if nickname:
        try:
            astrology_storage.save_record({
                "nickname": nickname,
                "birth_date": data["birth_date"],
                "birth_time": data["birth_time"],
                "latitude": latitude,
                "longitude": longitude,
                "utc_offset": utc_offset,
                "location_label": data.get("location_label", ""),
                "chart_type": chart_type,
                "email": data.get("email", "") if chart_type == "in_depth" else "",
            })
        except astrology_storage.InvalidNickname as e:
            return jsonify({"error": str(e)}), 400

    return jsonify(result)


# Astrology – load a previously saved nickname's chart
@app.route("/api/astrology/saved/<nickname>")
def astrology_saved(nickname):
    try:
        record = astrology_storage.load_record(nickname)
    except astrology_storage.InvalidNickname as e:
        return jsonify({"error": str(e)}), 400

    if not record:
        return jsonify({"error": "No saved chart for that nickname."}), 404

    try:
        result = astrology_chart.calculate_chart(
            record["birth_date"], record["birth_time"],
            float(record["latitude"]), float(record["longitude"]), float(record["utc_offset"]),
            record.get("chart_type", "basic"),
        )
    except (ValueError, KeyError) as e:
        return jsonify({"error": f"Saved record is corrupt: {e}"}), 500

    result["nickname"] = record["nickname"]
    result["location_label"] = record.get("location_label", "")
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
