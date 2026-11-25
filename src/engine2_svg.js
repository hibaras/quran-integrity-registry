// Companion to engine2_fontkit.js: draws as SVG (fontkit layout, 48 px em) a random sample
// of the pairs whose ink differed, so that src/engine2.py can rasterise and compare them
// pixel by pixel. Pairs come as JSON on stdin; one JSON line per sampled pair is written to
// stdout. Nothing is written to disk. Usage: node src/engine2_svg.js [per_cell=40] [seed=11]
const fs = require('fs');
const fk = require(process.env.FONTKIT || 'fontkit');
const FONTS = {
  'Noto Naskh Arabic': 'fonts/NotoNaskhArabic[wght].ttf', 'Amiri': 'fonts/Amiri-Regular.ttf',
  'Scheherazade New': 'fonts/ScheherazadeNew-Regular.ttf', 'KFGQPC Uthmanic Hafs': 'fonts/UthmanicHafs1Ver18.ttf',
};
const PX = 48;
let s = Number(process.argv[3] || 11);
const rnd = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; };

function layout(font, text) {
  const run = font.layout(text);
  let x = 0;
  const items = [];
  run.glyphs.forEach((g, i) => {
    const p = run.positions[i];
    const d = g.path.toSVG();
    if (d.length) items.push({ d, x: x + p.xOffset, y: p.yOffset });
    x += p.xAdvance;
  });
  return { items, adv: x, key: items.map((o) => o.d + '@' + o.x + ',' + o.y).sort().join('|') };
}

function svg(font, L, width) {
  const k = PX / font.unitsPerEm;
  const asc = font.ascent * k, desc = -font.descent * k;
  const H = Math.ceil(asc + desc + 2 * PX);
  const W = Math.ceil(width * k + 2 * PX);
  const g = L.items.map((o) => `<path transform="translate(${PX + o.x * k} ${PX + asc - o.y * k}) scale(${k} ${-k})" d="${o.d}"/>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><rect width="100%" height="100%" fill="#fff"/><g fill="#000">${g}</g></svg>`;
}

const perCell = Number(process.argv[2] || 40);
const pairs = JSON.parse(fs.readFileSync(0, 'utf8'));
let n = 0;
for (const [set, list] of Object.entries(pairs)) {
  for (const [fname, file] of Object.entries(FONTS)) {
    const font = fk.openSync(file);
    const diff = [];
    for (const [a, b] of list) {
      const A = layout(font, a), B = layout(font, b);
      if (A.key !== B.key) diff.push([A, B]);
    }
    for (let i = diff.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [diff[i], diff[j]] = [diff[j], diff[i]]; }
    diff.slice(0, perCell).forEach(([A, B]) => {
      const w = Math.max(A.adv, B.adv);
      process.stdout.write(JSON.stringify({ set, font: fname, a: svg(font, A, w), b: svg(font, B, w) }) + '\n');
      n++;
    });
  }
}
console.error('svg pairs', n);
