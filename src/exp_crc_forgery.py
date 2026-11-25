"""Experiment 4: second-preimage forgery of per-verse CRC-32 with visually neutral edits.

CRC-32 is affine over GF(2) for equal-length inputs, so the substitutions needed to
cancel the CRC change caused by a real content edit are found by Gaussian elimination.
Rules P1-P4 are selected on one font (Noto Naskh Arabic) and then measured on four
held-out fonts, two of them Mushaf fonts (Amiri Quran, KFGQPC Uthmanic Hafs).
Letter edits exclude yeh, kaf and alef maksura, whose positions carry rules P1-P3, so
that an edit never removes a substitution slot. A second construction changes one vowel
in each of N_RENDER random verses and appends 32 invisible characters (U+2062 or
U+2063); it is checked for rendering as well."""
import hashlib
import json
import os
import random
import sys
import zlib
from collections import Counter

import unicodedata as ud

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "src")
from qintegrity import Registry, canon, classify_verse, diagnose, load_edition, profile  # noqa: E402
from attacks import VOWELS, LETTERS, LETTER_SET, joins_next  # noqa: E402

SEED = 7
N_ATTACKS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
N_RENDER = int(sys.argv[2]) if len(sys.argv) > 2 else 200
SELECT_FONT = "Noto Naskh Arabic"
FONTS = {"Noto Naskh Arabic": "fonts/NotoNaskhArabic[wght].ttf", "Amiri": "fonts/Amiri-Regular.ttf",
         "Scheherazade New": "fonts/ScheherazadeNew-Regular.ttf", "Amiri Quran": "fonts/AmiriQuran.ttf",
         "KFGQPC Uthmanic Hafs": "fonts/UthmanicHafs1Ver18.ttf"}

full = load_edition("data/uthmani.json")              # includes verse 0 (basmala headers)
prof = profile(full)
reg = Registry(full)
IDX = [i for i, (_, v, _) in enumerate(full) if v >= 1]
ref = [full[i] for i in IDX]                           # the 6,236 numbered verses


# homoglyph rules: (source char, replacement, required position)
RULES = {"P1": ("\u064A", "\u06CC", "connected"),   # yeh -> farsi yeh (initial/medial form)
         "P2": ("\u0643", "\u06A9", "connected"),   # kaf -> keheh (initial/medial form)
         "P3": ("\u0649", "\u06CC", "final")}       # alef maksura -> farsi yeh (final/isolated form)
ACTIVE = list(RULES)


def repl(text: str, k: int, rules=None):
    for r in (ACTIVE if rules is None else rules):
        if r not in RULES:
            continue
        src, dst, where = RULES[r]
        if text[k] == src and (joins_next(text, k) == (where == "connected")):
            return dst
    return None


USE_REORDER = True
PAIRS = {"single": {}, "compensated": [], "suffix": []}   # kept in memory for the second-engine check


def toggles(text: str, rules=None, reorder=None) -> list[tuple[int, int, str]]:
    """Non-overlapping equal-byte-length, visually neutral edits: (start, length, replacement)."""
    reorder = USE_REORDER if reorder is None else reorder
    out, k = [], 0
    while k < len(text):
        r = repl(text, k, rules)
        if r is not None:
            out.append((k, 1, r)); k += 1; continue
        if reorder and k + 1 < len(text):
            a, b = text[k], text[k + 1]
            if (ud.category(a) == "Mn" and ud.category(b) == "Mn" and a != b
                    and ud.combining(a) and ud.combining(b) and ud.combining(a) != ud.combining(b)
                    and len(a.encode()) == len(b.encode())):
                out.append((k, 2, b + a)); k += 2; continue
        k += 1
    return out


def apply_toggles(text, tg, mask):
    chars = list(text)
    for j, (k, ln, new) in enumerate(tg):
        if mask >> j & 1:
            chars[k:k + ln] = list(new)
    return "".join(chars)


def crc_delta(text: str, tgl) -> int:
    a = text.encode("utf-8")
    b = apply_toggles(text, [tgl], 1).encode("utf-8")
    assert len(a) == len(b)
    d = bytes(x ^ y for x, y in zip(a, b))
    return zlib.crc32(d) ^ zlib.crc32(bytes(len(d)))


def gf2_basis(vectors: list[int]):
    """Return list of (pivot_vector, combination_mask) forming an echelon basis."""
    basis = []
    for idx, v in enumerate(vectors):
        mask = 1 << idx
        for bv, bm in basis:
            if v ^ bv < v:
                v ^= bv
                mask ^= bm
        if v:
            basis.append((v, mask))
            basis.sort(key=lambda x: -x[0])
    return basis


