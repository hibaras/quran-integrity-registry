"""Second shaping engine (fontkit 2.0.4) for the rendering checks of Experiments 2 and 4.

run(pairs) receives the string pairs in memory (from exp_crc_forgery.py), passes them to
src/engine2_fontkit.js on stdin (ink comparison -> results/e7_engine2.json), then has
src/engine2_svg.js draw a sample of differing pairs as SVG on stdout, rasterises each with
rsvg-convert through pipes and counts pixel-different pairs
(-> results/e7_engine2_raster.json). No altered Quran text is written to disk."""
import io
import json
import os
import subprocess
from collections import defaultdict

import numpy as np
from PIL import Image

NODE_ENV = dict(os.environ)


def _png(svg: str) -> np.ndarray:
    out = subprocess.run(["rsvg-convert"], input=svg.encode(), capture_output=True, check=True).stdout
    return np.asarray(Image.open(io.BytesIO(out)).convert("L"))


def run(pairs: dict, per_cell: int = 40, seed: int = 11) -> None:
    data = json.dumps(pairs, ensure_ascii=False).encode()
    subprocess.run(["node", "src/engine2_fontkit.js", "-", "results/e7_engine2.json"], input=data,
                   check=True, env=NODE_ENV)
    nfc = pairs.get("NFC", [])
    extra = {"nfc_shadda_fatha_words": sum(1 for a, b in nfc if "َّ" in a and "َّ" in b)}
    e7 = json.load(open("results/e7_engine2.json"))
    e7.update(extra)
    json.dump(e7, open("results/e7_engine2.json", "w"), indent=1)
    proc = subprocess.run(["node", "src/engine2_svg.js", str(per_cell), str(seed)], input=data,
                          capture_output=True, check=True, env=NODE_ENV)
    res = defaultdict(lambda: {"sampled": 0, "pixel_different": 0, "max_pixels_changed": 0})
    for line in proc.stdout.decode().splitlines():
        it = json.loads(line)
        a, b = _png(it["a"]), _png(it["b"])
        r = res[f"{it['set']}|{it['font']}"]
        r["sampled"] += 1
        if a.shape != b.shape or not np.array_equal(a, b):
            r["pixel_different"] += 1
            if a.shape == b.shape:
                r["max_pixels_changed"] = max(r["max_pixels_changed"], int((np.abs(a.astype(int) - b) > 64).sum()))
    json.dump(res, open("results/e7_engine2_raster.json", "w"), indent=1)
    print("engine2 raster:", dict(res), flush=True)
