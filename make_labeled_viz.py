"""Detailed labeled visualization of the converged house."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from pathlib import Path

from plot import PLOT
from constraints import SBC

NAVY  = "#1E2761"
RED   = "#B85042"
GREEN = "#2C5F2D"
BLUE  = "#065A82"
GREY  = "#64748B"
ORANGE = "#F59E0B"

# Converged house
HOUSE = ((5, 20), (70, 20), (70, 78), (5, 78))
DOOR  = (40, 20)

fig, ax = plt.subplots(figsize=(12, 11), dpi=140)
ax.set_aspect("equal")
ax.set_xlim(-12, 95)
ax.set_ylim(-10, 100)
ax.set_facecolor("white")
ax.set_xticks(range(0, 91, 10))
ax.set_yticks(range(0, 91, 10))
ax.grid(True, alpha=0.15, linestyle="--")
ax.tick_params(labelsize=9, colors="#666")

# Plot boundary
bd = list(PLOT.boundary) + [PLOT.boundary[0]]
ax.plot([p[0] for p in bd], [p[1] for p in bd], color=RED, linewidth=2.5,
        label="Plot boundary")

# Tree + buffer
tcx, tcy = PLOT.tree_center
ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius, color=GREEN, alpha=0.95))
ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius + SBC.tree_buffer_ft,
                       color=GREEN, fill=False, linestyle="--", linewidth=1.5, alpha=0.6))
ax.annotate(f"Tree (protected)\n+ 3 ft buffer",
            (tcx + 5, tcy + 2), fontsize=9, color=GREEN, ha="left")

# House
closed = list(HOUSE) + [HOUSE[0]]
ax.plot([p[0] for p in closed], [p[1] for p in closed],
        color=NAVY, linewidth=3, label="House (3,770 sq ft)")
ax.fill([p[0] for p in closed], [p[1] for p in closed], color=NAVY, alpha=0.18)

# Door
dx, dy = DOOR
ax.plot([dx - 2, dx + 2], [dy, dy], color=BLUE, linewidth=6, solid_capstyle="butt")
ax.annotate("Main door (40, 20)\non south wall", (dx, dy - 5),
            fontsize=9, color=BLUE, ha="center", fontweight="bold")

# Entry segment line
sx, ex = PLOT.entry_segment[0][0], PLOT.entry_segment[1][0]
ax.plot([sx, ex], [-0.4, -0.4], color=BLUE, linewidth=3, alpha=0.4)
ax.annotate("Entry segment x∈[35, 75]  (40 ft — driveway + parking)",
            ((sx + ex) / 2, -2.5), fontsize=8, color=BLUE, ha="center", style="italic")

# House dimension labels (inside house)
ax.annotate("65 ft", (37.5, 21.5), fontsize=12, color=NAVY, ha="center",
            fontweight="bold", va="bottom")
ax.annotate("58 ft", (6.5, 49), fontsize=12, color=NAVY, ha="left",
            fontweight="bold", rotation=90, va="center")
ax.annotate("3,770 sq ft\n(92.9% of Z3 max)", (37.5, 49),
            fontsize=14, color=NAVY, ha="center", va="center",
            fontweight="bold", style="italic")

# Setback arrows + labels
def setback(ax, x1, y1, x2, y2, label, color, offset=0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<->", color=color, lw=1.5))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.annotate(label, (mx, my), fontsize=10, color=color,
                ha="center", va="center", fontweight="bold",
                bbox=dict(facecolor="white", edgecolor=color, boxstyle="round,pad=0.25"))

# South (front) setback — measured from y=0 to house south (y=20)
setback(ax, 50, 0, 50, 20, "20 ft\nfront", ORANGE)

# North (rear) — house north (y=78) to plot top (y=88)
setback(ax, 35, 78, 35, 88, "10 ft\nrear", ORANGE)

# West side — plot left (x=0) to house west (x=5)
setback(ax, 0, 50, 5, 50, "5 ft\nwest", ORANGE)

# East side — house east (x=70) to plot right (x=80)
setback(ax, 70, 30, 80, 30, "10 ft\neast", ORANGE)

# Tree clearance arrow (from NE house corner to tree)
ax.annotate("", xy=(tcx, tcy), xytext=(70, 78),
            arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.5, linestyle="dashed"))
ax.annotate("11 ft\nto tree", (74, 82.5), fontsize=9, color=GREEN,
            ha="center", fontweight="bold",
            bbox=dict(facecolor="white", edgecolor=GREEN, boxstyle="round,pad=0.2"))

# House corner labels
for (cx, cy), tag in zip(HOUSE, ["SW (5,20)", "SE (70,20)", "NE (70,78)", "NW (5,78)"]):
    ax.annotate(tag, (cx, cy), fontsize=8, color=NAVY,
                xytext=(5 if cx < 40 else -5, 4 if cy > 40 else -10),
                textcoords="offset points",
                ha="left" if cx < 40 else "right")

# North compass
ax.annotate("N", (-8, 90), fontsize=14, fontweight="bold", color="#333", ha="center")
ax.annotate("", xy=(-8, 92), xytext=(-8, 84),
            arrowprops=dict(arrowstyle="->", color="#333", lw=1.8))

ax.set_title("Converged house — labeled with all setbacks, door, and tree clearance",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.legend(loc="upper left", fontsize=10, framealpha=0.95)

fig.tight_layout()
out = Path("output/slides/labeled_result.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}")
