"""Experiment 1 (tampering) and Experiment 2 (benign re-normalisation).

Compares the proposed registry with six baselines:
  B1  one SHA-256 digest of the whole file
  B2  position-bound per-verse CRC-32 table (raw bytes)
  B3  position-bound per-verse SHA-256 table (raw bytes)
  B4  unbound existence check of each verse digest (raw bytes)
  B3n ablation: B3 computed on NFC-canonical text
  B3n+A ablation: B3n plus alignment of the verse-digest sequence when a chapter's
        verse count differs (the same alignment the proposed scheme uses)
Also: repeated seeds for the proposed scheme, the hamza-as-letter sensitivity variant,
and a test in which the untrusted mirror returns one altered item.

Usage: python3 src/exp_detection.py [trials_per_operator]          (main run)
       python3 src/exp_detection.py [trials_per_operator] seeds K  (K extra seeds, proposed only)
"""
import difflib
import hashlib
import json
import random
import sys
import time
import unicodedata as ud
import zlib
from collections import Counter, defaultdict

sys.path.insert(0, "src")
import qintegrity as q  # noqa: E402
from qintegrity import AuthError, Mirror, Registry, canon, diagnose, load_edition, profile  # noqa: E402
from attacks import FAMILY, OPERATORS  # noqa: E402

q.USE_CACHE = True                      # identical leaf hashes recur across trials; results are unchanged
N_TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
SEEDS_MODE = len(sys.argv) > 2 and sys.argv[2] == "seeds"
EXTRA_SEEDS = int(sys.argv[3]) if SEEDS_MODE and len(sys.argv) > 3 else 4
SEED = 2026

ref = load_edition("data/uthmani.json")
prof = profile(ref)
reg = Registry(ref)

crc = lambda b: zlib.crc32(b)  # noqa: E731
sha = lambda b: hashlib.sha256(b).digest()  # noqa: E731


def _cached(fn):
    memo = {}

    def g(t):
        r = memo.get(t)
        if r is None:
            r = memo[t] = fn(t)
        return r
    return g


crc_t = _cached(lambda t: crc(t.encode()))
sha_t = _cached(lambda t: sha(t.encode()))
shan_t = _cached(lambda t: sha(canon(t).encode()))


def table(ed, fn):
    return {(c, v): fn(t) for c, v, t in ed}


REF_CRC, REF_SHA, REF_SHAN = table(ref, crc_t), table(ref, sha_t), table(ref, shan_t)
REF_SET = set(REF_SHA.values())
REF_FILE = sha("\n".join(f"{c}|{v}|{t}" for c, v, t in ref).encode())
REF_CHAP = defaultdict(list)
for c, v, t in ref:
    REF_CHAP[c].append((v, shan_t(t)))


def bound_flags(cand, reftab, fn):
    ct = table(cand, fn)
    return {k for k in reftab if ct.get(k) != reftab[k]} | {k for k in ct if k not in reftab}


