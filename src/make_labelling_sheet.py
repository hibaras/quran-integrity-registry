"""Builds a blank labelling sheet of naturally occurring differences (field-test copies vs the
closest reference edition) for independent human labelling. The sheet holds verse references,
copy ids, edit operations as Unicode code points and names, and the scheme's label; it holds no
Quran text. A specialist fills the empty column; agreement is then computed against it."""
import csv
import difflib
import random
import sys
import unicodedata as ud

sys.path.insert(0, "src")
import qintegrity as q  # noqa: E402
from exp_field import COPIES, REF, load_copy  # noqa: E402
from qintegrity import canon, load_edition, split_basmala  # noqa: E402

q.USE_CACHE = True
E = {k: load_edition(f"data/{k}.json") for k in REF}
V = {k: {(c, v): t for c, v, t in ed if v >= 1} for k, ed in E.items()}
PROF = {k: q.profile(E[k]) for k in REF}
rows = []
for cid, label, chan, kind, path in COPIES:
    cand = split_basmala(load_copy(kind, path))
    cv = {(c, v): t for c, v, t in cand if v >= 1}
    best = max(REF, key=lambda k: (sum(canon(cv[i]) == canon(V[k][i]) for i in set(cv) & set(V[k])),))
    R = V[best]
    for i in sorted(set(cv) & set(R)):
        a, b = canon(R[i]), canon(cv[i])
        if a == b:
            continue
        ops = []
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if op == "equal":
                continue
            nm = lambda s: "+".join(f"U+{ord(c):04X} {ud.name(c, '?')}" for c in s)  # noqa: E731
            ops.append(f"{op}: ref[{nm(a[i1:i2])}] -> copy[{nm(b[j1:j2])}]")
        rows.append({"copy": cid, "closest_edition": best, "verse": f"{i[0]}:{i[1]}",
                     "n_edits": len(ops), "edits": " | ".join(ops[:4]) + (" | ..." if len(ops) > 4 else ""),
                     "scheme_label": q.classify_verse(R[i], cv[i], PROF[best])})
random.seed(2026)
by = {}
for r in rows:
    by.setdefault(r["scheme_label"], []).append(r)
sample = []
for lab, rs in sorted(by.items()):
    random.shuffle(rs)
    sample += rs[:25]
print({k: len(v) for k, v in by.items()}, len(sample))
with open("out/natural_differences_labelling_sheet.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["copy", "closest_edition", "verse", "n_edits", "edits", "scheme_label",
                                      "human_label (U / D / L / U+D / U+L / other)", "notes"])
    w.writeheader()
    for r in sample:
        w.writerow({**r, "human_label (U / D / L / U+D / U+L / other)": "", "notes": ""})
