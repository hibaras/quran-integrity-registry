// ---------------------------------------------------------------- numbers
const D = R.derived, E1 = R.e1, N = E1.n_trials, NV = 6236;
const get = (op, m) => E1.rows.find((r) => r.operator === op && r.method === m);
const FAM = {
  "Letter and word (5 operators)": ["Letter substitution", "Letter deletion", "Letter insertion", "Word deletion", "Adjacent-word swap"],
  "Diacritic (3 operators)": ["Vowel substitution", "Diacritic deletion", "Diacritic insertion"],
  "Encoding-level (3 operators)": ["Homoglyph substitution", "Invisible-character insertion", "Bidi-control insertion"],
  "Verse deletion": ["Verse deletion"], "Verse insertion (duplicate)": ["Verse insertion (duplicate)"],
  "Verse swap within a chapter": ["Verse swap (within chapter)"],
};
const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
const pc = (x) => (x === 1 ? "100" : x === 0 ? "0" : fmt(100 * x, x > 0.999 ? 2 : 1));
const famVal = (ops, m, key) => mean(ops.map((o) => get(o, m)[key]));
const benign = E1.benign;
const RN = R.render_nfc;
const e3 = R.e3, e4 = R.e4, e5 = R.e5;
const cmp = (p) => e3.comparisons.find((c) => c.pair === p);
const uq = cmp("Tanzil Uthmani vs KFGQPC Hafs"), um = cmp("Tanzil Uthmani vs Tanzil Uthmani-min"),
  sc = cmp("Tanzil Simple vs Tanzil Simple-clean"), us = cmp("Tanzil Uthmani vs Tanzil Simple");
const dq = e3.diagnosis_vs_tanzil_registry["KFGQPC Hafs"];
const t2 = e3.table2;
const H = R.heldout;
const at = e4.attacks, fe = e4.feasibility, vf = e4.visual_forgeries, vp = e4.visual_pairs;
const sfx = e4.suffix, sfxv = e4.suffix_pixel_identical;
const loc = e5.localisation;
const costIn = Object.entries(E1.cost).filter(([k]) => !k.startsWith("Verse")).map(([, v]) => v);
const hIn = mean(costIn.map((c) => c.hashes_mean)), bIn = mean(costIn.map((c) => c.bytes_mean));
const bInMax = Math.max(...costIn.map((c) => c.bytes_max));
const del = E1.cost["Verse deletion"];
const ci = (a) => `95% CI ${fmt(a[0], 2)}–${fmt(a[1], 2)}%`;
const clsPct = pct(D.cls_ok, D.n_trials, 2), exactPct = pct(D.exact_ok, D.n_trials, 2);
const fonts5 = ["Noto Naskh Arabic", "Amiri", "Scheherazade New", "Amiri Quran", "KFGQPC Uthmanic Hafs"];
const allSfx = fonts5.every((f) => sfxv[f] === sfx.crc_collision);
const ms = (o) => fmt(o.median_ms, o.median_ms < 1 ? 3 : 1);
const msIqr = (o) => `${ms(o)} (${fmt(o.q1_ms, 1)}–${fmt(o.q3_ms, 1)})`;
const us_ = (o) => fmt(1000 * o.median_ms, 0);
const F6 = R.e6.copies, FK = R.e7.sets, FKR = R.e7_raster;
const REFN = { uthmani: "Uthmani", "uthmani-min": "Uthmani-min", simple: "Simple", "simple-clean": "Simple-clean", "qpc-hafs": "KFGQPC Hafs" };
const COPYN = { "api-uthmanihaf": "API Uthmani Hafs", "api-simple": "API Simple", "api-academy": "API Quran Academy",
  "api-indopak": "API IndoPak", "api-khaledhosn": "API Khaled Hosney", "api-uthmanihaf1": "API Hafs, no diacritics",
  "api-spelled": "API Spelled", "npm-quran": "npm quran", "npm-quran-cloud": "npm quran-cloud", "npm-muslims": "npm @muslims-community/quran" };
const nFlag = F6.filter((c) => c.mismatch_flag).length, nAcc = F6.filter((c) => c.accepted).length;
const cpN = (id, cp) => (f6(id).invisible_by_cp[cp] || f6(id).nonascii_space_by_cp[cp] || f6(id).out_of_profile_by_cp[cp] || 0);
const f6 = (id) => F6.find((c) => c.id === id);
const fk4 = ["Noto Naskh Arabic", "Amiri", "Scheherazade New", "KFGQPC Uthmanic Hafs"];
const fkDiff = (set, f) => FK[set].pairs - FK[set].fonts[f].ink_identical;
const fkPct = (set, f) => pct(fkDiff(set, f), FK[set].pairs, 1);
const rasterAll = Object.values(FKR).every((v) => v.pixel_different === v.sampled);
const rasterN = Object.values(FKR).reduce((a, v) => a + v.sampled, 0);
const T3 = D.t3_cells_below_100;

// ---------------------------------------------------------------- front matter
const placeholder = (t, size, font = ARIAL, bold = false) => new TextRun({ text: t, font, size, bold, highlight: "yellow" });
const front = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: "Unicode-Aware, Position-Bound Integrity Verification of Digital Quran Text with a Signed Two-Level Merkle Registry", font: ARIAL, size: 32, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [placeholder("[First Author]", 28), new TextRun({ text: "1,a", font: ARIAL, size: 28, superScript: true }),
      new TextRun({ text: ", ", font: ARIAL, size: 28 }), placeholder("[Second Author]", 28),
      new TextRun({ text: "2,b", font: ARIAL, size: 28, superScript: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "1", font: ARIAL, size: 22, superScript: true }),
    placeholder("[Department, University of Technology, Baghdad, Iraq]", 22)] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "2", font: ARIAL, size: 22, superScript: true }),
    placeholder("[Full address of second author, including country]", 22)] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [
    new TextRun({ text: "a", font: ARIAL, size: 22, superScript: true }), placeholder("[email]", 22),
    new TextRun({ text: ", ", font: ARIAL, size: 22 }), new TextRun({ text: "b", font: ARIAL, size: 22, superScript: true }),
    placeholder("[email]", 22)] }),
  new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: "Abstract", bold: true, font: TNR, size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 160 }, children: runs(
    `Digital copies of the Quran pass through apps, websites and open datasets, and a single altered letter, diacritic or verse position can change the meaning of a verse. Most integrity checks compare bytes, yet Unicode can store the same visible verse in several ways. We propose a scheme that brings each verse to Unicode Normalization Form C (NFC), binds it to its chapter and verse number in a two-level Merkle tree with an Ed25519-signed root, and labels each detected change as encoding-level, diacritic-level, letter-level or structural. Detection needs only a ${e5.detection_only_bytes}-byte signed statement, and the data used to locate a change can come from any untrusted server because every item is authenticated on arrival. On the Tanzil Uthmani text (6,236 verses), the scheme located the change exactly in ${exactPct}% of ${fmt(D.n_trials)} copies tampered by 14 operators and classified it correctly in ${clsPct}%. Ablations show that this accuracy comes from NFC and verse alignment; the signed tree reduces what verifiers hold and fetch. Converting the text to NFC changed the bytes of ${fmt(benign.NFC.verses_changed_bytes)} verses and all ${benign.NFC.headers_changed_bytes} basmala headers without changing a pixel rendered by HarfBuzz in five fonts, yet raw per-verse hash tables flagged them all. A second shaping engine, however, drew ${fkPct("NFC", "Noto Naskh Arabic")}–${fkPct("NFC", "Amiri")}% of the changed words differently in three of four fonts, so applications should display the text exactly as published. An independent King Fahd Complex encoding differed from the Tanzil text in ${fmt(uq.raw)} verses but in the folded letter skeleton of only ${uq.sigma_star}. None of ten copies distributed through a public Quran API and npm packages matched any of the five registries: most were other editions or versions, some carried invisible characters, Farsi yeh or decomposed marks, and one matched every verse but lacked the basmala headers. Registries must therefore be published per edition and encoding. Finally, per-verse CRC-32 tables accepted all ${sfx.crc_collision} vowel edits that we compensated with 32 appended invisible characters, which left no visible trace in any font that either engine could render.`,
    { font: TNR, size: 22 }) }),
  new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 240 }, children: [
    new TextRun({ text: "Keywords: ", bold: true, font: TNR, size: 22 }),
    new TextRun({ text: "Quran text integrity, Unicode normalization, Merkle tree, homoglyph attack, tamper localization, digital signature", bold: true, font: TNR, size: 22 })] }),
];

