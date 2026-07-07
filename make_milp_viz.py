"""Labeled visualization of the MILP / cutting-plane interior layout (PNG).

Standalone: solves the layout with PuLP+CBC (interior_milp), cross-checks the
full interior constraint set with Z3, and draws plot + tree + house shell +
corridor + rooms + ensuite bathrooms + bedroom windows. Run:
    python make_milp_viz.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from pathlib import Path

from plot import PLOT
from constraints import SBC
from interior_milp import solve_layout
from interior_verifier_z3 import check_interior

EPS = 1e-6
NAVY = "#1E2761"
RED = "#B85042"
GREEN = "#2C5F2D"
BLUE = "#065A82"
GREY = "#94A3B8"
WINDOW = "#0EA5E9"

FILL = {"living": "#DCEEF7", "kitchen": "#FBE3D6", "corridor": "#E5E7EB",
        "bathroom": "#E3ECF7", "bedroom": "#E5F0E0"}
EDGE = {"living": "#065A82", "kitchen": "#C2410C", "corridor": "#64748B",
        "bathroom": "#1D4ED8", "bedroom": "#2C5F2D"}


def exterior_walls(r, fp):
    """Return room walls that lie on the footprint boundary, as
    ('N'|'S'|'E'|'W', a, b, coord) where [a,b] is the wall span."""
    fx0, fy0, fx1, fy1 = fp
    walls = []
    if abs(r.y_max - fy1) < EPS: walls.append(("N", r.x_min, r.x_max, r.y_max))
    if abs(r.y_min - fy0) < EPS: walls.append(("S", r.x_min, r.x_max, r.y_min))
    if abs(r.x_min - fx0) < EPS: walls.append(("W", r.y_min, r.y_max, r.x_min))
    if abs(r.x_max - fx1) < EPS: walls.append(("E", r.y_min, r.y_max, r.x_max))
    return walls


def draw_window(ax, wall):
    """Draw a short window segment centred on a wall."""
    side, a, b, c = wall
    mid = (a + b) / 2
    half = min(2.0, (b - a) / 3)
    if side in ("N", "S"):
        ax.plot([mid - half, mid + half], [c, c], color=WINDOW, lw=4,
                solid_capstyle="butt", zorder=6)
    else:
        ax.plot([c, c], [mid - half, mid + half], color=WINDOW, lw=4,
                solid_capstyle="butt", zorder=6)


fp = (5.0, 20.0, 68.0, 78.0)
door = (40.0, 20.0)
res = solve_layout(fp, door)
layout = res.layout
viol = check_interior(layout, SBC, require_full_coverage=False)
assert not viol, f"MILP layout failed Z3 check: {[v.rule for v in viol]}"

fig, ax = plt.subplots(figsize=(12, 11), dpi=140)
ax.set_aspect("equal")
ax.set_xlim(-12, 95)
ax.set_ylim(-10, 100)
ax.set_xticks(range(0, 91, 10))
ax.set_yticks(range(0, 91, 10))
ax.grid(True, alpha=0.15, linestyle="--")
ax.tick_params(labelsize=9, colors="#666")

# Plot boundary + tree
bd = list(PLOT.boundary) + [PLOT.boundary[0]]
ax.plot([p[0] for p in bd], [p[1] for p in bd], color=RED, linewidth=2.5,
        label="Plot boundary")
tcx, tcy = PLOT.tree_center
ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius, color=GREEN, alpha=0.95))
ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius + SBC.tree_buffer_ft,
                       color=GREEN, fill=False, linestyle="--", linewidth=1.4, alpha=0.6))

# House shell
fx0, fy0, fx1, fy1 = fp
ax.add_patch(mp.Rectangle((fx0, fy0), fx1 - fx0, fy1 - fy0,
                          facecolor="white", edgecolor=NAVY, linewidth=3.0, zorder=1))

# Rooms
for r in layout.rooms:
    ax.add_patch(mp.Rectangle((r.x_min, r.y_min), r.width, r.depth,
                              facecolor=FILL[r.kind], edgecolor=EDGE[r.kind],
                              linewidth=2.0, zorder=2))
    cx, cy = r.center
    if r.kind == "corridor":
        ax.annotate("Corridor (4 ft)", (cx, cy), fontsize=9, color="#475569",
                    ha="center", va="center", style="italic", zorder=4)
        continue
    ax.annotate(r.name, (cx, cy + 1.4), fontsize=10.5, color=NAVY,
                ha="center", va="center", fontweight="bold", zorder=4)
    ax.annotate(f"{r.area:.0f} sq ft\n{r.width:.0f}×{r.depth:.0f}", (cx, cy - 2.4),
                fontsize=8, color="#444", ha="center", va="center", zorder=4)

# Bedroom windows (2 per bedroom, on exterior walls where available)
for r in layout.rooms:
    if r.kind != "bedroom":
        continue
    walls = exterior_walls(r, fp)
    if len(walls) >= 2:
        draw_window(ax, walls[0]); draw_window(ax, walls[1])
    elif len(walls) == 1:
        side, a, b, c = walls[0]
        q = (a + b) / 2
        if side in ("N", "S"):
            ax.plot([a + (b-a)*0.28, a + (b-a)*0.28 + 2], [c, c], color=WINDOW, lw=4, zorder=6)
            ax.plot([b - (b-a)*0.28 - 2, b - (b-a)*0.28], [c, c], color=WINDOW, lw=4, zorder=6)

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

ax.set_title("MILP / cutting-plane interior — 8 rooms placed by CBC, Z3-verified",
             fontsize=14, fontweight="bold", color=NAVY, pad=14)
handles = [mp.Patch(facecolor=FILL[k], edgecolor=EDGE[k], label=k.title())
           for k in ("living", "kitchen", "corridor", "bedroom", "bathroom")]
handles.append(plt.Line2D([0], [0], color=WINDOW, lw=4, label="Window"))
ax.legend(handles=handles, loc="upper left", fontsize=9, framealpha=0.95)

fig.tight_layout()
out = Path("output/slides/milp_result.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=140, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}  (CBC {res.status}, fill {res.fill_frac*100:.0f}%, "
      f"{len(layout.rooms)} rooms)")
