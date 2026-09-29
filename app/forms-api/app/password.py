"""What a new password must satisfy. forms-web/src/lib/password.ts shows the
same rules as a live checklist; this is the copy that is enforced."""

import re

MIN_CHARS = 10
MAX_CHARS = 256
REQUIRED_CLASSES = 3

COMMON = frozenset({
    "123456", "1234567", "12345678", "123456789", "1234567890", "12345",
    "password", "passwd", "pass", "letmein", "welcome", "admin", "administrator",
    "qwerty", "qwertyuiop", "asdfgh", "asdfghjkl", "zxcvbn", "zxcvbnm", "qazwsx",
    "iloveyou", "princess", "sunshine", "monkey", "dragon", "football",
    "baseball", "superman", "batman", "starwars", "pokemon", "trustno",
    "abc123", "abcd1234", "a1b2c3d4", "test", "testing", "temp", "changeme",
    "secret", "master", "shadow", "michael", "jordan", "hunter", "freedom",
    "whatever", "computer", "internet", "samsung", "google", "facebook",
    "login", "root", "toor", "guest", "user", "default", "system",
    "roofing", "roofer", "amkroofing", "amk",
})

_LEET = str.maketrans({
    "@": "a", "4": "a", "8": "b", "(": "c", "3": "e", "6": "g", "1": "i",
    "!": "i", "|": "i", "0": "o", "5": "s", "$": "s", "7": "t", "+": "t",
    "2": "z", "9": "g",
})


def _is_common(password: str) -> bool:
    lowered = password.lower()
    folded = lowered.translate(_LEET)
    for candidate in {lowered, folded, re.sub(r"[^a-z]", "", lowered), re.sub(r"[^a-z]", "", folded)}:
        if not candidate:
            continue
        if candidate in COMMON:
            return True
        if any(len(c) >= 6 and candidate.startswith(c) and len(candidate) - len(c) <= 4 for c in COMMON):
            return True
    return False


def _identity(email: str, name: str) -> list[str]:
    local, _, domain = email.lower().partition("@")
    sources = [local, domain.split(".")[0], name.lower()]
    return [chunk for source in sources for chunk in re.split(r"[^a-z0-9]+", source) if len(chunk) >= 4]


def _has_run(password: str) -> bool:
    lowered = password.lower()
    repeat = ascending = descending = 1
    for previous, current in zip(map(ord, lowered), map(ord, lowered[1:])):
        repeat = repeat + 1 if current == previous else 1
        ascending = ascending + 1 if current == previous + 1 else 1
        descending = descending + 1 if current == previous - 1 else 1
        if max(repeat, ascending, descending) >= 4:
            return True
    return False


def problem(password: str, *, email: str = "", name: str = "") -> str | None:
    """The first rule the password breaks, as a sentence for the user, or None."""
    if len(password) > MAX_CHARS:
        return f"Keep your password under {MAX_CHARS} characters."
    if len(password) < MIN_CHARS:
        return f"Use at least {MIN_CHARS} characters."
    classes = sum(bool(re.search(p, password)) for p in (r"[a-z]", r"[A-Z]", r"[0-9]", r"[^A-Za-z0-9]"))
    if classes < REQUIRED_CLASSES:
        return f"Mix at least {REQUIRED_CLASSES} of: lowercase, uppercase, number, symbol."
    if _is_common(password):
        return "That password shows up in breach lists. Pick something else."
    if any(fragment in password.lower() for fragment in _identity(email, name)):
        return "Leave your name and email out of your password."
    if _has_run(password):
        return 'Avoid repeated or sequential runs like "aaaa" or "1234".'
    return None