// ---------------------------------------------------------------- 1 Introduction
const intro = [
  h1("1. Introduction"),
  body("The Quran is now read daily on phones, websites, application programming interfaces (APIs) and open datasets, and each of these channels copies, converts and re-serves the text. Since one letter or diacritic can change the meaning of a verse, keeping digital copies intact is a recognised research problem (Hakak et al., 2017), approached with hashing, string matching, watermarking, certification and blockchain ledgers (Section 2). Large language models add urgency: the IslamicEval 2025 shared task measured how well systems detect and correct misquoted verses in model output (Mubarak et al., 2025)."),
  body("Hash-based verification is exact and easy to audit, but it compares byte strings, and in Unicode what a reader sees is not always what a program compares. The marks of one visible verse can be stored in different, canonically equivalent orders (Whistler, 2024). Independent editions of the same printed Mushaf use different code points. An attacker can insert invisible characters or swap in look-alike letters, tricks that have fooled both human reviewers and software (Boucher & Anderson, 2023; Boucher et al., 2022). Raw-byte checks can thus raise false alarms after harmless re-encoding, weak checksums can accept altered text, and lookups that ignore position accept deleted, duplicated or reordered verses."),
  body("Our aim is a check that ignores canonically equivalent re-encoding but catches every other change, says where it is and what kind it is, and lets anyone verify one verse or a whole copy against a small signed value without trusting the server that supplies the data. We make four contributions: (1) a position-bound, two-level Merkle registry over NFC-canonical verses with a signed root, authenticated retrieval from untrusted mirrors and a diagnosis derived from Unicode data files; (2) an evaluation with ablations, held-out manipulations and rendering checks in two shaping engines; (3) a measurement of how far independent encodings of the Madinah Mushaf diverge, and a field test on ten distributed copies; and (4) evidence from five fonts, two of them Mushaf fonts, that per-verse CRC-32 tables can be forged invisibly."),
];

// ---------------------------------------------------------------- 2 Related work
const litRows = [
  ["Study", "Technique", "Evaluation and reported result"],
  ["Alginahi et al. (2013)", "Verifies verses quoted on websites", "Quoted verses verified"],
  ["Alshaikhli & Alahmad (2013)", "SAB hash of the Quran text", "Integrity protection"],
  ["Tayan et al. (2014)", "Zero-watermarking and signature", "Detects and locates tampering"],
  ["Khan et al. (2017)", "Certifier and religious panel", "Certification framework"],
  ["Hakak et al. (2018)", "XOR residual to plain text", "87.1% accuracy (multi-style)"],
  ["Almazrooie, Samsudin, Gutub, et al. (2020)", "Per-verse SHA-256 and RIPEMD-160 tables, compressed", "Tables 84.73% and 90.46% smaller"],
  ["Almazrooie, Samsudin, Omar, et al. (2020)", "GPU collision attack on 32-bit verse hash tables", "Readable second preimages; 395-fold GPU speed-up"],
  ["Alkhafaji et al. (2021)", "Kashida watermarking, XOR, queuing", "Tamper detection, localisation"],
  ["Touati-Hamad et al. (2021)", "Blockchain, Merkle tree per surah", "Preservation model"],
  ["Kazmi et al. (2024)", "SHA-3 key in zero-width spaces", "Robust to tampering attacks"],
  ["Elnawasany (2026), preprint", "Uthmani-to-Standard word mapping", "90.9% of verses identical"],
  ["Zita et al. (2026), preprint", "Hierarchical hashes, signed records", "Selected chapters, variants"],
  ["This study (2026)", "NFC, signed two-level Merkle tree", `${exactPct}% exact; 10 field copies`],
];
const related = [
  h1("2. Related Work"),
  body("Table 1 lists representative studies in chronological order, as reported by their authors. Hashing schemes were presented at this conference series in 2013 (Alshaikhli & Alahmad, 2013). Almazrooie, Samsudin, Omar, et al. (2020) later forged readable second preimages for 32-bit verse hash tables using special Unicode characters. Touati-Hamad et al. (2021) stored surahs on a blockchain with a Merkle tree, and Kazmi et al. (2024) hid watermark bits in zero-width characters, so invisible characters can carry tampering too. The closest work is in two recent preprints: Elnawasany (2026) measured the gap between Uthmani and Standard forms, and Zita et al. (2026) combined canonical normalisation with hierarchical hashing and signed records."),
  tcap("Table 1: Representative studies on the integrity of digital Quranic text in chronological order, as reported by their authors"),
  table([2700, 3400, 2926], litRows, 1, 20, true),
  gap(),
  body("Our scheme differs in three ways. It binds every verse to its position under one signed root, so any item fetched from an untrusted server is authenticated; it derives its diagnosis from Unicode data; and is tested on a full edition, ten distributed copies and two shaping engines."),
];

// ---------------------------------------------------------------- 3 Methodology
const t2rows = [["Edition (source)", "Code points", "Distinct (raw / NFC)", "Basmala split off", "Changed by NFC"],
  ...["Tanzil Uthmani", "Tanzil Uthmani-min", "Tanzil Simple", "Tanzil Simple-clean", "KFGQPC Hafs"].map((k) => [
    k === "Tanzil Uthmani" ? "Tanzil Uthmani (reference)" : k === "KFGQPC Hafs" ? "KFGQPC Hafs (via Qur'anpedia)" : k,
    fmt(t2[k].code_points), `${t2[k].distinct} / ${t2[k].distinct_after_nfc}`, fmt(t2[k].basmala_headers), fmt(t2[k].verses_changed_by_nfc)])];
