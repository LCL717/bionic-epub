"""Rules for selecting the bold prefix of an English word."""

from __future__ import annotations

import re
from dataclasses import dataclass

WORD_RE = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
SKIP_RE = re.compile(r"^(?:https?://|www\.|mailto:|[^@\s]+@[^@\s]+\.)", re.IGNORECASE)


@dataclass(frozen=True)
class Strength:
    name: str
    long_word_ratio: float


STRENGTHS = {
    "light": Strength("light", 0.35),
    "standard": Strength("standard", 0.45),
    "strong": Strength("strong", 0.55),
}


def prefix_length(word: str, strength: str = "standard", ratio: float | None = None) -> int:
    """Return how many leading alphabetic characters should be bold."""
    if not word or not word.isascii() or not any(char.isalpha() for char in word):
        return 0

    letters = sum(char.isalpha() for char in word)
    if letters <= 3:
        return letters
    if letters <= 5:
        return 2
    if letters <= 7:
        return 3

    if ratio is None:
        try:
            ratio = STRENGTHS[strength].long_word_ratio
        except KeyError as error:
            raise ValueError(f"Unknown strength: {strength}") from error

    if not 0 < ratio <= 1:
        raise ValueError("ratio must be greater than 0 and at most 1")
    return max(1, min(letters, round(letters * ratio)))


def should_skip(word: str) -> bool:
    """Return whether a token should remain unchanged."""
    return bool(SKIP_RE.match(word)) or word.isdigit()


def bold_prefix(word: str, strength: str = "standard", ratio: float | None = None) -> tuple[str, int]:
    """Split a word into bold prefix HTML and remaining text."""
    if should_skip(word):
        return word, 0

    length = prefix_length(word, strength, ratio)
    if not length:
        return word, 0

    # The tokenizer only matches ASCII words, so punctuation can stay in place.
    prefix = word[:length]
    return f"<strong>{prefix}</strong>{word[length:]}", 1
