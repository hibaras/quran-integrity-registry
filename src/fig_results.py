"""Figures 2 and 3 from the result files (static, print-ready)."""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2})

# ---- Figure 2: localisation cost (hashes fetched from the untrusted mirror)
perf = json.load(open("results/e5_perf.json"))
loc = perf["localisation"]
k = [r["k"] for r in loc]
q = [r["hashes_mean"] for r in loc]
base = loc[0]["table_hashes"]
runs = loc[0]["runs"]
fig, ax = plt.subplots(figsize=(6.2, 3.3), dpi=300)
ax.plot(k, [base] * len(k), color=ORANGE, lw=2, ls=(0, (4, 3)))
ax.plot(k, q, color=BLUE, lw=2, marker="o", ms=5, mec="white", mew=1.2)
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xticks(k)
ax.set_xticklabels([str(x) for x in k])
ax.set_xlabel("Number of tampered verses (k)")
ax.set_ylabel("Reference hashes fetched")
ax.grid(True, which="major", color=GRID, lw=0.6)
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
ax.text(1.05, base * 1.12, f"per-verse table: {base:,} hashes", color=INK2, fontsize=8)
ax.annotate(f"{q[0]:.1f}", (k[0], q[0]), xytext=(6, -12), textcoords="offset points", color=INK, fontsize=8)
ax.annotate(f"{q[-1]:,.0f}", (k[-1], q[-1]), xytext=(-30, -14), textcoords="offset points", color=INK, fontsize=8)
ax.text(9, 40, f"top-down localisation, mean of {runs} runs", color=BLUE, fontsize=8)
ax.set_ylim(15, 12000)
plt.tight_layout()
plt.savefig("figs/fig2_localisation.png", facecolor="white")
print("figs ok")