const method = [
  h1("3. Methodology"),
  h2("3.1 Threat model"),
  body("We assume that a publisher, ideally a recognised scholarly body, signs one statement per edition and version with an offline key, and that verifiers hold the public key, for instance pinned in an application. The adversary can modify any distributed copy (edit letters, diacritics and words; insert invisible or bidirectional control characters; substitute look-alike letters; delete, duplicate or reorder verses), control the mirrors that serve tree nodes and texts, and replay an older statement. Harmless processes may also re-normalise a correct text. The scheme must detect every change that is not canonically equivalent, accept every equivalent copy, report where and what changed, and reject any altered item from a mirror. Rollback is discussed in Section 5; fonts, images and audio are out of scope."),
  h2("3.2 Data"),
  body("All texts come from snapshots of the repository *quran-json* (risan, 2026; commit 6523a9a, 1 October 2026). Its checksums matched, confirming the snapshot, not its fidelity to the publishers' releases. Our reference is the Tanzil Uthmani text (Tanzil Project, n.d.), an encoding of the Madinah Mushaf; the KFGQPC Hafs text came through Qur'anpedia (n.d.). Four editions prefix the basmala to verse 1 of every chapter except 1 and 9 (Table 2). We split it off at the fourth space of the raw text as a separate item, verse 0, keeping both parts byte for byte, so verse numbers follow the Mushaf and the basmala stays protected (6,348 items). Unicode data are version 15.1.0 (Unicode Consortium, 2023), as in Python 3.13; normalisation stability keeps their NFC unchanged in later versions (Whistler, 2024). Tampered copies existed only in memory. The field test used ten copies as distributed on 11 November 2026: seven Arabic Hafs editions of the *quran-api* dataset (Unlicense), served through a CDN (Ahmed, 2026; commit 93e6f64; a tafsir and a duplicate excluded), and the Arabic text of npm packages quran 0.0.9, quran-cloud 1.0.0 and @muslims-community/quran 1.1.0."),
  tcap("Table 2: Editions used in the experiments (114 chapters and 6,236 verses each)"),
  table([2826, 1400, 1700, 1400, 1700], t2rows, 1, 20, false, true),
  gap(),
  h2("3.3 Canonical and diagnostic views"),
  body("Each verse text *t* is mapped to a canonical form *κ*(*t*) (Equation 1): we apply Normalization Form C and then trim leading and trailing ASCII white space (U+0020, U+0009, U+000A, U+000D), nothing else. NFC gives canonically equivalent sequences, such as a shadda and a fatha stored in either order, one representation (Whistler, 2024). Every other character, including a no-break space at the end of a verse, is kept and therefore detected. The profile *P* holds the 63 code points of the canonical reference edition, one more than the raw text because NFC composes U+0622."),
  eq("κ(t) = trimASCII(NFC(t))", 1),
  body("For diagnosis only, we compute a letter skeleton *σ*(*t*) (Equation 2). The canonical text is decomposed (NFD); combining marks, default-ignorable code points, tatweel, the small letters U+06E5 and U+06E6 and the signs U+06DE and U+06E9 are removed; alef wasla becomes alef; and spaces are collapsed. Since NFD separates hamza above and below from their carriers, *σ* treats hamza as a mark; Sections 4.1 and 4.3 test keeping it as a letter. A folded skeleton *σ*~f~ also maps alef maksura to yeh and only compares editions; neither affects acceptance."),
  eq("σ(t) = fold(strip(NFD(κ(t))))", 2),
  h2("3.4 Two-level Merkle registry"),
  body("Each verse *v* of chapter *c* becomes a leaf hash that ties its position to its canonical text (Equation 3), where ⟨·⟩~k~ is a *k*-byte big-endian integer and || denotes concatenation. Internal nodes follow the domain-separated construction of Certificate Transparency (Laurie et al., 2021) in Equation 4; the prefixes 0x00 and 0x01 ensure that a leaf can never be read as a node."),
  eq("ℓ~c,v~ = H(0x00 || ⟨c⟩~2~ || ⟨v⟩~2~ || UTF8(κ(t~c,v~)))", 3),
  eq("node(L, R) = H(0x01 || L || R)", 4),
  body(`A Merkle tree over the leaves of each chapter gives a chapter root *R*~c~, and the record *ρ*~c~ = ⟨c⟩~2~ || ⟨n~c~⟩~2~ || *R*~c~ becomes a leaf of the edition tree, whose root is *R*. The publisher signs a ${e5.ed25519.statement_bytes}-byte statement (Equation 5). The edition identifier *e*, version *u*, hash name *a* and Unicode data version *w* each carry a one-byte length prefix, so no two field combinations share an encoding; the SHA-256 digest of the profile *P* and the root *R* follow, which lets mirrors serve *P* safely. We use SHA-256 (National Institute of Standards and Technology, 2015) and 64-byte Ed25519 signatures (Bernstein et al., 2012). A single-verse proof holds the chapter audit path, the chapter root and the edition audit path (Laurie et al., 2021).`),
  eq("s = Sign~sk~(\"QIR2\" || ⟨|e|⟩~1~ || e || ⟨|u|⟩~1~ || u || ⟨|a|⟩~1~ || a || ⟨|w|⟩~1~ || w || H(P) || R)", 5),
  figcap("fig1_architecture.png", 430, 220, "Figure 1. Publisher, untrusted mirror and verifier (Sections 3.4 and 3.5)."),
  h2("3.5 Verification, localisation and diagnosis"),
  body("To check a copy, the verifier parses and canonicalises it, recomputes the edition root and compares it with the signed statement. If the roots match, the copy is accepted, and that is all detection requires. If not, the verifier walks down the tree: for each differing node it fetches the two child hashes from a mirror and checks that they hash to the parent it has already authenticated, so *k* changed leaves among *n* cost about *k*·log~2~(*n*/*k*) fetched hashes. Chapter records and the reference texts of located verses are checked against their authenticated leaves in the same way. When a chapter's verse count differs, the verifier fetches that chapter's texts, checks them against *R*~c~ and aligns the two verse sequences on *σ*~f~, so even a copy in another encoding is paired verse by verse. Each located change is then labelled by these rules, in order:"),
  bullet("1)\tStructural (S): alignment yields deleted or inserted verses; a located verse whose text equals the reference text of another located verse is relocated."),
  bullet("2)\tEncoding-level (U): the candidate contains a code point outside *P*, a default-ignorable code point or a bidirectional control. A repair removes default-ignorable code points and maps each out-of-profile character to its NFKC form or to the profile letter with the same prototype in the Unicode confusables data (Davis & Suignard, n.d.); as those data conflate yeh and alef maksura, Farsi yeh maps to yeh when joined and to alef maksura when final. If the repair restores the reference text the change is U; otherwise the remainder is classified by rule 3 or 4 (U+D or U+L)."),
  bullet("3)\tDiacritic-level (D): the canonical texts differ but their skeletons *σ* are equal."),
  bullet("4)\tLetter-level (L): the skeletons differ."),
  body("A U label describes what changed in the encoding, not whether a reader would notice it. If more than half of a copy's verses are flagged and most findings are encoding-level, the copy is reported as another encoding; this flag never changes acceptance."),
  h2("3.6 Experimental design"),
  body(`*Experiment 1 (tampering).* We applied fourteen operators (Table 3) ${fmt(N)} times each (seed 2026) and ran the proposed scheme with four further seeds. Homoglyph substitution replaced U+064A with U+06CC, or U+0643 with U+06A9, in connected positions; invisible insertion used U+200B, U+200C, U+200D, U+2060 or U+FEFF; bidirectional insertion used U+202E, U+2067, U+200F or U+061C; and verse deletion and duplicate insertion renumbered the rest of the chapter. The baselines were B1, one SHA-256 digest of the whole file; B2, a position-bound per-verse CRC-32 table (Almazrooie, Samsudin, Gutub, et al., 2020); B3, the same table with SHA-256 over raw bytes; and B4, an existence check of each verse digest, which is all a verifier can do when a quoted verse's position is unknown. Two ablations isolate our components: B3n computes B3 on NFC text, and B3n+A adds our verse alignment. We report detection, exact localisation and classification accuracy with exact (Clopper-Pearson) 95% intervals. In 1,000 further copies we changed one vowel in a basmala header (verse 0), and in 1,000 more trials the mirror returned one altered node, chapter record, verse text or profile. Withheld data simply halts verification; stale data is the rollback case of Section 5.`),
  body(`*Held-out manipulations* test the rules on cases the operators did not shape. In 1,000 copies we inserted one default-ignorable code point other than the nine above (H1; ${H.dicp_pool} candidates), and in another 1,000 we substituted a code point with the same confusable prototype, excluding the two homoglyph pairs (H2; ${H.sub_pool} candidates). Each copy was labelled by the original rules (three confusable pairs, format characters only) and by the revised ones, and the affected word was rendered. Since the generator and the revised rules read the same data files, what matters is the comparison with the original rules and the visibility counts.`),
  body("*Experiment 2* converted the whole edition to NFC, NFD and NFKC and rendered every changed word before and after. We used HarfBuzz shaping (Pillow, libraqm) in five fonts: Noto Naskh Arabic, Amiri 1.000, Scheherazade New, and the Mushaf fonts Amiri Quran 1.000 and KFGQPC Uthmanic Hafs 0.18. The same pairs, and those of Experiment 4, were also laid out with fontkit 2.0.4 (Govett, 2024), which has its own OpenType layout. Two strings counted as identical if they gave the same glyph outlines at the same positions, and up to 40 differing pairs per font and set were rasterised to confirm. *Experiment 3* compared the editions on raw bytes, canonical text, *σ* and *σ*~f~, and verified each against the Tanzil registry. *Experiment 4.* For equal-length inputs CRC-32 is affine over GF(2) (Stigge et al., 2006), so an attacker who edits verse *m* into *m*′ can look for a set *S* of length-preserving, visually neutral edits whose byte differences *δ*~j~ cancel the CRC change (Equation 6). We tried P1 (U+064A to U+06CC) and P2 (U+0643 to U+06A9) in connected positions, P3 (U+0649 to U+06CC) in final positions, and P4, a canonically equivalent swap of two adjacent marks of different combining classes. A rule was kept if 300 random single substitutions rendered pixel-identically (48 px) in one font, Noto Naskh Arabic, and then measured in the other four. We solved Equation 6 by Gaussian elimination for 1,000 random vowel or letter edits; letter edits excluded yeh, kaf and alef maksura, which carry P1–P3. A second construction changed one vowel in each of 300 random verses and appended 32 characters, each U+2062 or U+2063."),
  eq("⊕~j∈S~ [CRC(δ~j~) ⊕ CRC(0^|m|^)] = CRC(m′) ⊕ CRC(m)", 6),
  body(`*Experiment 5* timed each operation (medians and interquartile ranges over 10–200 repetitions) and measured localisation for 1 to 256 tampered verses (100 runs each), in Python ${e5.platform.python} on two vCPUs (Intel Xeon, 2.10 GHz). *Experiment 6* compared each copy with the five editions under the four views and verified it against the registry with the most canonically equal verses.`),
];

