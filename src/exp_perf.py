"""Experiment 5: computational and storage cost, and the data a verifier fetches from the
untrusted mirror to localise k tampered verses (100 runs per k)."""
import hashlib
import json
import platform
import random
import statistics as st
import sys
import time
import zlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, "src")
import qintegrity as q  # noqa: E402
from qintegrity import HASHES, Registry, canon, diagnose, load_edition, profile, verify_verse  # noqa: E402
from attacks import VOWELS  # noqa: E402

REPS = 30
ref = load_edition("data/uthmani.json")
prof = profile(ref)


def timeit(fn, reps=REPS):
    xs = []
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        xs.append(time.perf_counter() - t)
    xs.sort()
    q = st.quantiles(xs, n=4)
    return {"median_ms": 1000 * st.median(xs), "q1_ms": 1000 * q[0], "q3_ms": 1000 * q[2]}


def main():
    out = {"platform": {"python": platform.python_version(), "machine": platform.machine(),
                        "processor": "Intel(R) Xeon(R) Processor @ 2.10GHz (2 vCPU)"}}
    # canonicalisation of the whole edition
    out["canonicalise_all"] = timeit(lambda: [canon(t) for *_, t in ref])
    # per-verse table hashing (raw) and full two-level registry build per hash function
    raw = [t.encode() for *_, t in ref]
    out["table"] = {"crc32": timeit(lambda: [zlib.crc32(b) for b in raw])}
    for name, h in HASHES.items():
        out["table"][name] = timeit(lambda h=h: [h(b) for b in raw])
    out["registry_build"] = {name: timeit(lambda name=name: Registry(ref, name).statement("tanzil-uthmani", "1.1"),
                                          reps=10) for name in HASHES}   # publisher: tree, profile P, statement
    # signature over the root statement
    reg = Registry(ref)
    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key()
    stmt = reg.statement("tanzil-uthmani", "1.1")
    sig = sk.sign(stmt)
    out["ed25519"] = {"sign": timeit(lambda: sk.sign(stmt), 200), "verify": timeit(lambda: pk.verify(sig, stmt), 200),
                      "signature_bytes": len(sig), "statement_bytes": len(stmt)}
    # proofs for every verse
    h = HASHES["sha256"]
    proofs = []
    t = time.perf_counter()
    for c in reg.order:
        for i in range(len(reg.chapters[c])):
            proofs.append((c, i, reg.proof(c, i)))
    gen_s = time.perf_counter() - t
    t = time.perf_counter()
    okc = 0
    for c, i, pf in proofs:
        v, txt = reg.chapters[c][i]
        okc += verify_verse(h, c, v, txt, pf, reg.root)
    ver_s = time.perf_counter() - t
    sizes = [32 * (len(pf["ch_path"]) + len(pf["top_path"]) + 1) + 4 for *_, pf in proofs]   # paths + chapter root + counters
    out["proofs"] = {"n": len(proofs), "all_valid": okc == len(proofs),
                     "gen_us_per_verse": 1e6 * gen_s / len(proofs), "verify_us_per_verse": 1e6 * ver_s / len(proofs),
                     "bytes_min": min(sizes), "bytes_mean": st.mean(sizes), "bytes_max": max(sizes)}
    out["storage_bytes"] = {"crc32_table": 4 * len(ref), "sha256_table": 32 * len(ref),
                            "signed_statement": len(stmt) + len(sig), "edition_utf8": sum(len(b) for b in raw),
                            "items": len(ref)}
    # full verification of an intact copy (fresh strings, so no shortcut applies)
    fresh = [(c, v, "".join(list(t))) for c, v, t in ref]
    out["full_verify_intact"] = timeit(lambda: Registry(fresh).root == reg.root and pk.verify(sig, stmt) is None, reps=10)
    out["detection_only_bytes"] = len(stmt) + len(sig)
    # localisation cost vs number of tampered verses
    q.USE_CACHE = True                                  # timings are finished; results do not depend on it
    rng = random.Random(11)
    vowelled = [i for i, (_, v, t) in enumerate(ref) if v >= 1 and any(ch in VOWELS for ch in t)]
    loc = []
    RUNS = 100
    for k in (1, 2, 4, 8, 16, 32, 64, 128, 256):
        qs, bs, exact = [], [], 0
        for _ in range(RUNS):
            idx = rng.sample(vowelled, k)
            cand = list(ref)
            truth = set()
            for i in idx:
                c, v, t = cand[i]
                pos = [p for p, ch in enumerate(t) if ch in VOWELS]
                p = rng.choice(pos)
                cand[i] = (c, v, t[:p] + rng.choice([x for x in VOWELS if x != t[p]]) + t[p + 1:])
                truth.add((c, v))
            res = diagnose(reg, cand, prof)
            qs.append(res["cost"]["hashes"])
            bs.append(res["bytes"])
            exact += {(c, v) for c, v, _ in res["findings"]} == truth
        loc.append({"k": k, "hashes_mean": st.mean(qs), "hashes_max": max(qs), "bytes_mean": st.mean(bs),
                    "bytes_max": max(bs), "exact": exact / RUNS, "runs": RUNS,
                    "table_hashes": len(ref), "table_bytes": 32 * len(ref)})
    out["localisation"] = loc
    json.dump(out, open("results/e5_perf.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
