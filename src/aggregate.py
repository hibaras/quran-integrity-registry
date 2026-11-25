"""Collect every number used in the paper into results/all_numbers.json.

The paper builder (build/build_paper.js) reads only this file. Confidence intervals
are exact (Clopper-Pearson) 95% intervals."""
import json

from scipy.stats import beta


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
    return [100 * lo, 100 * hi]


def load(name):
    return json.load(open(f"results/{name}", encoding="utf-8"))


e1 = load("e1_detection.json")
seeds = load("e1_seeds.json")
held = load("e1b_heldout.json")
r2b = load("e2b_render_nfc.json")
e3 = load("e3_crossedition.json")
e4 = load("e4_crc_forgery.json")
e5 = load("e5_perf.json")
e6 = load("e6_field.json")
e7 = load("e7_engine2.json")
e7r = load("e7_engine2_raster.json")

n = e1["n_trials"]
conf = e1["confusion_by_family"]
cls_ok = sum(conf[f].get(k, 0) for f, k in (("Letter/word", "L"), ("Diacritic", "D"), ("Unicode", "U")))
cls_ok += sum(conf["Structural"].get(k, 0) for k in ("S-del", "S-ins", "S-reloc"))
n_all = 14 * n
prop = [r for r in e1["rows"] if r["method"] == "Proposed"]
exact_ok = round(sum(r["exact_loc"] * n for r in prop))
hz = e1["hamza_as_letter_correct"]
seed_cls = [v["cls"] / v["n"] * 100 for v in seeds.values()]
seed_exact = [v["exact"] / v["n"] * 100 for v in seeds.values()]
at = e4["attacks"]
out = {
    "e1": e1, "seeds": seeds, "heldout": held, "render_nfc": r2b, "e3": e3, "e4": e4, "e5": e5,
    "e6": e6, "e7": e7, "e7_raster": e7r,
    "derived": {
        "n_trials": n_all, "cls_ok": cls_ok, "cls_ci": cp(cls_ok, n_all),
        "exact_ok": exact_ok, "exact_ci": cp(exact_ok, n_all),
        "detect_lower_per_operator": cp(n, n)[0], "detect_lower_all": cp(n_all, n_all)[0],
        "inverse_cls_ok": n_all - 3 * n, "inverse_n": 11 * n,
        "hamza_letter_ok": hz["Letter/word"], "hamza_letter_n": hz["Letter/word_n"],
        "seed_cls_min": min(seed_cls), "seed_cls_max": max(seed_cls),
        "seed_exact_min": min(seed_exact), "seed_exact_max": max(seed_exact), "n_seeds": len(seeds),
        "crc_ok": at["crc_collision"], "crc_n": at["attempts"], "crc_ci": cp(at["crc_collision"], at["attempts"]),
        "vis_ci": {f: cp(v["pixel_identical"], v["rendered"]) for f, v in e4["visual_forgeries"].items()},
        # NFC-changed words whose change includes moving a fatha before a shadda
        "nfc_shadda_fatha_words": e7["nfc_shadda_fatha_words"],
        "suffix_ci_lower": cp(e4["suffix"]["crc_collision"], e4["suffix"]["attempts"])[0],
        # Table 3: 95% lower bound of a 100% cell for each family size, and the CIs of
        # the cells of the proposed scheme that are below 100%
        "t3_lower_100": {str(k): cp(k, k)[0] for k in (1000, 3000, 5000)},
        "t3_cells_below_100": [
            {"family_ops": ops, "metric": m, "k": k, "n": len(ops) * n, "ci": cp(k, len(ops) * n)}
            for ops, m in ((["Letter substitution", "Letter deletion", "Letter insertion", "Word deletion",
                             "Adjacent-word swap"], "class_acc"), (["Verse insertion (duplicate)"], "exact_loc"))
            for k in [round(sum(r[m] * n for r in prop if r["operator"] in ops))] if k < len(ops) * n],
    },
}
json.dump(out, open("results/all_numbers.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out["derived"], indent=1))
