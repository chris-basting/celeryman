"""Turn whatever Paul types into a command."""

from __future__ import annotations

import re
from dataclasses import dataclass

WORD_NUMBERS = {
    "a couple": 2, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "a dozen": 12, "dozen": 12,
}
MAX_COPIES = 12

CHARACTER_WORDS = [
    ("tayne", "tayne"),
    ("oyster", "oyster"),
    ("celery", "celery_man"),
    ("cinco", "cinco_id"),
]


@dataclass
class Command:
    name: str
    character: str | None = None
    count: int | None = None


# Checked in order; first match wins.
RULES: list[tuple[str, str]] = [
    (r"^(y|yes|yeah|yep|sure|confirm|do it|affirmative)$", "yes"),
    (r"^(n|no|nope|cancel|never ?mind)$", "no"),
    (r"\b(quit|exit|bye|goodbye|shut ?down)\b", "quit"),
    (r"\bhelp\b|^commands$", "help"),
    (r"^(clear|cls)$", "clear"),
    (r"\b(reset|reboot|restart)\b", "reset"),
    (r"\bnude\b", "nude"),
    (r"\bhold\b", "hold"),
    (r"\b(answer|pick up|accept|take (the|her|it))\b", "answer"),
    (r"\b(error|crash|overload|improper)\b", "overload"),
    (r"\b(disengage|calm down|turn off)\b", "disengage"),
    (r"4d3|kick (it )?up", "engage"),
    (r"\bprint", "print"),
    (r"wobble", "wobble"),
    (r"fl[ae]r", "flarhgunnstow"),
    (r"side ?by ?side|\btile\b", "tile"),
    (r"\b(duplicate|stack|cascade|copies|copy|more)\b", "cascade"),
    (r"\b(\d+|" + "|".join(WORD_NUMBERS) + r") (taynes?|oysters?|celery m[ae]n|cinco)", "cascade"),
    (r"new sequence|anything new|\bbeta\b|what else", "beta"),
    (r"oyster", "oyster"),
    (r"celery", "celery_man"),
    (r"cinco", "cinco_id"),
    (r"tayne", "tayne"),
    (r"\b(hello|hi|hey|good morning|morning)\b", "greet"),
    (r"coffee", "coffee"),
]


def normalize(text: str) -> str:
    text = re.sub(r"[^\w\s]", " ", text.lower())
    text = re.sub(r"^computer\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def find_count(text: str) -> int | None:
    match = re.search(r"\b(\d+)\b", text)
    if match:
        return max(1, min(MAX_COPIES, int(match.group(1))))
    for word, value in WORD_NUMBERS.items():
        if re.search(rf"\b{word}\b", text):
            return value
    return None


def find_character(text: str) -> str | None:
    for word, key in CHARACTER_WORDS:
        if word in text:
            return key
    return None


def parse(raw: str) -> Command:
    if raw.strip() == "?":
        return Command("help")
    text = normalize(raw)
    for pattern, name in RULES:
        if re.search(pattern, text):
            return Command(name, find_character(text), find_count(text))
    return Command("unknown")