// ---------------------------------------------------------------- 4 Results
const methods = ["B2", "B3", "B4", "B3n", "B3n+A", "Proposed"];
const t3rows = [["Operators (trials)", "B2", "B3", "B4", "B3n", "B3n+A", "Scheme", "Scheme, class"]];
for (const [lab, ops] of Object.entries(FAM)) {
  t3rows.push([`${lab} (${fmt(ops.length * N)})`, ...methods.map((m) => pc(famVal(ops, m, "exact_loc"))),
    pc(famVal(ops, "Proposed", "class_acc"))]);
}
const b4struct = ["Verse deletion", "Verse insertion (duplicate)", "Verse swap (within chapter)"].map((o) => get(o, "B4").detect);
const t4rows = [["Edition pair", "Raw bytes", "NFC (*κ*)", "Skeleton *σ*", "Folded *σ*~f~"],
  ...[[uq, "Tanzil Uthmani vs KFGQPC Hafs"], [um, "Tanzil Uthmani vs Uthmani-min"], [sc, "Tanzil Simple vs Simple-clean"],
    [us, "Tanzil Uthmani vs Simple"]].map(([c, l]) => [l, fmt(c.raw), fmt(c.canonical), fmt(c.sigma), fmt(c.sigma_star)]),
  ["*Distributed copy vs closest reference*", "", "", "", ""],
  ...F6.map((c) => { const m = c.match[c.closest];
    return [`${COPYN[c.id]} vs ${REFN[c.closest]}`, fmt(m.shared - m.raw), fmt(m.shared - m.canonical), fmt(m.shared - m.sigma), fmt(m.shared - m.sigma_star)]; })];
const vpct = (x) => fmt(100 * x, x === 1 || x === 0 ? 0 : 1);
const t5rows = [["Font", "P1", "P2", "P3", "P4", "Subst. forgeries", "Suffix forgeries"],
  ...fonts5.map((f) => [f === "Noto Naskh Arabic" ? "Noto Naskh Arabic (selection)" : f, vpct(vp.P1[f]), vpct(vp.P2[f]),
    vpct(vp.P3[f]), vpct(vp.P4[f]), `${vf[f].pixel_identical}/${vf[f].rendered}`, `${sfxv[f]}/${sfx.crc_collision}`])];
const t6rows = [["Operation (whole edition unless stated)", "Median time (IQR)", "Size"],
  ["Per-verse table, CRC-32 / SHA-256 (raw bytes)", `${ms(e5.table.crc32)} / ${ms(e5.table.sha256)} ms`, `${fmt(e5.storage_bytes.crc32_table)} / ${fmt(e5.storage_bytes.sha256_table)} B`],
  ["Publisher: registry, profile and statement (SHA-256)", `${msIqr(e5.registry_build.sha256)} ms`, `${e5.storage_bytes.signed_statement} B statement + signature`],
  ["Full verification of an intact copy (rebuild and signature check)", `${msIqr(e5.full_verify_intact)} ms`, "-"],
  ["Single-verse proof: generate / verify", `${fmt(e5.proofs.gen_us_per_verse, 1)} / ${fmt(e5.proofs.verify_us_per_verse, 1)} µs`, `${e5.proofs.bytes_min}–${e5.proofs.bytes_max} B (mean ${fmt(e5.proofs.bytes_mean, 0)})`],
  ["Data fetched to localise and diagnose one in-verse change", "-", `mean ${fmt(bIn, 0)} B (max ${fmt(bInMax)})`],
  ["Data fetched for one verse deletion (chapter texts)", "-", `mean ${fmt(del.bytes_mean / 1000, 1)} kB (max ${fmt(del.bytes_max / 1000, 1)})`]];

