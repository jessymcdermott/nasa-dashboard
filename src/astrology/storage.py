"""Persists astrology chart requests to per-nickname .txt files.

No real names are collected — only a user-chosen nickname — and email is
only stored when the user opts into an in-depth chart. Nicknames are
restricted to a safe character set so they can be used directly as
filenames without any path-traversal risk.
"""
import re
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "astrology"
NICKNAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

FIELDS = [
    "nickname", "saved_at", "birth_date", "birth_time",
    "latitude", "longitude", "utc_offset", "location_label",
    "chart_type", "email",
]


class InvalidNickname(ValueError):
    pass


def _validate_nickname(nickname):
    if not nickname or not NICKNAME_RE.match(nickname):
        raise InvalidNickname(
            "Nickname must be 1-32 characters, letters/numbers/underscore/hyphen only."
        )
    return nickname


def _record_path(nickname):
    return DATA_DIR / f"{_validate_nickname(nickname)}.txt"


def save_record(record):
    """record: dict with keys matching FIELDS (missing keys stored blank)."""
    _validate_nickname(record["nickname"])
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    record = {**record, "saved_at": datetime.now(timezone.utc).isoformat()}
    lines = [f"{key}: {record.get(key, '') or ''}" for key in FIELDS]
    _record_path(record["nickname"]).write_text("\n".join(lines) + "\n")


def load_record(nickname):
    path = _record_path(nickname)
    if not path.exists():
        return None
    record = {}
    for line in path.read_text().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        record[key.strip()] = value.strip()
    return record
