#!/usr/bin/env bash
# Reproduce every result, figure and the paper (see README.md). Run from this folder.
set -euo pipefail
python3 src/exp_detection.py 1000
python3 src/exp_detection.py 1000 seeds 4
python3 src/exp_heldout.py 1000
python3 src/exp_render_nfc.py
python3 src/exp_crossedition.py
# fontkit 2.0.4 must be resolvable (npm install fontkit@2.0.4, or set FONTKIT to its path)
python3 src/exp_crc_forgery.py 1000 300
python3 src/exp_perf.py
bash src/fetch_field.sh data/field
python3 src/exp_field.py
python3 src/aggregate.py
python3 src/fig_architecture.py
cat build/head.js build/content.js > build/build_paper.js
node build/build_paper.js
