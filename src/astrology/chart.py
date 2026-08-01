"""Natal chart calculations using the Swiss Ephemeris (Moshier analytical model).

Moshier mode (swe.FLG_MOSEPH) is used deliberately: it needs no downloaded
ephemeris data files, works fully offline, and is accurate to a few
arc-seconds for planets — plenty for astrology purposes.
"""
import swisseph as swe

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


def _julian_day_ut(birth_date, birth_time, utc_offset):
    year, month, day = (int(p) for p in birth_date.split("-"))
    hour, minute = (int(p) for p in birth_time.split(":"))
    local_hours = hour + minute / 60
    ut_hours = local_hours - utc_offset
    return swe.julday(year, month, day, ut_hours)


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


def calculate_aspects(planets):
    aspects = []
    names = list(planets.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            angle = _angle_between(planets[a]["longitude"], planets[b]["longitude"])
            for aspect_name, target_angle, orb in ASPECTS:
                delta = abs(angle - target_angle)
                if delta <= orb:
                    aspects.append({
                        "planet_a": a,
                        "planet_b": b,
                        "aspect": aspect_name,
                        "angle": round(angle, 2),
                        "orb": round(delta, 2),
                    })
                    break
    return aspects


def calculate_chart(birth_date, birth_time, latitude, longitude, utc_offset, chart_type="basic"):
    """Returns a dict describing the natal chart.

    chart_type "basic" returns just Sun/Moon/Rising.
    chart_type "in_depth" returns full planets, houses, and aspects.
    """
    jd_ut = _julian_day_ut(birth_date, birth_time, utc_offset)
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

    return {
        "chart_type": "in_depth",
        "planets": planets,
        "houses": house_data,
        "aspects": calculate_aspects(planets),
    }
