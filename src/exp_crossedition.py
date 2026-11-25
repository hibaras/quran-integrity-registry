"""Experiment 3: encoding divergence between independent digital editions.

Each edition is parsed (basmala split into verse 0), then verses 1..n are compared at
four views: raw bytes, canonical text (NFC), diagnostic skeleton sigma and comparison
skeleton sigma* (sigma with alef maksura folded to yeh). The residual sigma*
differences between Tanzil Uthmani and KFGQPC Hafs are characterised, the hamza-as-
letter sensitivity variant is computed, and every edition is verified as a candidate
against the Tanzil Uthmani registry. Also writes the per-edition statistics of Table 2."""
import difflib
import json
import sys
import unicodedata as ud
from collections import Counter

sys.path.insert(0, "src")
import qintegrity as q  # noqa: E402
from qintegrity import Registry, canon, diagnose, load_edition, load_raw, profile, skeleton  # noqa: E402

q.USE_CACHE = True
NAMES = {"uthmani": "Tanzil Uthmani", "uthmani-min": "Tanzil Uthmani-min", "simple": "Tanzil Simple",
         "simple-clean": "Tanzil Simple-clean", "qpc-hafs": "KFGQPC Hafs"}
E = {k: load_edition(f"data/{k}.json") for k in NAMES}
V = {k: {(c, v): t for c, v, t in ed if v >= 1} for k, ed in E.items()}
B0 = {k: {c: t for c, v, t in ed if v == 0} for k, ed in E.items()}


def compare(a, b, hamza=False):
    ids = sorted(V[a])
    assert ids == sorted(V[b])
    raw = sum(V[a][i] != V[b][i] for i in ids)
    can = sum(canon(V[a][i]) != canon(V[b][i]) for i in ids)
    sig = [i for i in ids if skeleton(V[a][i], hamza_as_letter=hamza) != skeleton(V[b][i], hamza_as_letter=hamza)]
    sigf = [i for i in ids if skeleton(V[a][i], True, hamza) != skeleton(V[b][i], True, hamza)]
    return {"pair": f"{NAMES[a]} vs {NAMES[b]}", "verses": len(ids), "raw": raw, "canonical": can,
            "sigma": len(sig), "sigma_star": len(sigf)}, sig, sigf


def ops(x, y, fold=True):
    a, b = skeleton(x, fold), skeleton(y, fold)
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag != "equal":
            out.append((tag, " ".join(f"U+{ord(ch):04X}" for ch in a[i1:i2]),
                        " ".join(f"U+{ord(ch):04X}" for ch in b[j1:j2])))
    return out


def main():
    out = {"basmala_split": {NAMES[k]: len(B0[k]) for k in NAMES}}
    pairs = [("uthmani", "qpc-hafs"), ("uthmani", "uthmani-min"), ("simple", "simple-clean"), ("uthmani", "simple")]
    out["comparisons"] = []
    detail = {}
    for a, b in pairs:
        r, sig, sigf = compare(a, b)
        out["comparisons"].append(r)
        detail[(a, b)] = (sig, sigf)
        print(r, flush=True)
    # residual sigma* differences, Tanzil Uthmani vs KFGQPC Hafs
    _, sigf = detail[("uthmani", "qpc-hafs")]
    out["residual_uthmani_vs_qpc"] = {"ids": [f"{c}:{v}" for c, v in sigf],
                                      "ops": {f"{c}:{v}": ops(V["uthmani"][(c, v)], V["qpc-hafs"][(c, v)])
                                              for c, v in sigf}}
    # Tanzil Uthmani vs Uthmani-min: what the sigma differences are
    sig, sigf = detail[("uthmani", "uthmani-min")]
    oc = Counter()
    for i in sig:
        for o in ops(V["uthmani"][i], V["uthmani-min"][i], fold=False):
            oc[o] += 1
    out["uthmani_vs_min"] = {"sigma_ids": [f"{c}:{v}" for c, v in sig], "sigma_star_ids": [f"{c}:{v}" for c, v in sigf],
                             "ops": [(list(k), n) for k, n in oc.most_common(10)],
                             "sigma_star_ops": {f"{c}:{v}": ops(V["uthmani"][(c, v)], V["uthmani-min"][(c, v)])
                                                for c, v in sigf}}
    # sigma (no maksura fold) residual characterisation for Uthmani vs QPC
    sig_q, _ = detail[("uthmani", "qpc-hafs")]
    oq = Counter()
    for i in sig_q:
        for o in ops(V["uthmani"][i], V["qpc-hafs"][i], fold=False):
            oq[o] += 1
    out["uthmani_vs_qpc_sigma_ops"] = [(list(k), n) for k, n in oq.most_common(8)]
    # hamza-as-letter sensitivity
    r, _, sigf_h = compare("uthmani", "qpc-hafs", hamza=True)
    out["hamza_as_letter"] = {"uthmani_vs_qpc_sigma_star": r["sigma_star"]}
    # every edition verified against the Tanzil Uthmani registry
    ref = E["uthmani"]
    reg, prof = Registry(ref), profile(ref)
    diag = {}
    for k in ("qpc-hafs", "uthmani-min", "simple", "simple-clean"):
        res = diagnose(reg, E[k], prof)
        diag[NAMES[k]] = {"flagged": len(res["findings"]), "items": len(E[k]),
                          "labels": dict(Counter(x for *_, x in res["findings"]).most_common()),
                          "mismatch": res["mismatch"], "bytes": res["bytes"]}
        print(k, diag[NAMES[k]], flush=True)
    out["diagnosis_vs_tanzil_registry"] = diag
    # code points outside the Tanzil profile used by KFGQPC Hafs
    qp = profile(E["qpc-hafs"])
    out["qpc_out_of_profile"] = [f"U+{o:04X} {ud.name(chr(o), '?')}" for o in sorted(qp - prof)]
    # Table 2: per-edition statistics (verses 1..n as parsed; raw file sizes)
    t2 = {}
    for k in NAMES:
        raw = load_raw(f"data/{k}.json")
        txt = "".join(t for *_, t in raw)
        t2[NAMES[k]] = {"code_points": len(txt), "utf8_bytes": len(txt.encode()), "distinct": len(set(txt)),
                        "distinct_after_nfc": len(set(ud.normalize("NFC", txt))),
                        "verses_changed_by_nfc": sum(ud.normalize("NFC", t) != t for t in V[k].values()),
                        "basmala_headers": len(B0[k]),
                        "basmala_changed_by_nfc": sum(ud.normalize("NFC", t) != t for t in B0[k].values())}
    out["table2"] = t2
    json.dump(out, open("results/e3_crossedition.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("residual_uthmani_vs_qpc", "hamza_as_letter", "table2")},
                     ensure_ascii=False, indent=1)[:3500])
    print(json.dumps(out["uthmani_vs_min"], ensure_ascii=False)[:1500])
    print(out["uthmani_vs_qpc_sigma_ops"], out["qpc_out_of_profile"])


if __name__ == "__main__":
    main()
