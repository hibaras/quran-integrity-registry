"""Core library: canonicalisation, views, two-level Merkle registry, authenticated
localisation from an untrusted mirror, and diagnosis.

Design (used throughout the paper):
  * parse      : where an edition prefixes the basmala to verse 1 (chapters other than
                 1 and 9), the basmala is split off as verse 0 of that chapter, so verse
                 numbers follow the Mushaf and the basmala stays protected.
  * canon(t)   : Unicode NFC, then removal of leading/trailing ASCII white space only
                 (U+0020, U+0009, U+000A, U+000D). Any other character is kept.
  * Profile P  : set of code points of the canonical reference edition.
  * sigma(t)   : diagnostic letter skeleton (NFD; combining marks, default-ignorable
                 code points, tatweel, small annotation letters and two symbols removed;
                 alef wasla folded to alef). Used only to classify a detected change.
  * sigma*(t)  : comparison skeleton = sigma plus alef maksura -> yeh, used to compare
                 independent editions, which encode final yeh differently.
  * Registry   : RFC 6962 hashing (0x00 leaf, 0x01 node); verses -> chapter root;
                 chapter records -> edition root; length-prefixed signed statement that
                 also binds the Unicode data version and a digest of the profile P.
  * Verifier   : holds only the signed statement; fetches reference nodes, chapter
                 records and verse texts from an untrusted mirror and authenticates each
                 item against the already-authenticated parent hash.
"""
from __future__ import annotations

import hashlib
import json
import os
import unicodedata as ud
from dataclasses import dataclass, field
from functools import cached_property, lru_cache

LEAF, NODE = b"\x00", b"\x01"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
ASCII_WS = " \t\n\r"