const results = [
  h1("4. Results"),
  h2("4.1 Detection, localisation and classification"),
  body(`Every method except B4 detected all ${fmt(D.n_trials)} tampered copies. This is expected, because any operator output that survives canonicalisation changes the hashed bytes, so detection tests the implementation rather than the design (lower 95% bound ${fmt(D.detect_lower_per_operator, 2)}% per operator). Table 3 therefore reports exact localisation. The proposed scheme located ${fmt(D.exact_ok)} of ${fmt(D.n_trials)} copies exactly (${exactPct}%, ${ci(D.exact_ci)}); both misses inserted a duplicate next to an identical verse, where either position is correct. After a deletion or insertion, B2, B3 and B3n flagged every renumbered verse, and B4 detected no structural change at all, since every verse still existed somewhere. B3n+A matched the proposed scheme in every row, which shows that canonicalisation and alignment, not the tree, produce these accuracies. A 100% cell in Table 3 has a 95% lower bound of ${fmt(D.t3_lower_100["5000"], 2)}%, ${fmt(D.t3_lower_100["3000"], 2)}% or ${fmt(D.t3_lower_100["1000"], 2)}% for 5,000, 3,000 or 1,000 trials; the two cells below 100% are ${pct(T3[0].k, T3[0].n, 2)}% (${ci(T3[0].ci)}) and ${pct(T3[1].k, T3[1].n, 1)}% (${ci(T3[1].ci)}).`),
  body(`The scheme assigned the correct class in ${fmt(D.cls_ok)} trials (${clsPct}%, ${ci(D.cls_ci)}) and in ${fmt(D.seed_cls_min, 2)}–${fmt(D.seed_cls_max, 2)}% over four further seeds. Seven of the eight errors come from the skeleton convention: replacing a hamza carrier (four cases) or alef wasla (three) with a plain letter was labelled diacritic-level. The eighth swapped two words that differ only in a sukun (26:130). Treating hamza as a letter left ${D.hamza_letter_n - D.hamza_letter_ok} letter-level errors (but see Section 4.3). Locating an in-verse change fetched ${fmt(hIn, 1)} hashes on average over the 11 in-verse operators, plus one chapter record, the profile and one verse text (${fmt(bIn, 0)} bytes). For 1 to 256 changed verses this grew to ${fmt(loc[loc.length - 1].hashes_mean, 0)}, still below the ${fmt(loc[0].table_hashes)} entries of a per-verse table, and localisation was exact in all ${loc[0].runs} runs per size. All ${fmt(E1.verse0.detect)} basmala-header edits were detected, located at verse 0 and labelled D, and all ${fmt(E1.mirror_tamper.rejected)} altered mirror responses were rejected, as authentication guarantees.`),
  tcap("Table 3: Exact localisation (%) per method and classification accuracy (%) of the scheme"),
  table([3426, 700, 700, 700, 700, 850, 900, 1050], t3rows, 1, 20, false, true),
  gap(),
  body(`For the encoding-level operators, correct classification is partly guaranteed by construction, because rule 2 checks exactly the character classes these operators insert. The held-out manipulations address this. The original rules labelled ${H.H1.old.U} of 1,000 default-ignorable insertions and none of 1,000 confusable substitutions as encoding-level; the revised rules labelled ${H.H1.new.U} and ${H.H2.new.U}, and the other ${H.H2.new["U+L"]}, which exchanged yeh and alef maksura forms that the confusable data conflate, as U+L. Encoding-level does not mean invisible: ${H.H1.visible.true} insertions and ${H.H2.visible.true} substitutions changed the rendered word in Noto Naskh Arabic, mostly by breaking joins.`),
  h2("4.2 Benign re-normalisation"),
  body(`Converting the reference edition to NFC changed the bytes of ${fmt(benign.NFC.verses_changed_bytes)} verses (${pct(benign.NFC.verses_changed_bytes, NV)}%) and all ${benign.NFC.headers_changed_bytes} basmala headers; NFD changed ${fmt(benign.NFD.verses_changed_bytes)} verses (${pct(benign.NFD.verses_changed_bytes, NV)}%) and all headers. With HarfBuzz, all ${fmt(RN.NFC.unique_words)} distinct words changed by NFC and all ${fmt(RN.NFD.unique_words)} changed by NFD rendered pixel-identically in all five fonts. B2, B3 and B4 flagged every changed item (${fmt(benign.NFC.B3)} and ${fmt(benign.NFD.B3)}) and B1 rejected the file, while B3n, B3n+A and the proposed scheme flagged nothing. NFKC behaved like NFC.`),
  body(`Pixel identity, however, depends on the engine. HarfBuzz reorders Arabic marks as the Arabic mark rendering algorithm specifies (Pournader et al., n.d.), but fontkit does not; in inspected samples it stacked a vowel that NFC moves before a shadda in reverse order (${fmt(D.nfc_shadda_fatha_words)} changed words contain a fatha moved this way). Its ink differed for ${fkPct("NFC", "Noto Naskh Arabic")}%, ${fkPct("NFC", "Amiri")}% and ${fkPct("NFC", "KFGQPC Uthmanic Hafs")}% of the ${fmt(FK.NFC.pairs)} NFC-changed words in Noto Naskh Arabic, Amiri and KFGQPC Uthmanic Hafs, but for only ${fkPct("NFC", "Scheherazade New")}% in Scheherazade New (NFD: ${fkPct("NFD", "Scheherazade New")}–${fkPct("NFD", "Amiri")}%). ${rasterAll ? `All ${rasterN} rasterised samples of differing pairs were also pixel-different` : "Most rasterised samples were also pixel-different"}, and fontkit failed on nearly every Amiri Quran string. Canonical equivalence is thus a property of the text, not of every renderer. The scheme accepts such copies by design, so applications should display the publisher's bytes and use *κ* only to verify.`),
  h2("4.3 Encoding divergence between editions and distributed copies"),
  body(`Table 4 compares the editions after the basmala split. Tanzil Uthmani and KFGQPC Hafs, two encodings of the same Madinah Mushaf, differed in the bytes of ${fmt(uq.raw)} verses (${pct(uq.raw, NV)}%), and NFC did not help, because KFGQPC uses ${e3.qpc_out_of_profile.length} code points outside the Tanzil profile, such as U+06E1 for sukun. Their skeletons *σ* differed in ${fmt(uq.sigma)} verses, almost entirely because Tanzil writes alef maksura where KFGQPC writes yeh. Under *σ*~f~ only ${uq.sigma_star} verses remain (${e3.residual_uthmani_vs_qpc.ids.join(", ")}): three differ in word spacing and 2:72 in hamza encoding. Keeping hamza as a letter raises this residual to ${e3.hamza_as_letter.uthmani_vs_qpc_sigma_star} verses, since the editions encode hamza differently; hence *σ* treats it as a mark. Against the Tanzil registry, the KFGQPC copy was rejected and reported as another encoding, with ${fmt(dq.flagged)} findings (${fmt(dq.labels["U+D"])} U+D, ${fmt(dq.labels["U+L"])} U+L, ${dq.labels["S-del"]} absent headers, ${dq.labels.L} L, ${dq.labels.D} D).`),
  tcap("Table 4: Number of verses (of 6,236) that differ between editions, and between each distributed copy and its closest reference, under each view"),
  table([4426, 1150, 1150, 1150, 1150], t4rows, 1, 20, false, true),
  gap(),
  body(`No distributed copy matched any of the five registries, and most are editions, versions or encodings for which we had none. For four copies the closest reference matched fewer than 8% of the verses canonically (IndoPak ${f6("api-indopak").match["uthmani"].canonical}, Quran Academy ${f6("api-academy").match["qpc-hafs"].canonical}, Khaled Hosney ${f6("api-khaledhosn").match["qpc-hafs"].canonical}, Hafs without diacritics ${f6("api-uthmanihaf1").match["simple-clean"].canonical}), so it serves only as a yardstick. npm @muslims-community/quran matched Tanzil Uthmani-min in all 6,236 verses but stores no basmala headers, which the registry protects as verse 0 (${f6("npm-muslims").labels["S-del"]} S-del findings); such copies need a registry without headers. npm quran 0.0.9 (2019) differed from the current Tanzil Uthmani in ${f6("npm-quran").findings} verses. In ${f6("npm-quran").sigma_star_hamza_reencoding_only} of its ${f6("npm-quran").labels.L} L verses the only letter difference is a standalone hamza (U+0621) where Tanzil has tatweel, a vowel and hamza above (U+0640 … U+0654): the same hamza encoded differently, which the hamza convention counts as a letter change. This fits an earlier Tanzil release, but we could not confirm it. npm quran-cloud differed from KFGQPC Hafs in ${fmt(f6("npm-quran-cloud").findings)} verses, mostly in tatweel and spacing (D). The API copies contained U+200F (${fmt(cpN("api-uthmanihaf", "U+200F"))} and ${fmt(cpN("api-indopak", "U+200F"))} times in two copies), U+2060 (${fmt(cpN("api-khaledhosn", "U+2060"))} in a third), Farsi yeh for yeh (${fmt(cpN("api-academy", "U+06CC"))} and ${fmt(cpN("api-khaledhosn", "U+06CC"))} times), no-break and hair spaces, and pause marks that the Tanzil Simple file lacks; ${nFlag} copies were reported as other encodings. Farsi yeh also inflates the skeleton columns: after the scheme's repair step, the *σ*~f~ differences of Quran Academy and Khaled Hosney drop to ${fmt(f6("api-academy").sigma_star_differ_after_repair)} and ${fmt(f6("api-khaledhosn").sigma_star_differ_after_repair)}. The API Uthmani Hafs copy stores its marks in NFD order in ${fmt(f6("api-uthmanihaf").verse_level.copy_verses_in_nfd)} verses, and ${fmt(f6("api-uthmanihaf").canonical_only_equal)} of its verses differ from KFGQPC Hafs only in mark order; a raw-byte table flagged ${fmt(f6("api-uthmanihaf").verse_level.b3_raw_flagged)} of its verses, the scheme ${fmt(f6("api-uthmanihaf").verse_level.kappa_flagged)}. We found no published report of a platform re-normalising Quran text, but this copy shows that such variants circulate, although we cannot tell where its mark order came from.`),
  h2("4.4 Forging CRC-32 without a visible trace"),
  body(`In the selection font all four rules rendered invisibly (Table 5). With homoglyph rules alone, ${fe.full_rank_32_homoglyph_only} verses had the 32 independent edits needed to reach every CRC value; mark reordering raised this to ${fe.full_rank_32} (${pct(fe.full_rank_32, NV, 2)}%), the longest verses. Of 1,000 random edits to these verses, ${at.crc_collision} (${ci(D.crc_ci)}) were compensated, with a median of ${fmt(e4.swaps_median, 0)} substitutions. All ${vf["Noto Naskh Arabic"].rendered} sampled forgeries were pixel-identical to the uncompensated edit in the selection font, but only ${vf.Amiri.pixel_identical}, ${vf["Scheherazade New"].pixel_identical}, ${vf["Amiri Quran"].pixel_identical} and ${vf["KFGQPC Uthmanic Hafs"].pixel_identical} were in the held-out fonts, because the Mushaf fonts draw Farsi yeh and keheh differently or lack them. The suffix construction worked on every tested verse: ${sfx.crc_collision} of ${sfx.attempts} vowel-edited verses kept their CRC-32, and ${allSfx ? "all were pixel-identical to the edited verse in every font" : "most were pixel-identical"}. This extends the readable collisions of Almazrooie, Samsudin, Omar, et al. (2020) to edits with no visible trace; SHA-256 and the scheme rejected every forgery. With fontkit, P1–P3 matched the HarfBuzz rates within one case per font, but outside Scheherazade New most P4 swaps changed the ink (${fk4.map((f) => FK.single_P4.fonts[f].ink_identical).join(", ")} of 300 identical). Only ${fk4.reduce((a, f) => a + FK.compensated.fonts[f].ink_identical, 0)} of ${fmt(4 * FK.compensated.pairs)} substitution forgeries therefore kept their ink, whereas all ${FK.suffix.pairs} suffix forgeries did in all four fonts.`),
  tcap("Table 5: Pixel-identical renders with HarfBuzz (%) of single substitutions P1–P4 (n = 300 each) and of CRC-32 forgeries (count)"),
  table([2826, 650, 650, 650, 650, 1800, 1600], t5rows, 1, 20, false, true),
  gap(),
  h2("4.5 Computational and storage cost"),
  body(`Building the registry, profile and statement took ${msIqr(e5.registry_build.sha256)} ms, and verifying an intact copy (rebuild plus signature) took ${msIqr(e5.full_verify_intact)} ms, ${ms(e5.canonicalise_all)} ms of it for canonicalisation. Raw per-verse CRC-32 and SHA-256 tables took ${ms(e5.table.crc32)} and ${ms(e5.table.sha256)} ms and occupy ${fmt(e5.storage_bytes.crc32_table)} and ${fmt(e5.storage_bytes.sha256_table)} bytes, against ${e5.storage_bytes.signed_statement} bytes for the statement and signature. A single-verse proof took ${fmt(e5.proofs.gen_us_per_verse, 1)} µs to generate and ${fmt(e5.proofs.verify_us_per_verse, 1)} µs to verify and held ${e5.proofs.bytes_min}–${e5.proofs.bytes_max} bytes (mean ${fmt(e5.proofs.bytes_mean, 0)}); all ${fmt(e5.proofs.n)} verified. Locating one in-verse change fetched ${fmt(bIn, 0)} bytes on average (max ${fmt(bInMax)}), and one verse deletion ${fmt(del.bytes_mean / 1000, 1)} kB (max ${fmt(del.bytes_max / 1000, 1)}).`),
];