def aligned_flags(cand):
    """B3n+A: per-verse canonical digests; alignment of digest sequences on count change."""
    cc = defaultdict(list)
    for c, v, t in cand:
        cc[c].append((v, shan_t(t)))
    flags = set()
    for c, rl in REF_CHAP.items():
        cl = cc.get(c, [])
        if len(cl) == len(rl):
            flags |= {(c, v) for (v, a), (_, b) in zip(rl, cl) if a != b}
            continue
        sm = difflib.SequenceMatcher(a=[x for _, x in rl], b=[x for _, x in cl], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("delete", "replace"):
                flags |= {(c, rl[i][0]) for i in range(i1, i2)}
            elif tag == "insert":
                flags |= {(c, cl[j][0]) for j in range(j1, j2)}
    return flags


def run_baselines(cand):
    file_det = sha("\n".join(f"{c}|{v}|{t}" for c, v, t in cand).encode()) != REF_FILE
    out = {"B1": (file_det, None),
           "B2": bound_flags(cand, REF_CRC, crc_t),
           "B3": bound_flags(cand, REF_SHA, sha_t),
           "B4": {(c, v) for c, v, t in cand if sha_t(t) not in REF_SET},
           "B3n": bound_flags(cand, REF_SHAN, shan_t),
           "B3n+A": aligned_flags(cand)}
    return {k: (v if k == "B1" else (bool(v), v)) for k, v in out.items()}


def trial_stream(seed, n):
    rng = random.Random(seed)
    for name, op in OPERATORS.items():
        done = 0
        while done < n:
            r = op(ref, rng)
            if r is None:
                continue
            done += 1
            yield name, r


def run_seeds():
    t0 = time.time()
    seeds = {}
    for k in range(1, EXTRA_SEEDS + 1):
        sd = SEED + k
        det = exact = cls = n = 0
        for name, (cand, gt) in trial_stream(sd, N_TRIALS):
            res = diagnose(reg, cand, prof)
            f_ids = {(c, v) for c, v, _ in res["findings"]}
            det += bool(res["findings"])
            exact += f_ids == gt["ids"]
            cls += {kk for *_, kk in res["findings"]} == {gt["cls"]}
            n += 1
        seeds[sd] = {"n": n, "detect": det, "exact": exact, "cls": cls}
        print(f"seed {sd}: {seeds[sd]} ({time.time() - t0:.0f}s)", flush=True)
    json.dump(seeds, open("results/e1_seeds.json", "w"), indent=1)


def main():
    if SEEDS_MODE:
        return run_seeds()
    t0 = time.time()
    rows, confusion, cost_log = [], defaultdict(Counter), defaultdict(list)
    hamza_ok = Counter()
    stats = defaultdict(lambda: defaultdict(Counter))
    errors = []
    for name, (cand, gt) in trial_stream(SEED, N_TRIALS):
        for b, (det, flags) in run_baselines(cand).items():
            stats[name][b]["det"] += det
            if flags is not None:
                stats[name][b]["exact"] += flags == gt["ids"]
        res = diagnose(reg, cand, prof)
        f_ids = {(c, v) for c, v, _ in res["findings"]}
        f_cls = {k for *_, k in res["findings"]}
        s = stats[name]["Proposed"]
        s["det"] += bool(res["findings"])
        s["exact"] += f_ids == gt["ids"]
        ok = f_cls == {gt["cls"]}
        s["cls"] += ok
        if not ok and len(errors) < 40:
            errors.append({"operator": name, "expected": gt["cls"], "got": sorted(f_cls),
                           "ids": sorted(gt["ids"])})
        confusion[FAMILY[name]]["/".join(sorted(f_cls)) or "none"] += 1
        cost_log[name].append((res["cost"]["hashes"], res["cost"]["records"], res["cost"]["texts"], res["bytes"]))
        if FAMILY[name] != "Structural":
            rh = diagnose(reg, cand, prof, hamza_as_letter=True)
            hamza_ok[FAMILY[name]] += {k for *_, k in rh["findings"]} == {gt["cls"]}
        hamza_ok[FAMILY[name] + "_n"] += FAMILY[name] != "Structural"
    print(f"primary seed done ({time.time() - t0:.0f}s)", flush=True)
    for name in OPERATORS:
        for b, s in stats[name].items():
            rows.append({"operator": name, "family": FAMILY[name], "method": b, "trials": N_TRIALS,
                         "detect": s["det"] / N_TRIALS,
                         "exact_loc": (s["exact"] / N_TRIALS) if b != "B1" else None,
                         "class_acc": (s["cls"] / N_TRIALS) if b == "Proposed" else None})
    cost = {}
    for name, xs in cost_log.items():
        cost[name] = {"hashes_mean": sum(x[0] for x in xs) / len(xs), "hashes_max": max(x[0] for x in xs),
                      "records_mean": sum(x[1] for x in xs) / len(xs),
                      "texts_mean": sum(x[2] for x in xs) / len(xs), "texts_max": max(x[2] for x in xs),
                      "bytes_mean": sum(x[3] for x in xs) / len(xs), "bytes_max": max(x[3] for x in xs)}

    # untrusted mirror returning one altered item
    rng = random.Random(99)
    tamper = Counter()
    ops_in, ops_struct = ["Letter substitution", "Vowel substitution", "Homoglyph substitution"], ["Verse deletion"]
    for i in range(1000):
        structural = i % 4 == 0
        op = OPERATORS[rng.choice(ops_struct if structural else ops_in)]
        r = None
        while r is None:
            r = op(ref, rng)
        cand, _ = r
        kind = rng.choice(["node", "record", "chapter", "profile"] if structural
                          else ["node", "chnode", "record", "text", "profile"])
        try:
            diagnose(reg, cand, prof, mirror=Mirror(reg, corrupt=(kind,)))
            tamper["accepted"] += 1
        except AuthError:
            tamper["rejected"] += 1
        tamper[f"kind_{kind}"] += 1

    # basmala headers (verse 0): one vowel changed in a random header
    from attacks import VOWELS
    rng0 = random.Random(7)
    heads = [i for i, (_, v, _) in enumerate(ref) if v == 0]
    v0 = Counter()
    while v0["n"] < N_TRIALS:
        i = rng0.choice(heads)
        c, v, t = ref[i]
        pos = [k for k, ch in enumerate(t) if ch in VOWELS]
        k = rng0.choice(pos)
        cand = list(ref)
        cand[i] = (c, v, t[:k] + rng0.choice([x for x in VOWELS if x != t[k]]) + t[k + 1:])
        res = diagnose(reg, cand, prof)
        v0["n"] += 1
        v0["detect"] += bool(res["findings"])
        v0["exact"] += {(cc, vv) for cc, vv, _ in res["findings"]} == {(c, 0)}
        v0["cls_D"] += {x for *_, x in res["findings"]} == {"D"}

    # Experiment 2: benign whole-edition re-normalisation
    benign = {}
    for form in ("NFC", "NFD", "NFKC"):
        cand = [(c, v, ud.normalize(form, t)) for c, v, t in ref]
        b = run_baselines(cand)
        res = diagnose(reg, cand, prof)
        benign[form] = {"verses_changed_bytes": sum(1 for (_, v, a), (_, _, x) in zip(ref, cand) if a != x and v >= 1),
                        "headers_changed_bytes": sum(1 for (_, v, a), (_, _, x) in zip(ref, cand) if a != x and v == 0),
                        "items_changed_bytes": sum(1 for (_, _, a), (_, _, x) in zip(ref, cand) if a != x),
                        **{k: (len(v[1]) if v[1] is not None else int(v[0])) for k, v in b.items()},
                        "Proposed": len(res["findings"])}
    out = {"n_trials": N_TRIALS, "seed": SEED, "rows": rows,
           "confusion_by_family": {k: dict(v) for k, v in confusion.items()},
           "errors": errors, "cost": cost, "hamza_as_letter_correct": dict(hamza_ok),
           "mirror_tamper": dict(tamper), "verse0": dict(v0), "benign": benign,
           "n_reference_items": len(ref)}
    json.dump(out, open("results/e1_detection.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("benign", "mirror_tamper", "verse0", "hamza_as_letter_correct")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
