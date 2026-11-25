// Builds the IMAN 2026 paper (.docx) following the IMAN author instructions.
// All numbers are read from ../results/all_numbers.json produced by the experiments.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType,
  WidthType, BorderStyle, TabStopType, ShadingType, VerticalAlign, HeightRule,
} = require("docx");

const R = JSON.parse(fs.readFileSync(path.join(__dirname, "../results/all_numbers.json"), "utf8"));
const TNR = "Times New Roman", ARIAL = "Arial", AR = "Simplified Arabic";
const W = 9026; // text width in DXA (A4, 1-inch margins)
const fmt = (x, d = 0) => Number(x).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (a, b, d = 1) => fmt((100 * a) / b, d);

// ---------------------------------------------------------------- helpers
function runs(text, base = {}) {
  // light inline markup: *italic*, ^sup^, _sub_ (sub only for simple tokens)
  const out = [];
  const re = /(\*[^*]+\*|\^[^^]+\^|~[^~]+~)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const tok = m[0];
    if (tok[0] === "*") out.push(new TextRun({ text: tok.slice(1, -1), italics: true, ...base }));
    else if (tok[0] === "^") out.push(new TextRun({ text: tok.slice(1, -1), superScript: true, ...base }));
    else out.push(new TextRun({ text: tok.slice(1, -1), subScript: true, ...base }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const body = (text, opt = {}) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 100, line: 240 },
  children: runs(text, { font: TNR, size: 24 }), ...opt,
});
const h1 = (text) => new Paragraph({
  spacing: { before: 120, after: 160 }, keepNext: true,
  children: [new TextRun({ text, bold: true, font: TNR, size: 24 })],
});
const h2 = h1;
const bullet = (text) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 80 }, indent: { left: 360, hanging: 360 },
  children: runs(text, { font: TNR, size: 24 }),
});
const eq = (expr, n) => new Paragraph({
  spacing: { before: 100, after: 100 },
  tabStops: [{ type: TabStopType.CENTER, position: W / 2 }, { type: TabStopType.RIGHT, position: W }],
  children: [new TextRun({ text: "\t", font: TNR, size: 24 }), ...runs(expr, { font: TNR, size: 24 }),
    new TextRun({ text: `\t(${n})`, font: TNR, size: 24 })],
});
const tcap = (text) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 120, after: 80 }, keepNext: true,
  children: runs(text, { font: TNR, size: 24 }),
});
const fcap = (text) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
  children: runs(text, { font: TNR, size: 24 }),
});
const fig = (file, wpx, hpx) => new Paragraph({
  alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(__dirname, "../figs", file)),
    transformation: { width: wpx, height: hpx } })],
});
const figcap = (file, wpx, hpx, caption) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 120, after: 160 }, keepLines: true,
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(__dirname, "../figs", file)),
    transformation: { width: wpx, height: hpx } }), new TextRun({ text: "", break: 1 }),
    ...runs(caption, { font: TNR, size: 24 })],
});
const thin = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function table(widths, rows, headRows = 1, fs_ = 19, allLeft = false, keepAll = false) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
    rows: rows.map((r, i) => new TableRow({
      cantSplit: true, tableHeader: i < headRows,
      children: r.map((c, j) => new TableCell({
        width: { size: widths[j], type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
        margins: { top: 30, bottom: 30, left: 70, right: 70 },
        borders: {
          top: i === 0 ? thin : none, bottom: (i === headRows - 1 || i === rows.length - 1) ? thin : none,
          left: none, right: none,
        },
        children: [new Paragraph({
          keepNext: keepAll ? i < rows.length - 1 : i < headRows,
          alignment: (j === 0 || allLeft) ? AlignmentType.LEFT : AlignmentType.CENTER,
          children: runs(String(c), { font: TNR, size: fs_ }),
        })],
      })),
    })),
  });
}
const gap = () => new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: "", font: TNR, size: 12 })] });
const blank = () => new Paragraph({ children: [new TextRun({ text: "", font: TNR, size: 24 })] });

