# Data provenance

All texts were taken from the public GitHub repository `risan/quran-json`
(https://github.com/risan/quran-json), commit recorded in `repo_commit.txt`,
directory `data/` (committed upstream snapshots). Each file's SHA-256 was checked
against the repository's own `meta/sources.json` record; all matched.

| File | Upstream source (per sources.json) | Licence (per sources.json) |
|---|---|---|
| uthmani.json | tanzil.net, quranType=uthmani, outType=txt-2 | Tanzil, CC BY 3.0, verbatim copies only |
| uthmani-min.json | tanzil.net, quranType=uthmani-min | same |
| simple.json | tanzil.net, quranType=simple | same |
| simple-clean.json | tanzil.net, quranType=simple-clean | same |
| qpc-hafs.json | api.quranpedia.net dumps/mushafs-2 (KFGQPC Hafs) | Quranpedia data licence |

Tampered variants are generated in memory only, for evaluation; no modified
Quran text is written to disk or redistributed.
