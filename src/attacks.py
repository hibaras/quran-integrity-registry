"""Tampering operators. Each operator takes (edition, rng) and returns
(tampered_edition, ground_truth) or None when the sampled verse is unsuitable.
ground_truth = {"ids": set of (c, v) reference ids affected, "cls": expected class}.
Tampered copies live in memory only."""
from __future__ import annotations

import unicodedata as ud

from qintegrity import canon

LETTERS = [chr(c) for c in (0x0627, 0x0628, 0x062A, 0x062B, 0x062C, 0x062D, 0x062E, 0x062F, 0x0630, 0x0631,
                            0x0632, 0x0633, 0x0634, 0x0635, 0x0636, 0x0637, 0x0638, 0x0639, 0x063A, 0x0641,
                            0x0642, 0x0643, 0x0644, 0x0645, 0x0646, 0x0647, 0x0648, 0x064A)]
LETTER_SET = set(LETTERS) | {chr(c) for c in range(0x0621, 0x063B)} | {chr(c) for c in range(0x0641, 0x064B)} | {"ٱ"}
VOWELS = ["َ", "ُ", "ِ"]                  # fatha, damma, kasra
HARAKAT = {chr(c) for c in range(0x064B, 0x0653)}         # tanween .. sukun
INVISIBLES = ["​", "‌", "‍", "⁠", "﻿"]
BIDI = ["‮", "⁧", "‏", "؜"]
HOMO = {"ي": "ی", "ك": "ک"}           # yeh -> farsi yeh, kaf -> keheh


def _copy(ed):
    return list(ed)


def _pick(ed, rng):
    """Pick a numbered verse (verse 0, the split-off basmala, is never targeted)."""
    while True:
        i = rng.randrange(len(ed))
        if ed[i][1] >= 1:
            return i, ed[i]


def _replace(ed, i, new_text):
    out = _copy(ed)
    c, v, _ = out[i]
    out[i] = (c, v, new_text)
    return out


def _single(ed, i, new_text, cls):
    if canon(new_text) == canon(ed[i][2]):
        return None
    return _replace(ed, i, new_text), {"ids": {(ed[i][0], ed[i][1])}, "cls": cls}


def joins_next(t, k):
    """True if the letter at k is followed (after combining marks) by an Arabic letter,
    i.e. it is rendered in an initial/medial (connected) form."""
    j = k + 1
    while j < len(t) and ud.category(t[j]) == "Mn":
        j += 1
    return j < len(t) and t[j] in LETTER_SET


