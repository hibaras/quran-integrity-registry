"""Experiment 2b: does whole-edition NFC or NFD re-normalisation change what a reader sees?

Every word whose bytes change under NFC (or NFD) is rendered before and after with
HarfBuzz shaping (Pillow + libraqm) in five fonts, and the bitmaps are compared. Words
are separated by spaces, so Arabic joining and mark positioning never cross a word
boundary; a verse is pixel-identical if all of its changed words are."""
import json
import sys
import unicodedata as ud

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "src")
from qintegrity import load_edition  # noqa: E402

FONTS = {"Amiri": "fonts/Amiri-Regular.ttf", "Noto Naskh Arabic": "fonts/NotoNaskhArabic[wght].ttf",
         "Scheherazade New": "fonts/ScheherazadeNew-Regular.ttf", "Amiri Quran": "fonts/AmiriQuran.ttf",
         "KFGQPC Uthmanic Hafs": "fonts/UthmanicHafs1Ver18.ttf"}
SIZE = 40


def render(text, font):
    l, t, r, b = font.getbbox(text, direction="rtl")
    w, h = int(r - l) + 120, int(b - t) + 160
    img = Image.new("L", (w, h), 255)
    ImageDraw.Draw(img).text((w - 60, 80), text, font=font, fill=0, anchor="rs", direction="rtl")
    return np.asarray(img)


def same(a, b, font):
    x, y = render(a, font), render(b, font)
    return x.shape == y.shape and np.array_equal(x, y)


def main():
    ed = [(c, v, t) for c, v, t in load_edition("data/uthmani.json")]
    out = {}
    for form in ("NFC", "NFD"):
        pairs, verse_words = set(), {}
        for c, v, t in ed:
            ws = t.split(" ")
            ch = [(w, ud.normalize(form, w)) for w in ws if ud.normalize(form, w) != w]
            if ch:
                verse_words[(c, v)] = ch
                pairs.update(ch)
        res = {"items_changed": len(verse_words), "verses_changed": sum(1 for (c, v) in verse_words if v >= 1),
               "unique_words": len(pairs), "fonts": {}}
        for fname, path in FONTS.items():
            font = ImageFont.truetype(path, SIZE, layout_engine=ImageFont.Layout.RAQM)
            ok = {p: same(p[0], p[1], font) for p in pairs}
            bad_words = [p for p, s in ok.items() if not s]
            bad_items = [k for k, ch in verse_words.items() if not all(ok[p] for p in ch)]
            res["fonts"][fname] = {"words_identical": len(pairs) - len(bad_words),
                                   "items_identical": len(verse_words) - len(bad_items),
                                   "verses_not_identical": sum(1 for (c, v) in bad_items if v >= 1),
                                   "examples": [[" ".join(f"U+{ord(x):04X}" for x in a),
                                                 " ".join(f"U+{ord(x):04X}" for x in b)] for a, b in bad_words[:3]]}
            print(form, fname, {k: res["fonts"][fname][k] for k in ("words_identical", "items_identical")},
                  "of", len(pairs), len(verse_words), flush=True)
        out[form] = res
    json.dump(out, open("results/e2b_render_nfc.json", "w"), indent=1)


if __name__ == "__main__":
    main()
