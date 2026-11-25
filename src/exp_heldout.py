"""Experiment 1b: held-out encoding-level manipulations, generated from Unicode data
files rather than from the operators of Experiment 1, labelled by the original
classifier (three confusable pairs, format characters only) and by the revised one.

H1  insertion of one default-ignorable code point (DerivedCoreProperties 15.1), excluding
    the nine invisible and bidirectional characters used in Experiment 1.
H2  substitution of one letter by a single code point with the same UTS #39 skeleton
    prototype (confusables.txt 15.1), excluding the two pairs used in Experiment 1.
Each manipulated word is also rendered in Noto Naskh Arabic before and after, to record
whether the change is visible: the classifier says what changed in the encoding,
rendering says whether a reader could notice."""
import importlib.util
import json
import random
import sys
import unicodedata as ud
from collections import Counter

from PIL import ImageFont

sys.path.insert(0, "src")
import qintegrity as q  # noqa: E402
from exp_render_nfc import same  # noqa: E402

spec = importlib.util.spec_from_file_location("q_old", "backup_v2/src/qintegrity.py")
q_old = importlib.util.module_from_spec(spec)
sys.modules["q_old"] = q_old
spec.loader.exec_module(q_old)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
ref = [(c, v, t) for c, v, t in q.load_edition("data/uthmani.json") if v >= 1]
prof = q.profile(q.load_edition("data/uthmani.json"))
font = ImageFont.truetype("fonts/NotoNaskhArabic[wght].ttf", 40, layout_engine=ImageFont.Layout.RAQM)
SEEN_INV = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x202E, 0x2067, 0x200F, 0x061C}
DICP_ASSIGNED = sorted(o for o in q.DICP if o not in SEEN_INV and ud.category(chr(o)) != "Cn")
groups = {}
for o in prof:
    ch = chr(o)
    if ud.category(ch).startswith("L"):
        groups.setdefault(q.CONFUSABLES.get(ch, ch), set()).add(ch)
SEEN_SUB = {("ي", "ی"), ("ك", "ک")}
SUBS = {}
for s, proto in q.CONFUSABLES.items():
    if len(s) == 1 and ord(s) not in prof and proto in groups and ud.category(s).startswith("L"):
        for y in groups[proto]:
            if (y, s) not in SEEN_SUB:
                SUBS.setdefault(y, []).append(s)


def word_at(t, k):
    a = t.rfind(" ", 0, k) + 1
    b = t.find(" ", k)
    return a, (len(t) if b < 0 else b)


def run(kind, rng):
    tally = {"old": Counter(), "new": Counter(), "visible": Counter(), "cross": Counter()}
    for _ in range(N):
        c, v, t = rng.choice(ref)
        if kind == "H1":
            k = rng.randrange(1, len(t))
            x = chr(rng.choice(DICP_ASSIGNED))
            new = t[:k] + x + t[k:]
            a, b = word_at(t, k)
            w0, w1 = t[a:b], new[a:b + 1]
        else:
            pos = [k for k, ch in enumerate(t) if ch in SUBS]
            k = rng.choice(pos)
            x = rng.choice(SUBS[t[k]])
            new = t[:k] + x + t[k + 1:]
            a, b = word_at(t, k)
            w0, w1 = t[a:b], new[a:b]
        lo, ln = q_old.classify_verse(t, new, q_old.profile(ref)), q.classify_verse(t, new, prof)
        vis = not same(w0, w1, font)
        tally["old"][lo] += 1
        tally["new"][ln] += 1
        tally["visible"][vis] += 1
        tally["cross"][f"{ln}|{'visible' if vis else 'invisible'}"] += 1
    return {k: dict(v) for k, v in tally.items()}


def main():
    rng = random.Random(404)
    out = {"n": N, "dicp_pool": len(DICP_ASSIGNED),
           "sub_pool": sum(len(v) for v in SUBS.values()), "sub_letters": len(SUBS),
           "H1": run("H1", rng), "H2": run("H2", rng)}
    json.dump(out, open("results/e1b_heldout.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
