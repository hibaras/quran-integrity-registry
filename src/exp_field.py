"""Experiment 6 (field test): Quran copies distributed to application developers.

Ten copies taken as distributed (src/fetch_field.sh; seven editions of the public
fawazahmed0/quran-api dataset at a pinned commit and the Arabic text of three npm
packages) are parsed into (chapter, verse, text), the basmala is split as for the
reference editions, and each copy is
  (a) compared with the five reference editions at four views (raw, canonical,
      sigma, sigma*), to find the edition it derives from, and
  (b) verified with diagnose() against the registry of that closest edition.
Nothing is modified; the copies are only read. Output: results/e6_field.json."""
import json
import re
import sqlite3
import sys
import time
import unicodedata as ud
from collections import Counter

sys.path.insert(0, "src")
import qintegrity as q  # noqa: E402
from qintegrity import Registry, canon, diagnose, load_edition, skeleton, split_basmala  # noqa: E402

q.USE_CACHE = True
F = "data/field/"
REF = {"uthmani": "Tanzil Uthmani", "uthmani-min": "Tanzil Uthmani-min", "simple": "Tanzil Simple",
       "simple-clean": "Tanzil Simple-clean", "qpc-hafs": "KFGQPC Hafs"}

COPIES = [  # id, label, channel, loader kind, file
    ("api-uthmanihaf", "quran-api: Uthmani Hafs", "API/CDN", "api", "api-ara-quranuthmanihaf.json"),
    ("api-simple", "quran-api: Simple", "API/CDN", "api", "api-ara-quransimple.json"),
    ("api-academy", "quran-api: Quran Academy", "API/CDN", "api", "api-ara-quranacademy.json"),
    ("api-indopak", "quran-api: IndoPak", "API/CDN", "api", "api-ara-quranindopak.json"),
    ("api-khaledhosn", "quran-api: Khaled Hosney", "API/CDN", "api", "api-ara-qurankhaledhosn.json"),
    ("api-uthmanihaf1", "quran-api: Uthmani Hafs, no diacritics", "API/CDN", "api",
     "api-ara-quranuthmanihaf1.json"),
    ("api-spelled", "quran-api: Spelled", "API/CDN", "api", "api-ara-quranspelled.json"),
    ("npm-quran", "npm quran 0.0.9", "npm", "sqlite", "npm-quran-0.0.9.sqlite"),
    ("npm-quran-cloud", "npm quran-cloud 1.0.0", "npm", "cloud", "npm-quran-cloud-1.0.0.json"),
    ("npm-muslims", "npm @muslims-community/quran 1.1.0", "npm", "muslims",
     "npm-muslims-community-quran-1.1.0.json"),
]


def load_copy(kind, path):
    p = F + path
    if kind == "api":
        rows = [(int(x["chapter"]), int(x["verse"]), x["text"]) for x in json.load(open(p, encoding="utf-8"))["quran"]]
    elif kind == "sqlite":
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        rows = [(int(c), int(v), t) for c, v, t in con.execute("select chapter, verse, ar from ar order by chapter, verse")]
    elif kind == "cloud":
        rows = [(int(s["id"]), int(a["id"]), a["text"]) for s in json.load(open(p, encoding="utf-8")) for a in s["verses"]]
    elif kind == "muslims":
        rows = [(int(s["id"]), int(a["id"]), a["text"]) for s in json.load(open(p, encoding="utf-8"))["surahs"]
                for a in s["ayat"]]
    else:
        raise ValueError(kind)
    rows.sort()
    return rows


def views_equal(a, b):
    ids = sorted(set(a) & set(b))
    return {"shared": len(ids),
            "raw": sum(a[i] == b[i] for i in ids),
            "canonical": sum(canon(a[i]) == canon(b[i]) for i in ids),
            "sigma": sum(skeleton(a[i]) == skeleton(b[i]) for i in ids),
            "sigma_star": sum(skeleton(a[i], True) == skeleton(b[i], True) for i in ids)}