def solve(vectors: list[int], target: int):
    basis = gf2_basis(vectors)
    mask = 0
    for bv, bm in basis:
        if target ^ bv < target:
            target ^= bv
            mask ^= bm
    return (mask if target == 0 else None), len(basis)


def content_edit(text, rng):
    kind = rng.choice(["vowel", "letter"])
    if kind == "vowel":
        pos = [k for k, ch in enumerate(text) if ch in VOWELS]
        k = rng.choice(pos)
        return kind, text[:k] + rng.choice([v for v in VOWELS if v != text[k]]) + text[k + 1:]
    protected = {"\u064A", "\u0643", "\u0649"}
    pos = [k for k, ch in enumerate(text) if ch in LETTER_SET and ch not in protected]
    k = rng.choice(pos)
    return kind, text[:k] + rng.choice([x for x in LETTERS if x != text[k] and x not in protected]) + text[k + 1:]


def render(text, font, width=None):
    if width is None:
        l, t, r, b = font.getbbox(text, direction="rtl", features=["kern", "liga", "calt"])
        width = int(r - l) + 200
    img = Image.new("L", (width, 200), 255)
    ImageDraw.Draw(img).text((width - 50, 30), text, font=font, fill=0, anchor="ra", direction="rtl",
                             features=["kern", "liga", "calt"])
    return np.asarray(img)


def same_render(a, b, font):
    wa = font.getbbox(a, direction="rtl")[2]
    wb = font.getbbox(b, direction="rtl")[2]
    w = int(max(wa, wb)) + 300
    return np.array_equal(render(a, font, w), render(b, font, w))


def visual_pairs(n_per_rule, rng):
    """Single homoglyph substitution rendered with each font: share of pixel-identical renders."""
    out = {}
    fonts = {f: ImageFont.truetype(p, 48, layout_engine=ImageFont.Layout.RAQM) for f, p in FONTS.items()}
    for r in list(RULES) + ["P4"]:
        cases = []
        while len(cases) < n_per_rule:
            _, _, t = ref[rng.randrange(len(ref))]
            tg = toggles(t, rules=[r], reorder=False) if r != "P4" else [x for x in toggles(t, rules=["none"], reorder=True)]
            if tg:
                cases.append((t, apply_toggles(t, [rng.choice(tg)], 1)))
        PAIRS["single"][r] = cases
        out[r] = {f: sum(same_render(a, b, fo) for a, b in cases) / len(cases) for f, fo in fonts.items()}
    return out


