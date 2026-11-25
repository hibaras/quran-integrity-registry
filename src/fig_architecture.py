"""Figure 1: publisher, untrusted mirror and verifier of the proposed registry."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

INK, INK2 = "#0b0b0b", "#52514e"
BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams["font.family"] = "DejaVu Serif"

fig, ax = plt.subplots(figsize=(10, 5.0), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 54)
ax.axis("off")


def box(x, y, w, h, text, edge, fs=7.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc="white", ec=edge, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.22)


def arrow(x1, y1, x2, y2, color=INK2, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9, lw=1.0,
                                 color=color, linestyle=ls))


ax.text(1, 51.5, "Publisher (once per edition and version)", fontsize=8.5, color=BLUE, weight="bold")
top = [("Reference\nedition", 1), ("Parse: basmala\nas verse 0;\nNFC + trim", 17.5),
       ("Position-bound\nleaf hashes\n(c, v, text)", 34), ("114 chapter\nMerkle trees", 50.5),
       ("Edition tree over\nchapter records", 67), ("Sign statement\n(Ed25519)", 83.5)]
for t, x in top:
    box(x, 38, 13.0, 10, t, BLUE)
for (_, x1), (_, x2) in zip(top, top[1:]):
    arrow(x1 + 13.5, 43, x2 - 0.5, 43, BLUE)

box(31, 21.5, 30, 8, "Untrusted mirror (any server):\ntree nodes, chapter records, verse texts", GREEN)
arrow(56, 37.5, 48, 30.2, GREEN)
ax.text(53.5, 33.6, "publishes", fontsize=6.6, color=GREEN)

ax.text(1, 18.5, "Verifier (any copy, any time)", fontsize=8.5, color=ORANGE, weight="bold")
bot = [("Candidate copy\n(app, site, file)", 1), ("Parse and\ncanonicalise", 17.5),
       ("Recompute\nchapter roots", 34), ("Compare with\nsigned root", 50.5),
       ("Top-down\nlocalisation", 67), ("Diagnose class\nU / D / L / S", 83.5)]
for t, x in bot:
    box(x, 5, 13.0, 10, t, ORANGE)
for (_, x1), (_, x2) in zip(bot, bot[1:]):
    arrow(x1 + 13.5, 10, x2 - 0.5, 10, ORANGE)
arrow(90.0, 37.5, 59.5, 15.6, INK2)
ax.text(76.5, 30.5, "signed statement\n(62 B + 64 B signature)", fontsize=6.6, color=INK2, ha="left",
        bbox=dict(fc="white", ec="none", pad=0.4))
arrow(54, 21.0, 72.5, 15.6, GREEN, "--")
arrow(59, 21.0, 88.5, 15.6, GREEN, "--")
ax.text(50, 0.6, "Detection needs only the signed statement. Items fetched for localisation and diagnosis are each "
        "checked against an already authenticated hash.\nU: encoding-level   D: diacritic or annotation   "
        "L: letter or word   S: structural (verse inserted, deleted, relocated)",
        fontsize=6.5, color=INK2, ha="center", linespacing=1.4)
plt.savefig("figs/fig1_architecture.png", bbox_inches="tight", facecolor="white")
print("ok")
