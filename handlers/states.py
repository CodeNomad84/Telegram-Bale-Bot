"""State machine constants and small helpers shared by the handlers."""

import re

STATE_NEW = "new"
STATE_AWAIT_JOIN = "await_join"
STATE_AWAIT_USERNAME = "await_username"
STATE_AWAIT_PHONE = "await_phone"
STATE_INTRO = "intro"
STATE_QUIZ = "quiz"
STATE_DONE = "done"

# @ + 3..32 chars, so the shortest accepted value is 4 characters long.
USERNAME_PATTERN = re.compile(r"^@[A-Za-z0-9_]{3,32}$")

DEFAULT_ADDRESS = "دوست خوبم"


def normalize_username(text):
    """Normalize user input to "@username", or return None if it is invalid."""
    candidate = (text or "").strip().replace("\u200c", "")
    if candidate and not candidate.startswith("@"):
        candidate = "@" + candidate
    return candidate if USERNAME_PATTERN.match(candidate) else None


def build_display_name(author):
    """Build a display name from Bale author data, tolerating missing fields."""
    parts = [
        str(getattr(author, "first_name", "") or "").strip(),
        str(getattr(author, "last_name", "") or "").strip(),
    ]
    name = " ".join(part for part in parts if part)
    if name:
        return name
    username = str(getattr(author, "username", "") or "").strip()
    return f"@{username}" if username else ""


def address_of(user):
    """Name used in the welcome message: username, then display name, then fallback."""
    if not user:
        return DEFAULT_ADDRESS
    return user.get("username") or user.get("display_name") or DEFAULT_ADDRESS