def main():
    E = {k: load_edition(f"data/{k}.json") for k in REF}
    V = {k: {(c, v): t for c, v, t in ed if v >= 1} for k, ed in E.items()}
    regs = {}
    out = []
    for cid, label, chan, kind, path in COPIES:
        raw = load_copy(kind, path)
        cand = split_basmala(raw)
        cv = {(c, v): t for c, v, t in cand if v >= 1}
        headers = sum(1 for _, v, _ in cand if v == 0)
        cps = Counter(ch for *_, t in raw for ch in t)
        rec = {"id": cid, "label": label, "channel": chan, "file": path, "verses": len(raw),
               "chapters": len({c for c, _, _ in raw}), "basmala_headers_split": headers,
               "distinct_code_points": len(cps),
               "verses_not_nfc": sum(ud.normalize("NFC", t) != t for *_, t in raw),
               "verses_not_nfd": sum(ud.normalize("NFD", t) != t for *_, t in raw),
               "farsi_yeh_U06CC": cps.get("ی", 0), "tatweel_U0640": cps.get("ـ", 0),
               "default_ignorable": sum(n for ch, n in cps.items() if ord(ch) in q.DICP),
               "match": {k: views_equal(cv, V[k]) for k in REF}}
        # closest reference edition: most verses equal canonically, then on sigma*
        best = max(REF, key=lambda k: (rec["match"][k]["canonical"], rec["match"][k]["sigma_star"]))
        rec["closest"] = best
        m = rec["match"][best]
        rec["canonical_only_equal"] = m["canonical"] - m["raw"]   # equal only after NFC
        R = V[best]
        ids = sorted(set(cv) & set(R))
        rec["verse_level"] = {
            "b3_raw_flagged": sum(cv[i] != R[i] for i in ids),          # raw SHA-256 table
            "kappa_flagged": sum(canon(cv[i]) != canon(R[i]) for i in ids),
            "equal_to_nfd_of_ref": sum(cv[i] == ud.normalize("NFD", R[i]) for i in ids),
            "copy_verses_in_nfd": sum(ud.normalize("NFD", t) == t for *_, t in raw),
            "ref_verses_in_nfd": sum(ud.normalize("NFD", R[i]) == R[i] for i in ids)}
        rec["invisible_by_cp"] = {f"U+{ord(ch):04X}": n for ch, n in sorted(cps.items()) if ord(ch) in q.DICP}
        rec["nonascii_space_by_cp"] = {f"U+{ord(ch):04X}": n for ch, n in sorted(cps.items())
                                       if ch.isspace() and ord(ch) > 0x7F}
        prof_ref = q.profile(E[best])
        # letter-skeleton differences left after the scheme's repair step (Farsi yeh,
        # default-ignorables and other out-of-profile characters mapped back)
        # sigma*-differing verses whose only letter difference is a standalone hamza (U+0621)
        # where the reference has tatweel, optional vowel signs and hamza above (U+0640 .. U+0654)
        hz = re.compile("\u0640([\u064b-\u0652\u0670]*)\u0654")
        rec["sigma_star_hamza_reencoding_only"] = sum(
            1 for i in ids if skeleton(cv[i], True) != skeleton(R[i], True)
            and skeleton(hz.sub("\u0621\\1", canon(R[i])), True) == skeleton(cv[i], True))
        rec["sigma_star_differ_after_repair"] = sum(
            skeleton(q.repair(canon(cv[i]), prof_ref), True) != skeleton(R[i], True) for i in ids)
        rec["out_of_profile_by_cp"] = {f"U+{ord(ch):04X}": n for ch, n in sorted(cps.items())
                                       if ord(ch) not in prof_ref and ch not in "\n\r\t"}
        if best not in regs:
            regs[best] = Registry(E[best], "sha256")
        t0 = time.perf_counter()
        try:
            r = diagnose(regs[best], cand)
            labels = Counter(k for *_, k in r["findings"])
            rec.update({"accepted": not r["findings"], "findings": len(r["findings"]),
                        "labels": dict(sorted(labels.items())), "mismatch_flag": r["mismatch"],
                        "verse0_findings": sum(1 for _, v, _ in r["findings"] if v == 0),
                        "verify_ms": round(1000 * (time.perf_counter() - t0), 1)})
        except NotImplementedError as e:
            rec.update({"accepted": False, "error": str(e)})
        out.append(rec)
        print(cid, best, m, rec.get("accepted"), rec.get("labels"), rec.get("mismatch_flag"), flush=True)
    meta = {"quran_api_commit": "93e6f64925ae76273520d636fcaaf061129f2316",
            "npm": {"quran": "0.0.9", "quran-cloud": "1.0.0", "@muslims-community/quran": "1.1.0"},
            "fetched": "2026-11-11",
            "excluded": {"ara-kingfahadquranc": "tafsir text (al-Muyassar), not the Quran text",
                         "ara-quranuthmanienc": "byte-identical to ara-quranacademy (same SHA-256)"}}
    json.dump({"meta": meta, "copies": out}, open("results/e6_field.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
