// Second shaping engine for the rendering checks (Exp. 2b and Exp. 4).
// fontkit (npm 2.0.4) implements its own OpenType layout (GSUB/GPOS, Arabic shaper);
// it does not use HarfBuzz. For each string pair we lay both strings out and compare
// the ink they would put on the page: the multiset of (glyph outline, x, y) over all
// glyphs with a non-empty outline, in font units. Equal multisets give identical
// rasterisations with any renderer; glyph ids are ignored, so two glyphs with the
// same outline count as the same ink. The total advance is compared separately.
// Usage: node src/engine2_fontkit.js - results/e7_engine2.json   (pairs as JSON on stdin;
// src/engine2.py supplies them, so no altered text is ever written to disk)
const fs = require('fs');
const fk = require(process.env.FONTKIT || 'fontkit');

const FONTS = {
  'Noto Naskh Arabic': 'fonts/NotoNaskhArabic[wght].ttf',
  'Amiri': 'fonts/Amiri-Regular.ttf',
  'Scheherazade New': 'fonts/ScheherazadeNew-Regular.ttf',
  'Amiri Quran': 'fonts/AmiriQuran.ttf',
  'KFGQPC Uthmanic Hafs': 'fonts/UthmanicHafs1Ver18.ttf',
};

const pathCache = new Map();
function outline(font, fname, g) {
  const key = fname + ':' + g.id;
  if (!pathCache.has(key)) pathCache.set(key, g.path.toSVG());
  return pathCache.get(key);
}

function ink(font, fname, text) {
  const run = font.layout(text);
  let x = 0, y = 0;
  const items = [];
  const notdef = run.glyphs.filter(g => g.id === 0).length;
  run.glyphs.forEach((g, i) => {
    const p = run.positions[i];
    const d = outline(font, fname, g);
    if (d.length) items.push(d + '@' + (x + p.xOffset) + ',' + (y + p.yOffset));
    x += p.xAdvance; y += p.yAdvance;
  });
  items.sort();
  return { ink: items.join('|'), advance: x, notdef };
}

function main() {
  const [inp, outp] = process.argv.slice(2);
  const pairs = JSON.parse(fs.readFileSync(inp === '-' ? 0 : inp, 'utf8'));
  const out = { engine: 'fontkit ' + require((process.env.FONTKIT || 'fontkit') + '/package.json').version, sets: {} };
  for (const [set, list] of Object.entries(pairs)) {
    out.sets[set] = { pairs: list.length, fonts: {} };
    for (const [fname, file] of Object.entries(FONTS)) {
      const font = fk.openSync(file);
      const r = { ink_identical: 0, advance_identical: 0, errors: 0, notdef_pairs: 0, examples: [] };
      for (const [a, b] of list) {
        try {
          const A = ink(font, fname, a), B = ink(font, fname, b);
          if (A.ink === B.ink) r.ink_identical++;
          else if (r.examples.length < 3) r.examples.push([a.length, b.length]);
          if (A.advance === B.advance) r.advance_identical++;
          if (A.notdef || B.notdef) r.notdef_pairs++;
        } catch (e) {
          r.errors++;
          if (!r.error) r.error = String(e.message).slice(0, 80);
        }
      }
      out.sets[set].fonts[fname] = r;
      console.log(set, fname, JSON.stringify({ n: list.length, ink: r.ink_identical, adv: r.advance_identical, err: r.errors, notdef: r.notdef_pairs }));
    }
  }
  fs.writeFileSync(outp, JSON.stringify(out, null, 1));
}
main();