// ---------------------------------------------------------------- 5 Discussion
const discussion = [
  h1("5. Discussion"),
  body(`Raw-byte methods cannot tell harmless re-encoding from tampering: one normalisation step that changed no pixel under HarfBuzz made ${pct(benign.NFC.verses_changed_bytes, NV)}% of a correct text look tampered. NFC removes these false alarms and verse alignment locates structural changes, so a per-verse table with both (B3n+A) is as accurate as the registry. What the registry adds is a different trust and cost profile. Detection needs one ${e5.detection_only_bytes}-byte signed statement instead of an authenticated ${fmt(e5.storage_bytes.sha256_table / 1000, 0)}-kilobyte table, localisation fetches about ${fmt(hIn, 0)} authenticated hashes per change from any mirror, and a website or API can serve one verse with a proof of at most ${e5.proofs.bytes_max} bytes plus the statement. Binding verses to positions also exposes deletion, duplication and reordering, which matters because 272 verses share their text with another verse, and one text occurs 31 times.`),
  body("A registry is tied to an edition and its encoding. An independent encoding is rejected and reported as another encoding, and no distributed copy matched any registry, so integrity data must be published per edition, version and encoding, and an application must verify against the registry of the text it ships. Integrity decisions should not depend on rendering either, since substitutions invisible in one font or engine were visible in another. Following Khan et al. (2017), the key should belong to a recognised body that reviews each edition, be kept offline and pinned in applications. Rollback can be prevented by publishing the versioned statements in an append-only log, as in Certificate Transparency (Laurie et al., 2021)."),
  body("*Limitations.* We evaluated one reference edition with synthetic tampering. The field test covered ten freely distributed copies, not texts inside installed applications, and cannot tell how their differences arose. Rendering was checked with two engines at one size, and fontkit could not lay out Amiri Quran. Treating hamza and alef wasla as marks is a convention supported by cross-edition data, not by a linguistic authority, so specialists in Mushaf orthography should review it and the four residual verses. The data came from an intermediary, the timings from unoptimised Python, and the scheme cannot decide which edition is authoritative."),
];

