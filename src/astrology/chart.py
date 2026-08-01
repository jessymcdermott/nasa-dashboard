"""Natal chart calculations using the Swiss Ephemeris (Moshier analytical model).

Moshier mode (swe.FLG_MOSEPH) is used deliberately: it needs no downloaded
ephemeris data files, works fully offline, and is accurate to a few
arc-seconds for planets — plenty for astrology purposes.
"""
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe

from . import interpretations

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
    ("North Node", swe.MEAN_NODE),
]

# (name, angle, orb) — classic Ptolemaic aspects
ASPECTS = [
    ("Conjunction", 0, 8),
    ("Sextile", 60, 5),
    ("Square", 90, 7),
    ("Trine", 120, 7),
    ("Opposition", 180, 8),
]

CALC_FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED


def _sign_position(longitude):
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    return {
        "sign": SIGNS[sign_index],
        "degree": round(longitude % 30, 2),
        "longitude": round(longitude, 4),
    }


def _house_of(longitude, cusps):
    longitude = longitude % 360
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if start < end:
            if start <= longitude < end:
                return i + 1
        else:  # house wraps past 0°
            if longitude >= start or longitude < end:
                return i + 1
    return 12


def _angle_between(lon1, lon2):
    diff = abs(lon1 - lon2) % 360
    return 360 - diff if diff > 180 else diff


def _julian_day_ut(birth_date, birth_time, tz_name):
    year, month, day = (int(p) for p in birth_date.split("-"))
    hour, minute = (int(p) for p in birth_time.split(":"))
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Unknown timezone: {tz_name}")
    local_dt = datetime(year, month, day, hour, minute, tzinfo=tz)
    utc_dt = local_dt.astimezone(dt_timezone.utc)
    ut_hours = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hours)


def calculate_planets(jd_ut):
    planets = {}
    for name, code in PLANETS:
        xx, _ret_flags = swe.calc_ut(jd_ut, code, CALC_FLAGS)
        longitude, speed = xx[0], xx[3]
        pos = _sign_position(longitude)
        pos["retrograde"] = speed < 0
        planets[name] = pos
    return planets


def calculate_houses(jd_ut, latitude, longitude):
    cusps, ascmc = swe.houses(jd_ut, latitude, longitude, b"P")
    houses = [_sign_position(c) for c in cusps]
    return {
        "cusps": houses,
        "ascendant": _sign_position(ascmc[0]),
        "midheaven": _sign_position(ascmc[1]),
    }, cusps


def _find_aspects(name_lon_pairs):
    aspects = []
    for (name_a, lon_a), (name_b, lon_b) in name_lon_pairs:
        angle = _angle_between(lon_a, lon_b)
        for aspect_name, target_angle, orb in ASPECTS:
            delta = abs(angle - target_angle)
            if delta <= orb:
                aspects.append({
                    "planet_a": name_a,
                    "planet_b": name_b,
                    "aspect": aspect_name,
                    "angle": round(angle, 2),
                    "orb": round(delta, 2),
                })
                break
    return aspects


def calculate_aspects(planets):
    names = list(planets.keys())
    pairs = [
        ((names[i], planets[names[i]]["longitude"]), (names[j], planets[names[j]]["longitude"]))
        for i in range(len(names)) for j in range(i + 1, len(names))
    ]
    return _find_aspects(pairs)


def calculate_cross_aspects(set_a, set_b):
    """Aspects between two independent planet sets (e.g. transiting vs. natal)."""
    pairs = [
        ((name_a, pos_a["longitude"]), (name_b, pos_b["longitude"]))
        for name_a, pos_a in set_a.items() for name_b, pos_b in set_b.items()
    ]
    return _find_aspects(pairs)


def calculate_chart(birth_date, birth_time, latitude, longitude, tz_name, chart_type="basic"):
    """Returns a dict describing the natal chart.

    chart_type "basic" returns just Sun/Moon/Rising.
    chart_type "in_depth" returns full planets, houses, and aspects.
    """
    jd_ut = _julian_day_ut(birth_date, birth_time, tz_name)
    planets = calculate_planets(jd_ut)
    house_data, cusps = calculate_houses(jd_ut, latitude, longitude)

    if chart_type != "in_depth":
        return {
            "chart_type": "basic",
            "sun": planets["Sun"],
            "moon": planets["Moon"],
            "rising": house_data["ascendant"],
        }

    for name, pos in planets.items():
        pos["house"] = _house_of(pos["longitude"], cusps)
        pos["interpretation"] = interpretations.planet_interpretation(name, pos["sign"], pos["house"])

    aspects = calculate_aspects(planets)
    for a in aspects:
        a["interpretation"] = interpretations.aspect_interpretation(a["planet_a"], a["planet_b"], a["aspect"])

    house_data["ascendant"]["interpretation"] = (
        f"Your Ascendant sets the first impression you give: {interpretations.SIGN_TRAIT.get(house_data['ascendant']['sign'], 'distinctive')}."
    )
    house_data["midheaven"]["interpretation"] = (
        f"Your Midheaven shapes your public path: {interpretations.SIGN_TRAIT.get(house_data['midheaven']['sign'], 'distinctive')}."
    )

    return {
        "chart_type": "in_depth",
        "planets": planets,
        "houses": house_data,
        "aspects": aspects,
    }


def calculate_transits(natal_planets, natal_cusps_longitudes):
    """Current sky positions, their natal house placement, and aspects to the natal planets."""
    now = datetime.now(dt_timezone.utc)
    jd_ut = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60 + now.second / 3600)

    transiting_planets = calculate_planets(jd_ut)
    for name, pos in transiting_planets.items():
        pos["house"] = _house_of(pos["longitude"], natal_cusps_longitudes)

    aspects = calculate_cross_aspects(transiting_planets, natal_planets)
    for a in aspects:
        a["interpretation"] = interpretations.aspect_interpretation(a["planet_a"], a["planet_b"], a["aspect"])

    return {
        "as_of": now.isoformat(),
        "transiting_planets": transiting_planets,
        "aspects_to_natal": aspects,
    }
