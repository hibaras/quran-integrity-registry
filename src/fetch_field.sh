#!/usr/bin/env bash
# Fetch the distributed Quran copies used in the field test (Exp. 6) into data/field/.
# Every source is pinned (git commit or npm version) and checked against a SHA-256
# recorded on 2026-11-11. Nothing is executed from the downloaded packages.
set -euo pipefail
OUT="${1:-data/field}"
SUMS="$(cd "$(dirname "$0")" && pwd)/field_sha256.txt"
mkdir -p "$OUT"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) fawazahmed0/quran-api (Unlicense), branch "1" at commit 93e6f64 (served by jsDelivr)
C=93e6f64925ae76273520d636fcaaf061129f2316
for e in ara-quranuthmanihaf ara-quransimple ara-quranacademy ara-quranindopak \
         ara-qurankhaledhosn ara-quranuthmanihaf1 ara-quranspelled; do
  curl -sS -f -o "$OUT/api-$e.json" \
    "https://raw.githubusercontent.com/fawazahmed0/quran-api/$C/editions/$e.json"
done

# 2) npm packages (tarballs from registry.npmjs.org); only the Arabic text file is kept
fetch_npm () {   # name version tarball-url member out-name
  curl -sS -f -o "$TMP/p.tgz" "$3"
  tar -xzf "$TMP/p.tgz" -C "$TMP" "package/$4"
  mv "$TMP/package/$4" "$OUT/$5"
  rm -rf "$TMP/package" "$TMP/p.tgz"
}
fetch_npm quran 0.0.9 https://registry.npmjs.org/quran/-/quran-0.0.9.tgz \
  data/qurandb npm-quran-0.0.9.sqlite
fetch_npm quran-cloud 1.0.0 https://registry.npmjs.org/quran-cloud/-/quran-cloud-1.0.0.tgz \
  dist/quran.json npm-quran-cloud-1.0.0.json
fetch_npm @muslims-community/quran 1.1.0 \
  https://registry.npmjs.org/@muslims-community/quran/-/quran-1.1.0.tgz \
  dist/quran.json npm-muslims-community-quran-1.1.0.json

(cd "$OUT" && sha256sum -c "$SUMS")
