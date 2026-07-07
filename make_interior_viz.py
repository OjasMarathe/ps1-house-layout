"""Labeled floor-plan visualization (PNG) of the complete layout, for slides.

Standalone: it Z3-synthesizes the certified reference interior for the
converged footprint and draws plot + tree + house + rooms + door. Run:
    python make_interior_viz.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from pathlib import Path

from plot import PLOT
from constraints import SBC
from interior_synth_z3 import synthesize

NAVY = "#1E2761"
RED = "#B85042"
GREEN = "#2C5F2D"
BLUE = "#065A82"

# Soft fills per room kind
FILL = {
    "living":   "#DCEef7",
    "kitchen":  "#FBE3D6",
    "bathroom": "#E3ECF7",
    "bedroom":  "#E5F0E0",
}
EDGE = {
    "living":   "#065A82",
    "kitchen":  "#C2410C",
    "bathroom": "#1D4ED8",
    "bedroom":  "#2C5F2D",
}

fp = (5.0, 20.0, 70.0, 78.0)
door = (40.0, 20.0)
layout = synthesize(fp, door, SBC)

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
                       color=GREEN, fill=False, linestyle="--", linewidth=1.4, alpha=0.6))
ax.annotate("Tree (protected)\n+ 3 ft buffer", (tcx + 4, tcy + 2),
            fontsize=8, color=GREEN, ha="left")

# Rooms
for r in layout.rooms:
    ax.add_patch(mp.Rectangle((r.x_min, r.y_min), r.width, r.depth,
                              facecolor=FILL[r.kind], edgecolor=EDGE[r.kind],
                              linewidth=2.0, zorder=2))
    cx, cy = r.center
    ax.annotate(r.name, (cx, cy + 1.5), fontsize=11, color=NAVY,
                ha="center", va="center", fontweight="bold", zorder=3)
    ax.annotate(f"{r.area:.0f} sq ft\n{r.width:.0f}×{r.depth:.0f} ft",
                (cx, cy - 2.5), fontsize=8.5, color="#444",
                ha="center", va="center", zorder=3)

# House outer wall (thick)
fx0, fy0, fx1, fy1 = fp
ax.add_patch(mp.Rectangle((fx0, fy0), fx1 - fx0, fy1 - fy0,
                          fill=False, edgecolor=NAVY, linewidth=3.2, zorder=4,
                          label=f"House ({fx1-fx0:.0f}×{fy1-fy0:.0f} ft)"))

# Door
dx, dy = door
ax.plot([dx - 2.5, dx + 2.5], [dy, dy], color=BLUE, linewidth=7,
        solid_capstyle="butt", zorder=5)
ax.annotate("Main door\n(into Living)", (dx, dy - 5), fontsize=9, color=BLUE,
            ha="center", fontweight="bold")

# Compass
ax.annotate("N", (-8, 90), fontsize=14, fontweight="bold", color="#333", ha="center")
ax.annotate("", xy=(-8, 92), xytext=(-8, 84),
            arrowprops=dict(arrowstyle="->", color="#333", lw=1.8))

ax.set_title("Complete layout — exterior + Z3-verified interior (7 rooms)",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
ax.legend(loc="upper left", fontsize=10, framealpha=0.95)

fig.tight_layout()
out = Path("output/slides/interior_result.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}  ({len(layout.rooms)} rooms, "
      f"{layout.footprint_area:.0f} sq ft)")
