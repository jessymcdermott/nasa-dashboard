"""Templated plain-language readouts for chart placements.

Composes short, original interpretive sentences from small reference tables
(planet meaning x sign trait x house theme x aspect meaning) rather than
hand-written text per combination — keeps the content original and the
reference tables easy to extend.
"""

PLANET_MEANING = {
    "Sun": "core identity and sense of self",
    "Moon": "emotional instincts and inner needs",
    "Mercury": "thinking style and communication",
    "Venus": "approach to love, beauty, and values",
    "Mars": "drive, ambition, and how you assert yourself",
    "Jupiter": "growth, optimism, and where you seek expansion",
    "Saturn": "discipline, boundaries, and long-term responsibility",
    "Uranus": "need for independence and sudden change",
    "Neptune": "imagination, intuition, and idealism",
    "Pluto": "capacity for transformation and deep change",
    "North Node": "direction of growth this lifetime",
}

SIGN_TRAIT = {
    "Aries": "bold, direct, and quick to act",
    "Taurus": "steady, grounded, and slow to change course",
    "Gemini": "curious, adaptable, and quick-thinking",
    "Cancer": "nurturing, protective, and emotionally attuned",
    "Leo": "warm, expressive, and drawn to recognition",
    "Virgo": "precise, analytical, and detail-oriented",
    "Libra": "diplomatic, harmony-seeking, and relationship-focused",
    "Scorpio": "intense, private, and drawn to what's beneath the surface",
    "Sagittarius": "adventurous, philosophical, and freedom-loving",
    "Capricorn": "disciplined, ambitious, and patient",
    "Aquarius": "independent, inventive, and community-minded",
    "Pisces": "dreamy, compassionate, and imaginative",
}

HOUSE_THEME = {
    1: "self-image and first impressions",
    2: "money, possessions, and personal values",
    3: "communication, siblings, and everyday learning",
    4: "home, family, and roots",
    5: "romance, creativity, and self-expression",
    6: "daily routine, work, and health",
    7: "partnerships and one-on-one relationships",
    8: "shared resources and deep transformation",
    9: "travel, higher learning, and belief systems",
    10: "career and public reputation",
    11: "friendships and community",
    12: "the subconscious and private inner life",
}

ASPECT_MEANING = {
    "Conjunction": "blend together and intensify each other",
    "Sextile": "offer each other easy, low-friction opportunity",
    "Square": "create productive tension that pushes growth",
    "Trine": "flow together with natural ease",
    "Opposition": "pull in opposite directions, seeking balance",
}


def planet_interpretation(planet, sign, house=None):
    meaning = PLANET_MEANING.get(planet, "influence")
    trait = SIGN_TRAIT.get(sign, "distinctive")
    text = f"Your {meaning} tends to come out {trait}."
    if house is not None:
        theme = HOUSE_THEME.get(house, "this area of life")
        text += f" This mainly plays out through {theme}."
    return text


def aspect_interpretation(planet_a, planet_b, aspect):
    meaning = ASPECT_MEANING.get(aspect, "interact with")
    a_theme = PLANET_MEANING.get(planet_a, planet_a)
    b_theme = PLANET_MEANING.get(planet_b, planet_b)
    return f"Your {a_theme} and {b_theme} {meaning}."