// ---------------------------------------------------------------- 6 Conclusion
const conclusion = [
  h1("6. Conclusion"),
  new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 140, line: 240 }, children: [
    ...runs(`This paper presented a canonical, position-bound integrity scheme for digital Quran text. It signs the root of a two-level Merkle tree, authenticates every item fetched from untrusted servers and diagnoses the changes it detects. On the Tanzil Uthmani text it located ${exactPct}% of ${fmt(D.n_trials)} tampered copies exactly, classified ${clsPct}% correctly and raised no false alarm after NFC or NFD conversion. Two independent encodings of the same Mushaf differed in almost every verse, none of ten distributed copies matched any of the five registries, and CRC-32 tables were forged without a visible trace in every font that either of two shaping engines could render. We recommend publishing integrity data per edition, version and encoding; canonicalising with NFC for verification while displaying the published bytes; binding verses to their positions; reporting out-of-profile and invisible characters; and retiring CRC-32. Future work will cover other riwayat, Hadith, texts inside installed applications and an append-only log of statements. Code, data snapshots and result files: `, { font: TNR, size: 24 }),
    new TextRun({ text: "[public repository URL and DOI]", font: TNR, size: 24, highlight: "yellow" }),
    new TextRun({ text: ".", font: TNR, size: 24 })] }),
];

// ---------------------------------------------------------------- references (APA, alphabetical)
const refs = [
  "Ahmed, F. (2026). *quran-api* (Branch 1, commit 93e6f64) [Data set]. GitHub. https://github.com/fawazahmed0/quran-api",
  "Alginahi, Y. M., Tayan, O., & Kabir, M. N. (2013). Verification of Qur'anic quotations embedded in online Arabic and Islamic websites. *International Journal on Islamic Applications in Computer Science and Technology, 1*(2), 41–47.",
  "Alkhafaji, A. A. R., Sjarif, N. N. A., Shahidan, M. A., Azmi, N. F. M., Sarkan, H. M., & Chuprat, S. (2021). Tamper detection and localization for Quranic text watermarking scheme based on hybrid technique. *Computers, Materials & Continua, 68*(1), 77–102. https://doi.org/10.32604/cmc.2021.015770",
  "Almazrooie, M., Samsudin, A., Gutub, A. A.-A., Salleh, M. S., Omar, M. A., & Hassan, S. A. (2020). Integrity verification for digital Holy Quran verses using cryptographic hash function and compression. *Journal of King Saud University – Computer and Information Sciences, 32*(1), 24–34. https://doi.org/10.1016/j.jksuci.2018.02.006",
  "Almazrooie, M., Samsudin, A., Omar, M. A., Salleh, M. S., & Hassan, S. A. (2020). GPGPU-based collision attack on Quranic verses hash tables. *Journal of Mechanics of Continua and Mathematical Sciences*, Special Issue No. 6. https://doi.org/10.26782/jmcms.spl.6/2020.01.00004",
  "Alshaikhli, I. F. T., & Alahmad, M. A. (2013, July 1–2). *Protection of the digital Holy Quran using SAB hash function* [Conference paper]. International Conference on Islamic Applications in Computer Science and Technologies (IMAN 2013), Kuala Lumpur, Malaysia. http://irep.iium.edu.my/30607/",
  "Bernstein, D. J., Duif, N., Lange, T., Schwabe, P., & Yang, B.-Y. (2012). High-speed high-security signatures. *Journal of Cryptographic Engineering, 2*(2), 77–89. https://doi.org/10.1007/s13389-012-0027-1",
  "Boucher, N., & Anderson, R. (2023). Trojan Source: Invisible vulnerabilities. In *Proceedings of the 32nd USENIX Security Symposium* (pp. 6507–6524). USENIX Association.",
  "Boucher, N., Shumailov, I., Anderson, R., & Papernot, N. (2022). Bad characters: Imperceptible NLP attacks. In *2022 IEEE Symposium on Security and Privacy (SP)* (pp. 1987–2004). IEEE. https://doi.org/10.1109/SP46214.2022.9833641",
  "Davis, M., & Suignard, M. (Eds.). (n.d.). *Unicode Technical Standard #39: Unicode security mechanisms*. Unicode Consortium. Retrieved November 10, 2026, from https://www.unicode.org/reports/tr39/",
  "Elnawasany, Y. M. (2026). *A corpus-aligned Uthmani-to-Standard Quranic word mapping and a deterministic recitation validator* (arXiv:2609.14967) [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2609.14967",
  "Govett, D. (2024). *fontkit* (Version 2.0.4) [Computer software]. https://github.com/foliojs/fontkit",
  "Hakak, S., Kamsin, A., Palaiahnakote, S., Tayan, O., Idris, M. Y. I., & Abukhir, K. Z. (2018). Residual-based approach for authenticating pattern of multi-style diacritical Arabic texts. *PLoS ONE, 13*(6), e0198284. https://doi.org/10.1371/journal.pone.0198284",
  "Hakak, S., Kamsin, A., Tayan, O., Idris, M. Y. I., Gani, A., & Zerdoumi, S. (2017). Preserving content integrity of digital Holy Quran: Survey and open challenges. *IEEE Access, 5*, 7305–7325. https://doi.org/10.1109/ACCESS.2017.2682109",
  "Kazmi, M., Habib, S., Hayat, S., Rehman, L., Aziz, A., & Qazi, S. A. (2024). UniHaCh: Unicode and hash function supported with counting and frequency recurrence of Arabic characters for Quranic text watermarking. *Arabian Journal for Science and Engineering, 49*(3), 4307–4323. https://doi.org/10.1007/s13369-023-08349-9",
  "Khan, M. K., Siddiqui, Z., & Tayan, O. (2017). A secure framework for digital Quran certification. In *2017 IEEE International Conference on Consumer Electronics (ICCE)* (pp. 59–60). IEEE. https://doi.org/10.1109/ICCE.2017.7889229",
  "Laurie, B., Messeri, E., & Stradling, R. (2021). *Certificate transparency version 2.0* (RFC 9162). Internet Engineering Task Force. https://doi.org/10.17487/RFC9162",
  "Mubarak, H., Malhas, R., Mansour, W., Mohamed, A., Fawzi, M., Hawasly, M., Elsayed, T., Darwish, K. M., & Magdy, W. (2025). IslamicEval 2025: The first shared task of capturing LLMs hallucination in Islamic content. In *Proceedings of the Third Arabic Natural Language Processing Conference: Shared Tasks* (pp. 480–493). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.arabicnlp-sharedtasks.67",
  "National Institute of Standards and Technology. (2015). *Secure hash standard (SHS)* (FIPS PUB 180-4). https://doi.org/10.6028/NIST.FIPS.180-4",
  "Pournader, R., Hallissy, B., & Evans, L. (Eds.). (n.d.). *Unicode Standard Annex #53: Unicode Arabic mark rendering*. Unicode Consortium. Retrieved November 11, 2026, from https://www.unicode.org/reports/tr53/",
  "Qur'anpedia. (n.d.). *Mushaf data dumps* [Data set]. Retrieved November 10, 2026, from https://api.quranpedia.net/dumps/",
  "risan. (2026). *quran-json* [Computer software and data set]. GitHub. https://github.com/risan/quran-json",
  "Stigge, M., Plötz, H., Müller, W., & Redlich, J.-P. (2006). *Reversing CRC – Theory and practice* (HU Berlin Public Report SAR-PR-2006-05). Humboldt University Berlin.",
  "Tanzil Project. (n.d.). *Tanzil Quran text* [Data set]. Retrieved November 10, 2026, from https://tanzil.net/docs/",
  "Tayan, O., Kabir, M. N., & Alginahi, Y. M. (2014). A hybrid digital-signature and zero-watermarking approach for authentication and protection of sensitive electronic documents. *The Scientific World Journal, 2014*, 514652. https://doi.org/10.1155/2014/514652",
  "Touati-Hamad, Z., Laouar, M. R., & Bendib, I. (2021). A data preservation method based on blockchain for digital sensitive text integrity. In *2021 International Conference on Information Systems and Advanced Technologies (ICISAT)*. IEEE. https://doi.org/10.1109/ICISAT54145.2021.9678467",
  "Unicode Consortium. (2023). *The Unicode Standard, version 15.1.0*. https://www.unicode.org/versions/Unicode15.1.0/",
  "Whistler, K. (Ed.). (2024). *Unicode Standard Annex #15: Unicode normalization forms* (Version 16.0.0). Unicode Consortium. https://www.unicode.org/reports/tr15/tr15-56.html",
  "Zita, W., Zita, N., Khalil, M. S., ElShenieky, R. I. M., & Şahin, B. (2026). *Verification method and framework for the digital Holy Quran* [Preprint]. Research Square. https://doi.org/10.21203/rs.3.rs-9577829/v1",
];
const refSection = [
  h1("References"),
  ...refs.map((r) => new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 20 }, indent: { left: 567, hanging: 567 },
    children: runs(r, { font: TNR, size: 24 }) })),
];