# ---------------------------------------------------------------- Unicode data files
def _load_dicp() -> frozenset[int]:
    """Default_Ignorable_Code_Point from DerivedCoreProperties.txt (Unicode 15.1.0)."""
    out = set()
    for line in open(os.path.join(DATA, "DerivedCoreProperties-15.1.0.txt"), encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line or "Default_Ignorable_Code_Point" not in line:
            continue
        rng = line.split(";")[0].strip()
        if ".." in rng:
            a, b = rng.split("..")
            out.update(range(int(a, 16), int(b, 16) + 1))
        else:
            out.add(int(rng, 16))
    return frozenset(out)


def _load_confusables() -> dict[str, str]:
    """UTS #39 confusables.txt (version 15.1.0): source -> skeleton prototype."""
    out = {}
    for line in open(os.path.join(DATA, "confusables-15.1.0.txt"), encoding="utf-8-sig"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        s, t, _ = [x.strip() for x in line.split(";")]
        out["".join(chr(int(h, 16)) for h in s.split())] = "".join(chr(int(h, 16)) for h in t.split())
    return out


DICP = _load_dicp()
CONFUSABLES = _load_confusables()
BIDI_CONTROLS = frozenset({0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)})
SMALL_ANNOTATION_LETTERS = {0x06E5, 0x06E6}          # small waw / small yeh (category Lm)
EXTRA_SYMBOLS = {0x06DE, 0x06E9}                      # rub el hizb, sajdah sign (category So)
HAMZA_MARKS = {0x0654, 0x0655}                        # hamza above / below (separated by NFD)
YEH, MAKSURA, FARSI_YEH = 0x064A, 0x0649, 0x06CC


# ---------------------------------------------------------------- loading and parsing
BASMALA = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"


def load_raw(path: str) -> list[tuple[int, int, str]]:
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for c in sorted(d, key=int):
        for v in d[c]:
            out.append((int(v["chapter"]), int(v["verse"]), v["text"]))
    return out


def split_basmala(ed: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Split a basmala prefixed to verse 1 (chapters other than 1 and 9) into verse 0.
    The raw text is split at its fourth space and both parts are kept byte for byte;
    detection uses the folded skeleton of the first four words, so a tampered basmala
    is still split off and then detected as a change to verse 0."""
    target = skeleton(BASMALA, fold_maksura=True)
    out = []
    for c, v, t in ed:
        if v == 1 and c not in (1, 9):
            parts = t.split(" ", 4)
            if len(parts) == 5 and skeleton(" ".join(parts[:4]), fold_maksura=True) == target:
                out.append((c, 0, " ".join(parts[:4])))
                out.append((c, 1, parts[4]))
                continue
        out.append((c, v, t))
    return out


def load_edition(path: str) -> list[tuple[int, int, str]]:
    return split_basmala(load_raw(path))


# ---------------------------------------------------------------- views
def canon(t: str) -> str:
    return ud.normalize("NFC", t).strip(ASCII_WS)


def skeleton(t: str, fold_maksura: bool = False, hamza_as_letter: bool = False) -> str:
    """Letter skeleton. Default = diagnostic skeleton sigma; fold_maksura=True gives the
    comparison skeleton sigma*; hamza_as_letter=True is the sensitivity variant."""
    t = ud.normalize("NFD", canon(t))
    out = []
    for ch in t:
        o = ord(ch)
        if hamza_as_letter and o in HAMZA_MARKS:
            out.append("ء")
            continue
        if (ud.category(ch) in ("Mn", "Me", "Cf") or o in DICP or o == 0x0640
                or o in SMALL_ANNOTATION_LETTERS or o in EXTRA_SYMBOLS):
            continue
        if o == 0x0671:
            o = 0x0627                                    # alef wasla -> alef
        elif fold_maksura and o == MAKSURA:
            o = YEH
        out.append(chr(o))
    return " ".join("".join(out).split())


def layer1(t: str) -> str:                                # diagnostic skeleton sigma
    return skeleton(t)


def layer1_folded(t: str) -> str:                         # comparison skeleton sigma*
    return skeleton(t, fold_maksura=True)


def profile(edition: list[tuple[int, int, str]]) -> frozenset[int]:
    return frozenset(ord(ch) for *_, t in edition for ch in canon(t))


UNICODE_VERSION = ud.unidata_version          # 15.1.0 under Python 3.13


def profile_bytes(prof: frozenset[int]) -> bytes:
    """Canonical encoding of the profile: its code points in ascending order, UTF-8."""
    return "".join(chr(o) for o in sorted(prof)).encode("utf-8")


# ---------------------------------------------------------------- hashing
HASHES = {
    "sha256": lambda b: hashlib.sha256(b).digest(),
    "sha3_256": lambda b: hashlib.sha3_256(b).digest(),
    "blake2b256": lambda b: hashlib.blake2b(b, digest_size=32).digest(),
}
try:
    import blake3 as _b3
    HASHES["blake3"] = lambda b: _b3.blake3(b).digest()
except Exception:  # pragma: no cover
    pass

USE_CACHE = False          # experiments that repeat identical work may enable it; timings never do


def leaf_bytes(c: int, v: int, text: str) -> bytes:
    return c.to_bytes(2, "big") + v.to_bytes(2, "big") + canon(text).encode("utf-8")


def _leaf_hash(hname: str, c: int, v: int, text: str) -> bytes:
    return HASHES[hname](LEAF + leaf_bytes(c, v, text))


_leaf_hash_cached = lru_cache(maxsize=None)(_leaf_hash)


def leaf_hash(hname: str, c: int, v: int, text: str) -> bytes:
    return (_leaf_hash_cached if USE_CACHE else _leaf_hash)(hname, c, v, text)


class Merkle:
    """RFC 6962 Merkle Tree Hash over precomputed leaf hashes."""

    def __init__(self, leaf_hashes: list[bytes], h=HASHES["sha256"]):
        self.h = h
        self.leaf_hashes = leaf_hashes
        self.n = len(leaf_hashes)
        self._memo: dict[tuple[int, int], bytes] = {}
        self.root = self.node(0, self.n) if self.n else h(b"")

    @classmethod
    def from_leaves(cls, leaves: list[bytes], h=HASHES["sha256"]):
        return cls([h(LEAF + x) for x in leaves], h)

    @staticmethod
    def _split(n: int) -> int:
        k = 1
        while k * 2 < n:
            k *= 2
        return k

    def node(self, lo: int, hi: int) -> bytes:
        key = (lo, hi)
        if key in self._memo:
            return self._memo[key]
        if hi - lo == 1:
            r = self.leaf_hashes[lo]
        else:
            k = self._split(hi - lo)
            r = self.h(NODE + self.node(lo, lo + k) + self.node(lo + k, hi))
        self._memo[key] = r
        return r

    def children(self, lo: int, hi: int) -> tuple[bytes, bytes]:
        k = self._split(hi - lo)
        return self.node(lo, lo + k), self.node(lo + k, hi)

    def path(self, m: int) -> list[bytes]:
        """Audit path for leaf m (RFC 6962 PATH(m, D[n]))."""
        out: list[bytes] = []

        def rec(lo, hi, m):
            if hi - lo <= 1:
                return
            k = self._split(hi - lo)
            if m - lo < k:
                rec(lo, lo + k, m)
                out.append(self.node(lo + k, hi))
            else:
                rec(lo + k, hi, m)
                out.append(self.node(lo, lo + k))

        rec(0, self.n, m)
        return out


def verify_path(h, leaf_data: bytes, m: int, n: int, path: list[bytes], root: bytes) -> bool:
    """RFC 9162 s.2.1.3.2 inclusion-proof verification."""
    if m >= n:
        return False
    fn, sn = m, n - 1
    r = h(LEAF + leaf_data)
    for p in path:
        if sn == 0:
            return False
        if fn & 1 or fn == sn:
            r = h(NODE + p + r)
            if not fn & 1:
                while fn & 1 == 0 and fn != 0:
                    fn >>= 1
                    sn >>= 1
        else:
            r = h(NODE + r + p)
        fn >>= 1
        sn >>= 1
    return sn == 0 and r == root


# ---------------------------------------------------------------- two-level registry
def chapter_record(c: int, n_c: int, root: bytes) -> bytes:
    return c.to_bytes(2, "big") + n_c.to_bytes(2, "big") + root


def _lp(b: bytes) -> bytes:                               # one-byte length prefix
    assert len(b) < 256
    return bytes([len(b)]) + b


@dataclass
class Registry:
    edition: list[tuple[int, int, str]]
    hname: str = "sha256"
    chapters: dict[int, list[tuple[int, str]]] = field(default_factory=dict)
    ch_trees: dict[int, Merkle] = field(default_factory=dict)
    top: Merkle | None = None
    order: list[int] = field(default_factory=list)

    def __post_init__(self):
        h = HASHES[self.hname]
        for c, v, t in self.edition:
            self.chapters.setdefault(c, []).append((v, t))
        self.order = sorted(self.chapters)
        for c in self.order:
            self.ch_trees[c] = Merkle([leaf_hash(self.hname, c, v, t) for v, t in self.chapters[c]], h)
        self.top = Merkle.from_leaves([self.record(c) for c in self.order], h)

    @cached_property
    def profile(self) -> frozenset[int]:
        """Profile P, computed only when the statement or a diagnosis needs it."""
        return profile(self.edition)

    @cached_property
    def profile_digest(self) -> bytes:
        return hashlib.sha256(profile_bytes(self.profile)).digest()

    def record(self, c: int) -> bytes:
        return chapter_record(c, len(self.chapters[c]), self.ch_trees[c].root)

    @property
    def root(self) -> bytes:
        return self.top.root

    def statement(self, edition_id: str, version: str) -> bytes:
        """The byte string that the publisher signs (Equation 5): fixed tag; length-
        prefixed edition identifier, version, hash name and Unicode data version; the
        SHA-256 digest of the profile P used for diagnosis; and the edition root."""
        return (b"QIR2" + _lp(edition_id.encode()) + _lp(version.encode())
                + _lp(self.hname.encode()) + _lp(UNICODE_VERSION.encode())
                + self.profile_digest + self.root)

    def proof(self, c: int, idx: int) -> dict:
        return {"c": c, "idx": idx, "n_c": len(self.chapters[c]),
                "ch_path": self.ch_trees[c].path(idx),
                "ch_root": self.ch_trees[c].root,
                "top_idx": self.order.index(c), "n_top": len(self.order),
                "top_path": self.top.path(self.order.index(c))}


def verify_verse(h, c: int, v: int, text: str, pf: dict, root: bytes) -> bool:
    if not verify_path(h, leaf_bytes(c, v, text), pf["idx"], pf["n_c"], pf["ch_path"], pf["ch_root"]):
        return False
    return verify_path(h, chapter_record(c, pf["n_c"], pf["ch_root"]), pf["top_idx"], pf["n_top"],
                       pf["top_path"], root)


# ---------------------------------------------------------------- untrusted mirror
class AuthError(Exception):
    """Raised when an item returned by the mirror does not match its authenticated hash."""


class Mirror:
    """Serves the reference edition's tree nodes, chapter records and verse texts.
    It is untrusted: every item is authenticated by the verifier. `corrupt` lets a test
    make the mirror return one altered item."""

    def __init__(self, reg: Registry, corrupt: tuple | None = None):
        self.reg = reg
        self.corrupt = corrupt
        self.cost = {"hashes": 0, "records": 0, "texts": 0, "text_bytes": 0, "profile_bytes": 0}

    def _maybe(self, kind, value):
        if self.corrupt and self.corrupt[0] == kind:
            self.corrupt = None
            if isinstance(value, bytes):
                return bytes([value[0] ^ 1]) + value[1:]
            if isinstance(value, tuple):
                return (bytes([value[0][0] ^ 1]) + value[0][1:], value[1])
            if isinstance(value, str):
                return value + "َ"
            if isinstance(value, list):
                (v, t), *rest = value
                return [(v, t + "َ"), *rest]
        return value

    def top_children(self, lo, hi):
        self.cost["hashes"] += 2
        return self._maybe("node", self.reg.top.children(lo, hi))

    def record(self, ci):
        self.cost["records"] += 1
        return self._maybe("record", self.reg.record(self.reg.order[ci]))

    def chapter_children(self, c, lo, hi):
        self.cost["hashes"] += 2
        return self._maybe("chnode", self.reg.ch_trees[c].children(lo, hi))

    def profile(self):
        b = profile_bytes(self.reg.profile)
        self.cost["profile_bytes"] += len(b)
        return self._maybe("profile", b)

    def text(self, c, idx):
        v, t = self.reg.chapters[c][idx]
        self.cost["texts"] += 1
        self.cost["text_bytes"] += len(canon(t).encode())
        return v, self._maybe("text", t)

    def chapter_texts(self, c):
        lst = self.reg.chapters[c]
        self.cost["texts"] += len(lst)
        self.cost["text_bytes"] += sum(len(canon(t).encode()) for _, t in lst)
        return self._maybe("chapter", list(lst))

    def bytes_fetched(self) -> int:
        return (32 * self.cost["hashes"] + 36 * self.cost["records"] + self.cost["text_bytes"]
                + self.cost["profile_bytes"])


def auth_localise(h, trusted: bytes, cand: Merkle, fetch) -> list[tuple[int, bytes]]:
    """Top-down comparison. `trusted` is the authenticated hash of the root of the
    reference subtree; children fetched from the mirror are checked against it.
    Returns differing leaf indices with their authenticated reference leaf hashes."""
    out: list[tuple[int, bytes]] = []

    def rec(lo, hi, ref_hash):
        if cand.node(lo, hi) == ref_hash:
            return
        if hi - lo == 1:
            out.append((lo, ref_hash))
            return
        L, R = fetch(lo, hi)
        if h(NODE + L + R) != ref_hash:
            raise AuthError("node")
        k = Merkle._split(hi - lo)
        rec(lo, lo + k, L)
        rec(lo + k, hi, R)

    rec(0, cand.n, trusted)
    return out


# ---------------------------------------------------------------- diagnosis rules
def joins_next(t: str, k: int) -> bool:
    """True if the character at k is followed (after combining marks and default-ignorable
    characters) by an Arabic letter, i.e. it is rendered in a connected form."""
    j = k + 1
    while j < len(t) and (ud.category(t[j]) == "Mn" or ord(t[j]) in DICP):
        j += 1
    return j < len(t) and ud.category(t[j]) == "Lo" and 0x0620 <= ord(t[j]) <= 0x06FF


@lru_cache(maxsize=None)
def _proto_groups(prof: frozenset[int]) -> dict[str, tuple[str, ...]]:
    groups: dict[str, list[str]] = {}
    for o in sorted(prof):
        ch = chr(o)
        if ud.category(ch).startswith("L"):
            groups.setdefault(CONFUSABLES.get(ch, ch), []).append(ch)
    return {k: tuple(v) for k, v in groups.items()}


def repair(t: str, prof: frozenset[int]) -> str:
    """Undo encoding-level manipulation: drop default-ignorable characters; map each
    out-of-profile character to its compatibility (NFKC) form or, failing that, to the
    profile letter with the same UTS #39 skeleton prototype. UTS #39 conflates yeh and
    alef maksura; Farsi yeh (dotted only when joined) is mapped to yeh in connected
    positions and to alef maksura in final or isolated positions."""
    groups = _proto_groups(prof)
    t = "".join(ch for ch in t if ord(ch) not in DICP)
    out = []
    for k, ch in enumerate(t):
        o = ord(ch)
        if o in prof:
            out.append(ch)
            continue
        x = ud.normalize("NFKC", ch)
        if ord(x[0]) == FARSI_YEH or o == FARSI_YEH:
            out.append(chr(YEH) if joins_next(t, k) else chr(MAKSURA))
            continue
        if all(ord(y) in prof for y in x):
            out.append(x)
            continue
        g = groups.get(CONFUSABLES.get(ch, ch))
        if g:
            out.append(chr(MAKSURA) if chr(MAKSURA) in g else g[0])
        else:
            out.append(ch)
    return "".join(out)


def anomalous(b: str, prof: frozenset[int]) -> bool:
    return any(ord(ch) not in prof or ord(ch) in DICP or ord(ch) in BIDI_CONTROLS for ch in b)


def classify_verse(ref_text: str, cand_text: str, prof: frozenset[int], hamza_as_letter=False) -> str:
    """'intact', 'U' (encoding-level only), 'U+D', 'U+L', 'D' (marks) or 'L' (letters)."""
    a, b = canon(ref_text), canon(cand_text)
    if a == b:
        return "intact"
    sk = lambda x: skeleton(x, hamza_as_letter=hamza_as_letter)  # noqa: E731
    if anomalous(b, prof):
        r = canon(repair(b, prof))
        if r == a:
            return "U"
        return "U+D" if sk(a) == sk(r) else "U+L"
    return "D" if sk(a) == sk(b) else "L"


# ---------------------------------------------------------------- verification and diagnosis
def diagnose(reg: Registry, cand: list[tuple[int, int, str]], prof: frozenset[int] | None = None,
             mirror: Mirror | None = None, hamza_as_letter=False) -> dict:
    """Verify a candidate copy against the signed statement. Only reg.root and
    reg.profile_digest are used directly (they stand for the signed statement); every
    other reference item, including the profile P, is fetched from the (untrusted)
    mirror and authenticated. Returns findings, mirror cost and a copy-level flag.
    The `prof` argument is accepted for backward compatibility and ignored."""
    h = HASHES[reg.hname]
    mirror = mirror or Mirror(reg)
    root = reg.root
    cand_ch: dict[int, list[tuple[int, str]]] = {}
    for c, v, t in cand:
        cand_ch.setdefault(c, []).append((v, t))
    order = sorted(cand_ch)
    trees = {c: Merkle([leaf_hash(reg.hname, c, v, t) for v, t in cand_ch[c]], h) for c in order}
    cand_top = Merkle.from_leaves([chapter_record(c, len(cand_ch[c]), trees[c].root) for c in order], h)
    findings: list[tuple[int, int, str]] = []
    if cand_top.root == root:
        return {"findings": [], "cost": dict(mirror.cost), "bytes": 0, "mismatch": False}
    if len(order) != len(reg.order):
        raise NotImplementedError("chapter-level insertion/deletion is outside the experiments")
    pb = mirror.profile()                                      # profile P, authenticated by digest
    if hashlib.sha256(pb).digest() != reg.profile_digest:
        raise AuthError("profile")
    prof = frozenset(ord(ch) for ch in pb.decode("utf-8", errors="replace"))
    bad = auth_localise(h, root, cand_top, mirror.top_children)
    for ci, ref_leaf in bad:
        rec = mirror.record(ci)
        if h(LEAF + rec) != ref_leaf:
            raise AuthError("record")
        c, n_c, R_c = int.from_bytes(rec[:2], "big"), int.from_bytes(rec[2:4], "big"), rec[4:]
        lst = cand_ch.get(c, [])
        if len(lst) != n_c:                                   # structural: align verse texts
            ref_list = mirror.chapter_texts(c)
            if Merkle([leaf_hash(reg.hname, c, v, t) for v, t in ref_list], h).root != R_c:
                raise AuthError("chapter texts")
            # align on the comparison skeleton, so that a copy in another encoding is
            # still paired verse by verse; paired verses are then compared exactly
            import difflib
            sm = difflib.SequenceMatcher(a=[layer1_folded(t) for _, t in ref_list],
                                         b=[layer1_folded(t) for _, t in lst], autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                pairs = list(zip(range(i1, i2), range(j1, j2)))
                for i, j in pairs:
                    cls = classify_verse(ref_list[i][1], lst[j][1], prof, hamza_as_letter)
                    if cls != "intact":
                        findings.append((c, ref_list[i][0], cls))
                findings += [(c, ref_list[i][0], "S-del") for i in range(i1 + len(pairs), i2)]
                findings += [(c, lst[j][0], "S-ins") for j in range(j1 + len(pairs), j2)]
            continue
        idxs = auth_localise(h, R_c, trees[c], lambda lo, hi, c=c: mirror.chapter_children(c, lo, hi))
        ref_texts = {}
        for i, ref_leaf_v in idxs:
            v_ref, t_ref = mirror.text(c, i)
            if leaf_hash(reg.hname, c, v_ref, t_ref) != ref_leaf_v:
                raise AuthError("text")
            ref_texts[i] = (v_ref, t_ref)
        flagged_canon = {canon(t): v for v, t in ref_texts.values()}
        for i, (v_ref, t_ref) in ref_texts.items():
            v_c, t_c = lst[i]
            if v_c != v_ref:
                findings.append((c, v_ref, "S-renum"))
            elif canon(t_c) in flagged_canon and flagged_canon[canon(t_c)] != v_ref:
                findings.append((c, v_ref, "S-reloc"))
            else:
                findings.append((c, v_ref, classify_verse(t_ref, t_c, prof, hamza_as_letter)))
    # copy-level flag (a reporting aid; it never changes acceptance): a copy that differs
    # in most verses, mostly through out-of-profile code points, is reported as another
    # encoding, and its per-verse labels are then read as encoding triage. Wholesale
    # diacritic or letter changes without encoding anomalies are not flagged.
    n_u = sum(1 for *_, k in findings if k.startswith("U"))
    return {"findings": findings, "cost": dict(mirror.cost), "bytes": mirror.bytes_fetched(),
            "mismatch": len(findings) > 0.5 * len(cand) and n_u > 0.5 * len(findings)}
