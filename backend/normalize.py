"""
Text normalisation for scam detection
=====================================

Scammers evade keyword filters with obfuscation: leetspeak ("d1g1t4l arr3st"),
spaced-out words ("t r a n s f e r"), unicode homoglyphs (Cyrillic "а" for "a"),
and zero-width characters. A pure regex engine misses all of these. This layer
canonicalises the text FIRST, so the explainable signal model sees the real
message — a concrete "beyond literal regex" NLP step, fully offline and testable.
"""

from __future__ import annotations

import re
import unicodedata

# Common homoglyph → ASCII map (Cyrillic/Greek look-alikes + fullwidth).
_HOMOGLYPH = {
    "а": "a", "е": "e", "о": "o", "с": "c", "р": "p", "х": "x", "у": "y",
    "ѕ": "s", "і": "i", "ј": "j", "к": "k", "н": "h", "м": "m", "т": "t",
    "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "α": "a", "ι": "i",
}
# Leetspeak digits → letters (applied only inside alphabetic runs).
_LEET = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def _deleet_word(w: str) -> str:
    """De-leet a token only if it's a mixed letter+digit run (so real numbers
    like account balances or '500' are left intact)."""
    if any(c.isalpha() for c in w) and any(c in _LEET for c in w):
        return "".join(_LEET.get(c, c) for c in w)
    return w


def normalize(text: str) -> str:
    if not text:
        return ""
    # remove zero-width / control chars
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t ")
    text = "".join(_HOMOGLYPH.get(ch, ch) for ch in text)
    text = _strip_accents(text)
    # collapse "s p a c e d   o u t" letters into words: single letters sep by spaces
    text = re.sub(r"\b(?:[A-Za-z]\s){2,}[A-Za-z]\b",
                  lambda m: m.group(0).replace(" ", ""), text)
    # de-leet token by token
    text = " ".join(_deleet_word(t) for t in text.split(" "))
    # squeeze repeated chars ("arrrrest" -> "arrest") and whitespace
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text