# ---- in-verse, letter level
def letter_sub(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    pos = [k for k, ch in enumerate(t) if ch in LETTER_SET]
    k = rng.choice(pos)
    new = rng.choice([x for x in LETTERS if x != t[k]])
    return _single(ed, i, t[:k] + new + t[k + 1:], "L")


def letter_del(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    k = rng.choice([k for k, ch in enumerate(t) if ch in LETTER_SET])
    return _single(ed, i, t[:k] + t[k + 1:], "L")


def letter_ins(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    k = rng.randrange(len(t) + 1)
    return _single(ed, i, t[:k] + rng.choice(LETTERS) + t[k:], "L")


def word_del(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    w = t.split(" ")
    if len(w) < 2:
        return None
    del w[rng.randrange(len(w))]
    return _single(ed, i, " ".join(w), "L")


def word_swap(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    w = t.split(" ")
    cand = [k for k in range(len(w) - 1) if w[k] != w[k + 1]]
    if not cand:
        return None
    k = rng.choice(cand)
    w[k], w[k + 1] = w[k + 1], w[k]
    return _single(ed, i, " ".join(w), "L")


# ---- in-verse, diacritic level
def vowel_sub(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    pos = [k for k, ch in enumerate(t) if ch in VOWELS]
    if not pos:
        return None
    k = rng.choice(pos)
    return _single(ed, i, t[:k] + rng.choice([x for x in VOWELS if x != t[k]]) + t[k + 1:], "D")


def harakah_del(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    pos = [k for k, ch in enumerate(t) if ch in HARAKAT]
    if not pos:
        return None
    k = rng.choice(pos)
    return _single(ed, i, t[:k] + t[k + 1:], "D")


def harakah_ins(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    pos = [k for k, ch in enumerate(t) if ch in LETTER_SET]
    k = rng.choice(pos)
    return _single(ed, i, t[:k + 1] + rng.choice(["ّ", "ْ", "َ", "ُ", "ِ"]) + t[k + 1:], "D")


# ---- in-verse, Unicode level (visually identical or invisible)
def homoglyph(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    pos = [k for k, ch in enumerate(t) if ch in HOMO and joins_next(t, k)]
    if not pos:
        return None
    k = rng.choice(pos)
    return _single(ed, i, t[:k] + HOMO[t[k]] + t[k + 1:], "U")


def invisible(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    k = rng.randrange(1, len(t))
    return _single(ed, i, t[:k] + rng.choice(INVISIBLES) + t[k:], "U")


def bidi(ed, rng):
    i, (_, _, t) = _pick(ed, rng)
    k = rng.randrange(0, len(t))
    return _single(ed, i, t[:k] + rng.choice(BIDI) + t[k:], "U")


# ---- structural (verse level); chapters are renumbered as a careless/malicious copy would be
def _chapter_bounds(ed, c):
    idx = [k for k, (cc, _, _) in enumerate(ed) if cc == c]
    return idx[0], idx[-1] + 1


def verse_del(ed, rng):
    i, (c, v, t) = _pick(ed, rng)
    lo, hi = _chapter_bounds(ed, c)
    if hi - lo < 2:
        return None
    out = ed[:i] + [(cc, vv - 1, tt) for (cc, vv, tt) in ed[i + 1:hi]] + ed[hi:]
    return out, {"ids": {(c, v)}, "cls": "S-del"}


def verse_ins(ed, rng):
    i, (c, v, t) = _pick(ed, rng)
    lo, hi = _chapter_bounds(ed, c)
    j, _ = _pick(ed, rng)                            # duplicate some existing verse text
    fake = ed[j][2]
    out = ed[:i] + [(c, v, fake)] + [(cc, vv + 1, tt) for (cc, vv, tt) in ed[i:hi]] + ed[hi:]
    return out, {"ids": {(c, v)}, "cls": "S-ins"}


def verse_swap(ed, rng):
    i, (c, v, t) = _pick(ed, rng)
    lo, hi = _chapter_bounds(ed, c)
    others = [k for k in range(lo, hi) if ed[k][1] >= 1 and canon(ed[k][2]) != canon(t)]
    if not others:
        return None
    j = rng.choice(others)
    out = _copy(ed)
    out[i] = (c, v, ed[j][2])
    out[j] = (ed[j][0], ed[j][1], t)
    return out, {"ids": {(c, v), (ed[j][0], ed[j][1])}, "cls": "S-reloc"}


OPERATORS = {
    "Letter substitution": letter_sub, "Letter deletion": letter_del, "Letter insertion": letter_ins,
    "Word deletion": word_del, "Adjacent-word swap": word_swap,
    "Vowel substitution": vowel_sub, "Diacritic deletion": harakah_del, "Diacritic insertion": harakah_ins,
    "Homoglyph substitution": homoglyph, "Invisible-character insertion": invisible, "Bidi-control insertion": bidi,
    "Verse deletion": verse_del, "Verse insertion (duplicate)": verse_ins, "Verse swap (within chapter)": verse_swap,
}
FAMILY = {k: ("Letter/word" if k in ("Letter substitution", "Letter deletion", "Letter insertion", "Word deletion", "Adjacent-word swap")
              else "Diacritic" if k in ("Vowel substitution", "Diacritic deletion", "Diacritic insertion")
              else "Unicode" if k in ("Homoglyph substitution", "Invisible-character insertion", "Bidi-control insertion")
              else "Structural") for k in OPERATORS}
