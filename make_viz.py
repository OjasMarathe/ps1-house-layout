"""Generate PNG visualizations for the slide deck."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from pathlib import Path

from plot import PLOT
from constraints import SBC

OUT = Path("output/slides")
OUT.mkdir(parents=True, exist_ok=True)

NAVY   = "#1E2761"
ICE    = "#CADCFC"
RED    = "#B85042"
GREEN  = "#2C5F2D"
BLUE   = "#065A82"


def base_axes(title=""):
    fig, ax = plt.subplots(figsize=(8, 7), dpi=160)
    ax.set_aspect("equal")
    ax.set_xlim(-8, 88)
    ax.set_ylim(-6, 96)
    ax.set_facecolor("white")
    ax.set_xticks(range(0, 91, 10))
    ax.set_yticks(range(0, 91, 10))
    ax.grid(True, alpha=0.15, linestyle="--")
    ax.tick_params(labelsize=8, colors="#666")
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", color=NAVY, pad=12)
    # plot boundary
    boundary = list(PLOT.boundary) + [PLOT.boundary[0]]
    xs = [p[0] for p in boundary]; ys = [p[1] for p in boundary]
    ax.plot(xs, ys, color=RED, linewidth=3, label="Plot (L-shape, 6420 sq ft)")
    # tree
    tcx, tcy = PLOT.tree_center
    ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius, color=GREEN, fill=True, alpha=0.9))
    ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius + SBC.tree_buffer_ft,
                           color=GREEN, fill=False, linestyle="--", linewidth=1.5, alpha=0.6))
    ax.annotate("Tree (protected)\n+ 3 ft buffer", (tcx + 4, tcy),
                fontsize=8, color=GREEN, va="center")
    # entry segment
    sx, ex = PLOT.entry_segment[0][0], PLOT.entry_segment[1][0]
    ax.plot([sx, ex], [0, 0], color=BLUE, linewidth=4, alpha=0.5)
    ax.annotate("Entry segment (40 ft)\nmain door + parking", ((sx+ex)/2, -4.5),
                fontsize=8, color=BLUE, ha="center")
    # north arrow
    ax.annotate("N", (-4, 88), fontsize=12, fontweight="bold", color="#333", ha="center")
    ax.annotate("", xy=(-4, 90), xytext=(-4, 84),
                arrowprops=dict(arrowstyle="->", color="#333", lw=1.5))
    return fig, ax


def draw_house(ax, corners, door, color, label, alpha=0.25):
    closed = list(corners) + [corners[0]]
    xs = [p[0] for p in closed]; ys = [p[1] for p in closed]
    ax.plot(xs, ys, color=color, linewidth=2.5, label=label)
    ax.fill(xs, ys, color=color, alpha=alpha)
    # door
    dx, dy = door
    ax.plot([dx-1.5, dx+1.5], [dy, dy], color=BLUE, linewidth=4)
    ax.annotate("door", (dx, dy-2), fontsize=7, color=BLUE, ha="center")


# 1. Plot only (no house) — show the problem
fig, ax = base_axes("The plot: L-shape, 6420 sq ft, tree at top-right")
ax.legend(loc="lower left", fontsize=8, framealpha=0.95)
fig.tight_layout()
fig.savefig(OUT / "plot_only.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("wrote", OUT / "plot_only.png")


# 2. Final converged result — house at (5,20)-(70,78) = 3770 sq ft (iter 2 result)
fig, ax = base_axes("Converged result: 3,770 sq ft house — 58.7% of plot, 92.9% of Z3 max")
final = ((5, 20), (70, 20), (70, 78), (5, 78))
draw_house(ax, final, (40, 20), NAVY, "House (3770 sq ft)")
ax.legend(loc="lower left", fontsize=8, framealpha=0.95)
fig.tight_layout()
fig.savefig(OUT / "result_final.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("wrote", OUT / "result_final.png")


# 3. Three-stage prompt comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 6.5), dpi=160)
for ax, corners, door, label, area, pct in [
    (axes[0], ((35,20),(70,20),(70,74),(35,74)), (40,20), "Verbose prompt", 1890, 29.4),
    (axes[1], ((20,20),(75,20),(75,78),(20,78)), (47.5,20), "Minimalist prompt", 3190, 49.7),
    (axes[2], ((5,20),(70,20),(70,78),(5,78)), (40,20), "+ Z3 area constraint", 3770, 58.7),
]:
    ax.set_aspect("equal"); ax.set_xlim(-8, 88); ax.set_ylim(-6, 96)
    ax.set_xticks([]); ax.set_yticks([])
    # plot boundary
    bd = list(PLOT.boundary) + [PLOT.boundary[0]]
    ax.plot([p[0] for p in bd], [p[1] for p in bd], color=RED, linewidth=2.5)
    # tree
    tcx, tcy = PLOT.tree_center
    ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius, color=GREEN, fill=True))
    # house
    closed = list(corners) + [corners[0]]
    ax.plot([p[0] for p in closed], [p[1] for p in closed], color=NAVY, linewidth=2.5)
    ax.fill([p[0] for p in closed], [p[1] for p in closed], color=NAVY, alpha=0.3)
    ax.set_title(f"{label}\n{area:,} sq ft — {pct}% coverage",
                 fontsize=12, color=NAVY, fontweight="bold")
fig.suptitle("Prompt strategy drives 2× difference in achieved coverage",
             fontsize=14, fontweight="bold", color=NAVY, y=1.0)
fig.tight_layout()
fig.savefig(OUT / "comparison.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("wrote", OUT / "comparison.png")


# 4. Z3 max (theoretical) vs converged result side-by-side
fig, axes = plt.subplots(1, 2, figsize=(12, 6.5), dpi=160)
for ax, corners, door, label, area, pct in [
    (axes[0], ((5,20),(75,20),(75,78),(5,78)), (40,20),
     "Z3-provable maximum", 4060, 63.2),
    (axes[1], ((5,20),(70,20),(70,78),(5,78)), (40,20),
     "Our converged result", 3770, 58.7),
]:
    ax.set_aspect("equal"); ax.set_xlim(-8, 88); ax.set_ylim(-6, 96)
    ax.set_xticks([]); ax.set_yticks([])
    bd = list(PLOT.boundary) + [PLOT.boundary[0]]
    ax.plot([p[0] for p in bd], [p[1] for p in bd], color=RED, linewidth=2.5)
    tcx, tcy = PLOT.tree_center
    ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius, color=GREEN, fill=True))
    closed = list(corners) + [corners[0]]
    ax.plot([p[0] for p in closed], [p[1] for p in closed], color=NAVY, linewidth=2.5)
    ax.fill([p[0] for p in closed], [p[1] for p in closed], color=NAVY, alpha=0.3)
    ax.set_title(f"{label}\n{area:,} sq ft — {pct}% of plot",
                 fontsize=13, color=NAVY, fontweight="bold")
fig.suptitle("LLM design (right) matches 92.9% of formal optimum (left)",
             fontsize=14, fontweight="bold", color=NAVY, y=1.0)
fig.tight_layout()
fig.savefig(OUT / "vs_optimal.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("wrote", OUT / "vs_optimal.png")

print("done")