def main():
    global ACTIVE
    rng = random.Random(SEED)
    vis_pairs = visual_pairs(N_RENDER, rng)
    print("visual pairs", vis_pairs, flush=True)
    global USE_REORDER
    ACTIVE = [r for r in RULES if vis_pairs[r][SELECT_FONT] == 1.0]
    USE_REORDER = vis_pairs["P4"][SELECT_FONT] == 1.0
    print("active rules", ACTIVE, "reorder", USE_REORDER, flush=True)
    # 1) feasibility over the whole corpus
    ranks, npos = [], []
    ranks_h = []
    for _, _, t in ref:
        p = toggles(t)
        npos.append(len(p))
        ranks.append(len(gf2_basis([crc_delta(t, x) for x in p])) if p else 0)
        ph = toggles(t, reorder=False)
        ranks_h.append(len(gf2_basis([crc_delta(t, x) for x in ph])) if ph else 0)
    ranks = np.array(ranks)
    npos = np.array(npos)
    ranks_h = np.array(ranks_h)
    feas = {"active_rules": ACTIVE, "reorder": USE_REORDER,
            "full_rank_32_homoglyph_only": int((ranks_h == 32).sum()), "verses": len(ref), "full_rank_32": int((ranks == 32).sum()),
            "share_full_rank": float((ranks == 32).mean()),
            "chars_in_full_rank_verses": int(sum(len(t) for (_, _, t), r in zip(ref, ranks) if r == 32)),
            "chars_total": int(sum(len(t) for *_, t in ref)),
            "positions_median": float(np.median(npos)), "positions_mean": float(np.mean(npos)),
            "positions_max": int(npos.max())}
    print(feas, flush=True)

    # 2) attacks: real content edit + homoglyph compensation
    elig = [i for i, r in enumerate(ranks) if r == 32]
    att = Counter()
    n_swaps, samples = [], []
    for _ in range(N_ATTACKS):
        i = rng.choice(elig)
        c, v, t = ref[i]
        kind, edited = content_edit(t, rng)
        if canon(edited) == canon(t):
            continue
        pos = toggles(edited)
        vecs = [crc_delta(edited, x) for x in pos]
        target = zlib.crc32(edited.encode()) ^ zlib.crc32(t.encode())
        mask, _ = solve(vecs, target)
        att["attempts"] += 1
        att[f"attempts_{kind}"] += 1
        if mask is None:
            continue
        forged = apply_toggles(edited, pos, mask)
        crc_ok = zlib.crc32(forged.encode()) == zlib.crc32(t.encode())
        att["crc_collision"] += crc_ok
        att["sha256_detects"] += hashlib.sha256(forged.encode()).digest() != hashlib.sha256(t.encode()).digest()
        cand = list(full)
        cand[IDX[i]] = (c, v, forged)
        res = diagnose(reg, cand, prof)
        att["proposed_detects"] += bool(res["findings"])
        cls = res["findings"][0][2] if res["findings"] else "none"
        att[f"class_{kind}_{cls}"] += 1
        n_swaps.append(bin(mask).count("1"))
        samples.append((t, edited, forged))
    # 3) visual check: does the compensation leave any pixel trace?
    vis = {}
    sub = random.Random(SEED + 1).sample(samples, min(N_RENDER, len(samples)))
    for fname, path in FONTS.items():
        font = ImageFont.truetype(path, 48, layout_engine=ImageFont.Layout.RAQM)
        same = sum(same_render(e, f, font) for _, e, f in sub)
        vis[fname] = {"rendered": len(sub), "pixel_identical": int(same)}
    PAIRS["compensated"] = [[e, f] for _, e, f in sub]
    # 4) invisible-suffix construction: edit any verse, append 32 characters U+2062/U+2063
    sfx = Counter()
    sfx_vis = Counter()
    fonts = {f: ImageFont.truetype(p, 48, layout_engine=ImageFont.Layout.RAQM) for f, p in FONTS.items()}
    rng2 = random.Random(SEED + 2)
    while sfx["attempts"] < N_RENDER:                 # N_RENDER vowelled verses, one vowel edit each
        i = rng2.randrange(len(ref))
        c, v, t = ref[i]
        pos = [k for k, ch in enumerate(t) if ch in VOWELS]
        if not pos:
            sfx["skipped_no_vowel"] += 1
            continue
        k = rng2.choice(pos)
        edited = t[:k] + rng2.choice([x for x in VOWELS if x != t[k]]) + t[k + 1:]
        base = edited + "\u2062" * 32
        vecs = []
        for j in range(32):
            a, b = base.encode(), (edited + "\u2062" * j + "\u2063" + "\u2062" * (31 - j)).encode()
            vecs.append(zlib.crc32(bytes(x ^ y for x, y in zip(a, b))) ^ zlib.crc32(bytes(len(a))))
        mask, _ = solve(vecs, zlib.crc32(base.encode()) ^ zlib.crc32(t.encode()))
        sfx["attempts"] += 1
        if mask is None:
            continue
        forged = edited + "".join("\u2063" if mask >> j & 1 else "\u2062" for j in range(32))
        PAIRS["suffix"].append([edited, forged])
        sfx["crc_collision"] += zlib.crc32(forged.encode()) == zlib.crc32(t.encode())
        cand = list(full)
        cand[IDX[i]] = (c, v, forged)
        res = diagnose(reg, cand, prof)
        sfx["proposed_detects"] += bool(res["findings"])
        sfx["class_" + (res["findings"][0][2] if res["findings"] else "none")] += 1
        for fname, font in fonts.items():
            sfx_vis[fname] += same_render(edited, forged, font)
    out = {"visual_pairs": vis_pairs, "select_font": SELECT_FONT, "feasibility": feas, "eligible_verses": len(elig),
           "attacks": dict(att), "swaps_median": float(np.median(n_swaps)),
           "swaps_mean": float(np.mean(n_swaps)), "swaps_max": int(max(n_swaps)), "visual_forgeries": vis,
           "suffix": dict(sfx), "suffix_pixel_identical": dict(sfx_vis),
           "seed": SEED, "n_render": N_RENDER}
    json.dump(out, open("results/e4_crc_forgery.json", "w"), indent=1)
    # second shaping engine (fontkit): NFC/NFD word pairs of Experiment 2 and the pairs above,
    # passed through pipes only (src/engine2.py); set ENGINE2=0 to skip
    if os.environ.get("ENGINE2", "1") == "1":
        import engine2
        e2 = {}
        for form in ("NFC", "NFD"):
            e2[form] = sorted({(w, ud.normalize(form, w)) for _, _, t in full for w in t.split(" ")
                               if ud.normalize(form, w) != w})
        for r, cases in PAIRS["single"].items():
            e2["single_" + r] = cases
        e2["compensated"], e2["suffix"] = PAIRS["compensated"], PAIRS["suffix"]
        engine2.run(e2)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
