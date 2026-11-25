# Reproducibility package – Unicode-aware, position-bound Quran text integrity (IMAN 2026)

Every number, table and figure in the paper is produced by the scripts below; the paper
builder reads only `results/all_numbers.json`, which `src/aggregate.py` assembles from the
experiment outputs.

## Data (`data/`)
* Quran texts from https://github.com/risan/quran-json, commit
  6523a9ad3b73bb7e8cb3a9cdf0ea774b8bab3123, directory `data/`: `tanzil/uthmani.json`,
  `tanzil/uthmani-min.json`, `tanzil/simple.json`, `tanzil/simple-clean.json`,
  `quranpedia/qpc-hafs.json`, `meta/sources.json`, `meta/qa.json` (see `data/PROVENANCE.md`).
  The repository checksums show snapshot integrity only, not fidelity to the publishers' releases.
* Field-test copies (Exp. 6), fetched by `src/fetch_field.sh` into `data/field/` and checked
  against `src/field_sha256.txt`: seven Arabic editions of https://github.com/fawazahmed0/quran-api
  (public domain, branch `1` at commit 93e6f64925ae76273520d636fcaaf061129f2316) and the Arabic
  text of the npm packages quran 0.0.9 (LGPL), quran-cloud 1.0.0 (CC-BY-4.0) and
  @muslims-community/quran 1.1.0 (MIT). They are not redistributed here; the script downloads
  them from their pinned sources. `ara-kingfahadquranc` (a tafsir) and `ara-quranuthmanienc`
  (byte-identical to `ara-quranacademy`) were excluded.
* Unicode 15.1.0 data files (the version used by Python 3.13's `unicodedata`), from
  https://github.com/unicode-org/unicodetools: `confusables-15.1.0.txt` (UTS #39) and
  `DerivedCoreProperties-15.1.0.txt` (Default_Ignorable_Code_Point).

## Fonts (`fonts/`, not redistributed here; download before running the rendering checks)
Noto Naskh Arabic (Google Fonts, OFL), Amiri 1.000 and Amiri Quran 1.000
(github.com/aliftype/amiri releases, OFL), Scheherazade New (SIL, OFL), and KFGQPC Uthmanic
Hafs 0.18 (`UthmanicHafs1Ver18.ttf`, King Fahd Complex; obtain from the publisher or an
authorised source and respect its licence).

## Requirements
Python 3.13 with cryptography, blake3, numpy, scipy, Pillow built with libraqm (HarfBuzz),
matplotlib; Node.js with the `docx` package for the paper build and `fontkit` 2.0.4
(`npm install fontkit@2.0.4`) for the second-engine check; `rsvg-convert` (librsvg) to rasterise
its samples.

## Run (from this folder); experiment numbers match the paper
```
python3 src/exp_detection.py 1000            # Exp. 1 (tampering) + Exp. 2 (benign) -> results/e1_detection.json
python3 src/exp_detection.py 1000 seeds 4    # Exp. 1, four further seeds          -> results/e1_seeds.json
python3 src/exp_heldout.py 1000              # held-out manipulations H1/H2        -> results/e1b_heldout.json
python3 src/exp_render_nfc.py                # Exp. 2 rendering check (5 fonts)    -> results/e2b_render_nfc.json
python3 src/exp_crossedition.py              # Exp. 3 (editions, Table 2 numbers)  -> results/e3_crossedition.json
FONTKIT=/path/to/node_modules/fontkit python3 src/exp_crc_forgery.py 1000 300
                                             # Exp. 4 (CRC-32 forgery) and the fontkit check of Exp. 2 and 4
                                             # -> results/e4_crc_forgery.json, e7_engine2.json, e7_engine2_raster.json
python3 src/exp_perf.py                      # Exp. 5 (cost; run on an idle machine) -> results/e5_perf.json
bash src/fetch_field.sh data/field           # field-test copies (pinned, SHA-256 checked)
python3 src/exp_field.py                     # Exp. 6 (distributed copies)         -> results/e6_field.json
python3 src/aggregate.py                     # -> results/all_numbers.json (adds exact 95% CIs)
python3 src/fig_architecture.py              # Figure 1 (fig_results.py draws a localisation plot no longer in the paper)
cat build/head.js build/content.js > build/build_paper.js && node build/build_paper.js   # -> out/IMAN2026_Quran_Integrity.docx
```
`exp_heldout.py` compares the revised diagnosis rules with the original ones, which it loads
from `backup_v2/src/qintegrity.py`; keep that file when publishing the package.

## Code
* `src/qintegrity.py` – parsing (basmala as verse 0), canonical form (NFC + ASCII trim),
  skeletons σ and σ_f, two-level RFC 6962 Merkle registry, length-prefixed signed statement,
  RFC 9162 proof verification, untrusted-mirror verification with authentication of every
  fetched item, and diagnosis rules derived from the Unicode data files.
* `src/attacks.py` – the 14 tampering operators (verse 0 is never targeted).
* `src/engine2.py`, `src/engine2_fontkit.js`, `src/engine2_svg.js` – second shaping engine
  (fontkit): string pairs reach Node and `rsvg-convert` through pipes only.
* `src/exp_field.py`, `src/fetch_field.sh`, `src/field_sha256.txt` – field test (Exp. 6).
* Tampered copies are generated in memory only; no modified Quran text is written to disk.