// ---------------------------------------------------------------- biodata + Arabic abstract
const bioRow = (label) => new TableRow({ height: { value: 1700, rule: HeightRule.ATLEAST }, children: [
  new TableCell({ width: { size: 1800, type: WidthType.DXA }, borders: { top: thin, bottom: thin, left: thin, right: thin },
    verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "[Photo]", font: TNR, size: 20, highlight: "yellow" })] })] }),
  new TableCell({ width: { size: 7226, type: WidthType.DXA }, borders: { top: thin, bottom: thin, left: thin, right: thin },
    margins: { left: 100, right: 100 }, children: [new Paragraph({ alignment: AlignmentType.JUSTIFIED,
      children: [new TextRun({ text: label, font: TNR, size: 22, highlight: "yellow" })] })] })] });
const bio = [
  h1("Biodata"),
  new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [1800, 7226],
    rows: [bioRow("[Biodata of author 1: degree, position, affiliation and research interests]"),
      bioRow("[Biodata of author 2]")] }),
  blank(),
];
const ar = (text, opt = {}) => new Paragraph({ bidirectional: true, alignment: opt.align || AlignmentType.CENTER,
  spacing: { after: opt.after ?? 80 }, children: (Array.isArray(text) ? text : [text]).map((x) => (typeof x === "string" ? { t: x } : x)).map((t) =>
    new TextRun({ text: t.t, font: AR, size: t.size || opt.size || 24, bold: t.bold ?? opt.bold ?? false, rightToLeft: true,
      highlight: t.hl ? "yellow" : undefined })) });
const arabic = [
  ar("التحقق من سلامة النص القرآني الرقمي المرتبط بالموضع والمراعي لترميز يونيكود باستخدام سجل ميركل موقّع ثنائي المستوى", { size: 36, bold: true, after: 200 }),
  ar([{ t: "[المؤلف الأول]1، [المؤلف الثاني]2", hl: true, bold: true }]),
  ar([{ t: "1[القسم، الجامعة التكنولوجية، بغداد، العراق]", hl: true }]),
  ar([{ t: "2[عنوان المؤلف الثاني]", hl: true }]),
  ar([{ t: "[البريد الإلكتروني للمؤلفين]", hl: true }], { after: 240 }),
  ar([{ t: "الخلاصة. ", bold: true }, { t: `تنتقل نسخ القرآن الكريم الرقمية بين التطبيقات والمواقع ومجموعات البيانات المفتوحة، وقد يكفي تغيير حرف أو حركة أو موضع آية واحدة لتغيير المعنى. وتعتمد معظم أساليب التحقق على مقارنة البايتات، مع أن يونيكود يسمح بتخزين الآية المرئية نفسها بأكثر من طريقة. نقترح في هذا البحث مخططاً يوحّد كل آية بصيغة التطبيع NFC، ويربطها برقم سورتها ورقمها في شجرة ميركل ثنائية المستوى يُوقَّع جذرها بخوارزمية Ed25519، ثم يصنّف كل تغيير يكتشفه إلى تغيير في الترميز أو الحركات أو الحروف أو البنية. يكفي لاكتشاف التغيير بيانٌ موقّع حجمه ${e5.detection_only_bytes} بايتاً، أما البيانات اللازمة لتحديد موضعه فيمكن جلبها من أي خادم غير موثوق، لأن كل عنصر يُتحقَّق منه عند وصوله. وعلى نص تنزيل العثماني (6,236 آية)، حدّد المخطط موضع العبث بدقة في ${exactPct}% من ${fmt(D.n_trials)} نسخة عُبث بها بأربعة عشر أسلوباً، وصنّفه تصنيفاً صحيحاً في ${clsPct}%. وتبيّن تجارب الاستئصال أن هذه الدقة مصدرها التطبيع ومحاذاة الآيات، وأن فائدة الشجرة الموقّعة هي تقليل ما يحمله المتحقِّق وما يجلبه. وغيّر التحويل إلى NFC بايتات ${fmt(benign.NFC.verses_changed_bytes)} آية وكل البسملات الـ${benign.NFC.headers_changed_bytes} دون أن يتغيّر أي بكسل يرسمه محرّك التشكيل HarfBuzz في خمسة خطوط، ومع ذلك عدّتها جداول التجزئة الخام لكل آية معبوثاً بها. غير أن محرّك تشكيل ثانياً رسم ${fkPct("NFC", "Noto Naskh Arabic")}–${fkPct("NFC", "Amiri")}% من الكلمات المتغيّرة بصورة مختلفة في ثلاثة من أربعة خطوط، لذا ينبغي أن تعرض التطبيقات النص كما نُشر تماماً. واختلف ترميز مجمع الملك فهد المستقل عن نص تنزيل في ${fmt(uq.raw)} آية، لكنه لم يختلف في الهيكل الحرفي الموحَّد إلا في ${uq.sigma_star} آيات. ولم تطابق أيٌّ من عشر نسخ موزَّعة عبر واجهة برمجية عامة للقرآن وحزم npm أياً من السجلات الخمسة: فمعظمها طبعات أو إصدارات أخرى، وبعضها يحمل محارف غير مرئية أو الياء الفارسية أو علامات مفكَّكة، وواحدة طابقت كل الآيات لكنها خلت من البسملات. لذلك يجب نشر السجل لكل طبعة وترميز على حدة. وأخيراً، قبلت جداول CRC-32 لكل آية كل التعديلات الـ${sfx.crc_collision} على الحركات بعد تعويضها بإلحاق 32 محرفاً غير مرئي، ولم تترك هذه المحارف أثراً مرئياً في أي خط استطاع أيٌّ من المحرّكين رسمه.` }],
    { align: AlignmentType.JUSTIFIED, after: 160 }),
  ar([{ t: "الكلمات الجوهرية. ", bold: true }, { t: "سلامة النص القرآني، تطبيع يونيكود، شجرة ميركل، هجوم الأحرف المتشابهة، تحديد موضع العبث، التوقيع الرقمي." }],
    { align: AlignmentType.JUSTIFIED }),
];

// ---------------------------------------------------------------- assemble
const doc = new Document({
  styles: { default: { document: { run: { font: TNR, size: 24 } } } },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children: [...front, ...intro, ...related, ...method, ...results, ...discussion, ...conclusion, ...refSection, ...bio, ...arabic],
  }],
});
Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "../out/IMAN2026_Quran_Integrity.docx");
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, buf);
  console.log("written", out);
});
