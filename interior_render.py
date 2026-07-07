"""Render an InteriorLayout to a labeled PNG (importable, no side effects)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp

from plot import PLOT
from constraints import SBC

EPS = 1e-6
NAVY, RED, GREEN, BLUE, GREY, WINDOW = "#1E2761", "#B85042", "#2C5F2D", "#065A82", "#94A3B8", "#0EA5E9"
FILL = {"living": "#DCEEF7", "kitchen": "#FBE3D6", "corridor": "#E5E7EB",
        "bathroom": "#E3ECF7", "bedroom": "#E5F0E0"}
EDGE = {"living": "#065A82", "kitchen": "#C2410C", "corridor": "#64748B",
        "bathroom": "#1D4ED8", "bedroom": "#2C5F2D"}


def _ext_walls(r, fp):
    fx0, fy0, fx1, fy1 = fp
    w = []
    if abs(r.y_max - fy1) < EPS: w.append(("H", r.x_min, r.x_max, r.y_max))
    if abs(r.y_min - fy0) < EPS: w.append(("H", r.x_min, r.x_max, r.y_min))
    if abs(r.x_min - fx0) < EPS: w.append(("V", r.y_min, r.y_max, r.x_min))
    if abs(r.x_max - fx1) < EPS: w.append(("V", r.y_min, r.y_max, r.x_max))
    return w


def render(layout, out_path, title="Interior layout — Z3-verified", fill_frac=None):
    fp = layout.footprint
    fx0, fy0, fx1, fy1 = fp
    fig, ax = plt.subplots(figsize=(12, 11), dpi=140)
    ax.set_aspect("equal"); ax.set_xlim(-12, 95); ax.set_ylim(-10, 100)
    ax.set_xticks(range(0, 91, 10)); ax.set_yticks(range(0, 91, 10))
    ax.grid(True, alpha=0.15, linestyle="--"); ax.tick_params(labelsize=9, colors="#666")

    bd = list(PLOT.boundary) + [PLOT.boundary[0]]
    ax.plot([p[0] for p in bd], [p[1] for p in bd], color=RED, linewidth=2.5, label="Plot boundary")
    tcx, tcy = PLOT.tree_center
    ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius, color=GREEN, alpha=0.95))
    ax.add_patch(mp.Circle((tcx, tcy), PLOT.tree_radius + SBC.tree_buffer_ft, color=GREEN,
                           fill=False, linestyle="--", linewidth=1.4, alpha=0.6))

    # house shell (uncovered interior reads as open / flex space)
    ax.add_patch(mp.Rectangle((fx0, fy0), fx1 - fx0, fy1 - fy0, facecolor="#FBFDFF",
                              edgecolor=NAVY, linewidth=3.0, zorder=1))

    for r in layout.rooms:
        ax.add_patch(mp.Rectangle((r.x_min, r.y_min), r.width, r.depth, facecolor=FILL[r.kind],
                                  edgecolor=EDGE[r.kind], linewidth=2.0, zorder=2))
        cx, cy = r.center
        if r.kind == "corridor":
            ax.annotate("Corridor (4 ft)", (cx, cy), fontsize=9, color="#475569",
                        ha="center", va="center", style="italic", zorder=4)
            continue
        ax.annotate(r.name, (cx, cy + 1.3), fontsize=10.5, color=NAVY, ha="center",
                    va="center", fontweight="bold", zorder=4)
        ax.annotate(f"{r.area:.0f} sq ft\n{r.width:.0f}×{r.depth:.0f}", (cx, cy - 2.3),
                    fontsize=8, color="#444", ha="center", va="center", zorder=4)

    # windows on any bedroom wall that lies on the house boundary
    for r in layout.rooms:
        if r.kind != "bedroom":
            continue
        for w in _ext_walls(r, fp)[:2]:
            orient, a, b, c = w
            m = (a + b) / 2; half = min(2.0, (b - a) / 3)
            if orient == "H":
                ax.plot([m - half, m + half], [c, c], color=WINDOW, lw=4, zorder=6)
            else:
                ax.plot([c, c], [m - half, m + half], color=WINDOW, lw=4, zorder=6)

    dx, dy = layout.door
    ax.plot([dx - 2.5, dx + 2.5], [dy, dy], color=BLUE, linewidth=7, solid_capstyle="butt", zorder=5)
    ax.annotate("Main door\n(into Living)", (dx, dy - 5), fontsize=9, color=BLUE,
                ha="center", fontweight="bold")
    ax.annotate("N", (-8, 90), fontsize=14, fontweight="bold", color="#333", ha="center")
    ax.annotate("", xy=(-8, 92), xytext=(-8, 84), arrowprops=dict(arrowstyle="->", color="#333", lw=1.8))

    if fill_frac is not None:
        title = f"{title}   ·   {fill_frac*100:.0f}% rooms / {(1-fill_frac)*100:.0f}% open"
    ax.set_title(title, fontsize=14, fontweight="bold", color=NAVY, pad=14)
    handles = [mp.Patch(facecolor=FILL[k], edgecolor=EDGE[k], label=k.title())
               for k in ("living", "kitchen", "corridor", "bedroom", "bathroom")]
    handles.append(mp.Patch(facecolor="#FBFDFF", edgecolor=NAVY, label="Open / flex space"))
    ax.legend(handles=handles, loc="upper left", fontsize=9, framealpha=0.95)

    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_path
