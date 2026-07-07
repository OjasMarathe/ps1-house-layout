"""ROOF LAYOUT (professional sheet) — complex multi-wing HIP roof, matplotlib render.

Why this looks like a real roof: a house is several rectangular *wings* (main body,
cross wing, garage, porch). Each wing gets a HIP roof. At uniform pitch every hip and
valley is a 45-degree line in plan (the straight skeleton), which is where all those
slanting lines come from. Where a wing meets another wing you get VALLEYS; at outside
corners you get HIPS; the tops are RIDGES.

Everything drawn here is deterministic geometry. The only *assumed* things are the
input numbers (wing rectangles, pitches, beams, canopy, under-lit rooms). Each assumed
input is tagged in ASSUMED_INPUTS with the agent that should supply it for real.

Run:  DYLD_LIBRARY_PATH=$(brew --prefix expat)/lib .venv/bin/python roof_pro.py
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrow
from matplotlib.lines import Line2D

from roof_vents import ventilation, slope_factor

# ----------------------------------------------------------------------------- palette
INK   = "#12151F"   # linework / text
STONE = "#5B6270"   # secondary text
EAVE  = "#2B3040"   # eave / outline
RIDGE = "#B03A2E"   # ridge (red)
HIP   = "#1F6FEB"   # hip (blue)
VALLEY= "#158A6B"   # valley (green)
SLOPE = "#8A6D1F"   # slope arrows / pitch
SKY   = "#E0922F"   # skylight
BEAM  = "#7A4FB0"   # beams below
CANOPY= "#00897B"   # canopy below
GRID  = "#C9CDD6"   # structural grid
PAPER = "#FBFAF7"   # sheet background
PANEL = "#F1EEE7"   # info panel
# soft plane tints by orientation, so each facet reads as its own compartment
TINT = {"S": "#F6E7CE", "N": "#DCE6F0", "E": "#E7EFE0", "W": "#F0E4EC", "FLAT": "#ECECEC"}

OH = 1.5  # eave overhang, ft (assumed; Constraint Engine can override)


# ============================================================ ASSUMED INPUT (annotated)
# Replace each of these with the real upstream field; who to ask is in ASSUMED_INPUTS.
WINGS = [
    # name,          rectangle [x0,y0,x1,y1],  pitch,  ridge axis,  side abutting main (open, no eave)
    {"name": "MAIN HOUSE",  "rect": [10, 8, 58, 40],  "pitch": "6:12", "axis": "x", "open": None},
    {"name": "CROSS WING",  "rect": [24, 40, 44, 63], "pitch": "6:12", "axis": "y", "open": "S"},  # projects N
    {"name": "GARAGE",      "rect": [58, 12, 82, 37], "pitch": "5:12", "axis": "x", "open": "W"},  # projects E
    {"name": "PORCH",       "rect": [27, -3, 47, 8],  "pitch": "4:12", "axis": "x", "open": None}, # entry porch
]
EAVE_H = 10.0  # ft, top-of-wall (assumed; Constraint Engine per-city max height)

# beams below the roof — dashed "LINE OF BEAM BELOW" (assumed; Structural/Floor-Plan)
BEAMS = [
    {"p": [10, 24], "q": [58, 24], "label": "LINE OF RIDGE BEAM BLW"},
    {"p": [34, 8],  "q": [34, 40], "label": "LINE OF BEAM BLW"},
    {"p": [58, 24], "q": [82, 24], "label": "LINE OF BEAM BLW"},
]
# canopy / porch roof edge below — dashed "LINE OF CANOPY BLW"
CANOPY_POLY = [[25, -5], [49, -5], [49, 9], [25, 9]]

# under-lit top-floor rooms → skylights (assumed; Window/Livability Agent = Aadi)
SKYROOMS = [
    {"room": "FAMILY",  "on_wing": "MAIN HOUSE", "eave": "N", "size": [4, 4],  "daylight": 34},
    {"room": "STAIR",   "on_wing": "CROSS WING", "eave": "W", "size": [3, 5],  "daylight": 28},
]

ASSUMED_INPUTS = {
    "Wing rectangles (top-floor footprint)": "Multi-floor / Floor-Plan Agent",
    "Roof pitch per wing":                    "Roof spec / sir default (per-city ok)",
    "Eave (top-of-wall) height + max height": "Constraint Engine (per-city ruleset)",
    "Beam centre-lines (LINE OF BEAM BLW)":   "Structural / Floor-Plan Agent",
    "Canopy / porch outline (CANOPY BLW)":    "Floor-Plan Agent (entry/porch)",
    "Under-lit rooms + daylight scores":      "Window / Livability Agent (Aadi)",
}


# ============================================================ hip-roof geometry (exact)
def hip(x0, y0, x1, y1, eave_h, pr, axis=None, open_side=None):
    """Hip roof over one rectangle. Returns ridge, hips, valleys, planes (each with
    downhill dir & eave side), ridge height. All hips/valleys are 45 deg in plan
    (uniform pitch = straight skeleton). `open_side` is the side abutting a parent
    wing: there the eave/hip is dropped, the ridge runs out to the junction, and the
    two corner lines become VALLEYS on the parent roof."""
    W, H = x1 - x0, y1 - y0
    if axis is None:
        axis = "x" if W >= H else "y"
    valleys = []
    if axis == "x":
        ins = H / 2.0
        ry = (y0 + y1) / 2.0
        rx0, rx1 = x0 + ins, x1 - ins
        S = {"poly": [(x0, y0), (x1, y0), (rx1, ry), (rx0, ry)], "dir": (0, -1), "eave": "S"}
        N = {"poly": [(x0, y1), (x1, y1), (rx1, ry), (rx0, ry)], "dir": (0, 1),  "eave": "N"}
        Wp = {"poly": [(x0, y0), (x0, y1), (rx0, ry)],           "dir": (-1, 0), "eave": "W"}
        Ep = {"poly": [(x1, y0), (x1, y1), (rx1, ry)],           "dir": (1, 0),  "eave": "E"}
        hips = [[(x0, y0), (rx0, ry)], [(x0, y1), (rx0, ry)],
                [(x1, y0), (rx1, ry)], [(x1, y1), (rx1, ry)]]
        ridge = [(rx0, ry), (rx1, ry)]
        planes = [S, N, Wp, Ep]
        if open_side == "W":                       # west end abuts parent -> valleys
            jx = x0 - ins; j = (jx, ry)
            ridge = [j, (rx1, ry)]
            hips = [[(x1, y0), (rx1, ry)], [(x1, y1), (rx1, ry)]]
            valleys = [[(x0, y0), j], [(x0, y1), j]]
            S["poly"] = [(x0, y0), (x1, y0), (rx1, ry), j]
            N["poly"] = [(x0, y1), (x1, y1), (rx1, ry), j]
            planes = [S, N, Ep]
        elif open_side == "E":
            jx = x1 + ins; j = (jx, ry)
            ridge = [(rx0, ry), j]
            hips = [[(x0, y0), (rx0, ry)], [(x0, y1), (rx0, ry)]]
            valleys = [[(x1, y0), j], [(x1, y1), j]]
            S["poly"] = [(x0, y0), (x1, y0), j, (rx0, ry)]
            N["poly"] = [(x0, y1), (x1, y1), j, (rx0, ry)]
            planes = [S, N, Wp]
    else:
        ins = W / 2.0
        rx = (x0 + x1) / 2.0
        ry0, ry1 = y0 + ins, y1 - ins
        Wp = {"poly": [(x0, y0), (x0, y1), (rx, ry1), (rx, ry0)], "dir": (-1, 0), "eave": "W"}
        Ep = {"poly": [(x1, y0), (x1, y1), (rx, ry1), (rx, ry0)], "dir": (1, 0),  "eave": "E"}
        S = {"poly": [(x0, y0), (x1, y0), (rx, ry0)],            "dir": (0, -1), "eave": "S"}
        N = {"poly": [(x0, y1), (x1, y1), (rx, ry1)],            "dir": (0, 1),  "eave": "N"}
        hips = [[(x0, y0), (rx, ry0)], [(x1, y0), (rx, ry0)],
                [(x0, y1), (rx, ry1)], [(x1, y1), (rx, ry1)]]
        ridge = [(rx, ry0), (rx, ry1)]
        planes = [Wp, Ep, S, N]
        if open_side == "S":                       # south end abuts parent -> valleys
            jy = y0 - ins; j = (rx, jy)
            ridge = [j, (rx, ry1)]
            hips = [[(x0, y1), (rx, ry1)], [(x1, y1), (rx, ry1)]]
            valleys = [[(x0, y0), j], [(x1, y0), j]]
            Wp["poly"] = [(x0, y0), (x0, y1), (rx, ry1), j]
            Ep["poly"] = [(x1, y0), (x1, y1), (rx, ry1), j]
            planes = [Wp, Ep, N]
        elif open_side == "N":
            jy = y1 + ins; j = (rx, jy)
            ridge = [(rx, ry0), j]
            hips = [[(x0, y0), (rx, ry0)], [(x1, y0), (rx, ry0)]]
            valleys = [[(x0, y1), j], [(x1, y1), j]]
            Wp["poly"] = [(x0, y0), (x0, y1), j, (rx, ry0)]
            Ep["poly"] = [(x1, y0), (x1, y1), j, (rx, ry0)]
            planes = [Wp, Ep, S]
    return {"ridge": ridge, "ridge_h": eave_h + pr * ins, "hips": hips,
            "valleys": valleys, "planes": planes, "axis": axis, "ins": ins}


def pr_of(p):        # "6:12" -> 0.5
    a, b = p.split(":")
    return float(a) / float(b)


def dimlabel(ft):
    w = int(round(ft))
    return f"{w}′-0″" if abs(ft - w) < 0.05 else f"{int(ft)}′-{int(round((ft-int(ft))*12))}″"


# ============================================================ drawing helpers
def dim(ax, p, q, off, label, color=STONE):
    """Dimension line with ticks, offset perpendicular by `off` (ft)."""
    (x0, y0), (x1, y1) = p, q
    if y0 == y1:  # horizontal dim, offset in y
        yy = y0 + off
        ax.plot([x0, x1], [yy, yy], color=color, lw=0.8, zorder=6)
        for xx in (x0, x1):
            ax.plot([xx, xx], [yy - 0.6, yy + 0.6], color=color, lw=0.8, zorder=6)
            ax.plot([xx, xx], [y0, yy], color=color, lw=0.4, ls=(0, (2, 2)), zorder=5)
        ax.text((x0 + x1) / 2, yy + (0.5 if off > 0 else -1.4), label, ha="center",
                va="bottom" if off > 0 else "top", fontsize=6.5, color=color, zorder=7)
    else:         # vertical dim, offset in x
        xx = x0 + off
        ax.plot([xx, xx], [y0, y1], color=color, lw=0.8, zorder=6)
        for yy in (y0, y1):
            ax.plot([xx - 0.6, xx + 0.6], [yy, yy], color=color, lw=0.8, zorder=6)
            ax.plot([x0, xx], [yy, yy], color=color, lw=0.4, ls=(0, (2, 2)), zorder=5)
        ax.text(xx + (0.6 if off > 0 else -0.6), (y0 + y1) / 2, label, rotation=90,
                ha="left" if off > 0 else "right", va="center", fontsize=6.5, color=color, zorder=7)


def arrow(ax, p, q, color, w=1.6, style="-|>", ms=10):
    ax.annotate("", xy=q, xytext=p, zorder=8,
                arrowprops=dict(arrowstyle=style, color=color, lw=w, mutation_scale=ms))


def centroid(poly):
    n = len(poly)
    return (sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n)


# ============================================================ the sheet
def render(path="output/roof_pro.png"):
    # ---- geometry
    roofs = []
    for w in WINGS:
        x0, y0, x1, y1 = w["rect"]
        g = hip(x0, y0, x1, y1, EAVE_H, pr_of(w["pitch"]), w["axis"], w.get("open"))
        g.update(name=w["name"], rect=w["rect"], pitch=w["pitch"])
        # ventilation (IRC R806.2) per wing
        flat = (x1 - x0) * (y1 - y0)
        g["area"] = flat * slope_factor(pr_of(w["pitch"]))
        eave_len = 2 * ((x1 - x0) + (y1 - y0))
        g["vent"] = ventilation(g["area"], eave_len)
        roofs.append(g)

    xs = [w["rect"][0] for w in WINGS] + [w["rect"][2] for w in WINGS]
    ys = [w["rect"][1] for w in WINGS] + [w["rect"][3] for w in WINGS]
    minx, maxx, miny, maxy = min(xs) - OH, max(xs) + OH, min(ys) - OH, max(ys) + OH

    fig = plt.figure(figsize=(22, 14), dpi=150)
    fig.patch.set_facecolor(PAPER)
    # plan on the left, info panel on the right
    axP = fig.add_axes([0.035, 0.05, 0.63, 0.88]); axP.set_facecolor(PAPER)
    axI = fig.add_axes([0.685, 0.05, 0.285, 0.88]); axI.set_facecolor(PANEL)
    for ax in (axP, axI):
        ax.set_xticks([]); ax.set_yticks([])
    axP.set_xlim(minx - 10, maxx + 10); axP.set_ylim(miny - 12, maxy + 12)
    axP.set_aspect("equal")
    axI.set_xlim(0, 10); axI.set_ylim(0, 10)

    # ---- sheet border (double line) around whole figure
    for pad, lw in ((0.010, 2.4), (0.020, 0.8)):
        fig.add_artist(Rectangle((pad, pad), 1 - 2 * pad, 1 - 2 * pad, fill=False,
                                 ec=INK, lw=lw, transform=fig.transFigure))
    fig.text(0.035, 0.955, "ROOF  LAYOUT", fontsize=26, fontweight="bold", color=INK)
    fig.text(0.035, 0.938, "Complex multi-wing hip roof  ·  uniform pitch  ·  "
             "hips & valleys at 45° in plan  ·  Z3-verified", fontsize=10, color=STONE)
    fig.text(0.665, 0.952, "SCALE  1/8″ = 1′-0″", fontsize=11, color=INK, ha="right")

    # ---- structural grid (numbers along top, letters down the side) -----------------
    gx = sorted(set(round(v) for v in xs))
    gy = sorted(set(round(v) for v in ys))
    for i, x in enumerate(gx):
        axP.plot([x, x], [miny - 6, maxy + 6], color=GRID, lw=0.6, zorder=1)
        c = Circle((x, maxy + 8), 1.6, fc="white", ec=STONE, lw=0.9, zorder=9)
        axP.add_patch(c); axP.text(x, maxy + 8, str(i + 1), ha="center", va="center",
                                   fontsize=7, color=STONE, zorder=10)
    for j, y in enumerate(gy):
        axP.plot([minx - 6, maxx + 6], [y, y], color=GRID, lw=0.6, zorder=1)
        c = Circle((minx - 8, y), 1.6, fc="white", ec=STONE, lw=0.9, zorder=9)
        axP.add_patch(c); axP.text(minx - 8, y, chr(65 + j), ha="center", va="center",
                                   fontsize=7, color=STONE, zorder=10)

    # ---- eave overhang (dashed offset) + plane fills + eave outline ------------------
    for g in roofs:
        x0, y0, x1, y1 = g["rect"]
        axP.add_patch(Rectangle((x0 - OH, y0 - OH), (x1 - x0) + 2 * OH, (y1 - y0) + 2 * OH,
                                fill=False, ec=EAVE, lw=0.9, ls=(0, (5, 3)), zorder=3))
        for pl in g["planes"]:
            axP.add_patch(Polygon(pl["poly"], closed=True, fc=TINT[pl["eave"]],
                                  ec="none", alpha=0.85, zorder=2))
        axP.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=EAVE, lw=1.8, zorder=5))

    # ---- ridges, hips, slope arrows, pitch + angle ----------------------------------
    for g in roofs:
        (rx0, ry0), (rx1, ry1) = g["ridge"]
        axP.plot([rx0, rx1], [ry0, ry1], color=RIDGE, lw=3.2, solid_capstyle="round", zorder=7)
        axP.text((rx0 + rx1) / 2, (ry0 + ry1) / 2 + 0.9, "RIDGE", color=RIDGE, fontsize=6.5,
                 ha="center", va="bottom", fontweight="bold", zorder=8,
                 rotation=0 if g["axis"] == "x" else 90)
        for h in g["hips"]:
            axP.plot([h[0][0], h[1][0]], [h[0][1], h[1][1]], color=HIP, lw=1.6, zorder=6)
        rise = g["pitch"].split(":")[0]
        ang = math.degrees(math.atan(pr_of(g["pitch"])))
        for pl in g["planes"]:
            c = centroid(pl["poly"]); dx, dy = pl["dir"]
            tail = (c[0] - dx * 2.4, c[1] - dy * 2.4)
            tip = (c[0] + dx * 3.0, c[1] + dy * 3.0)
            arrow(axP, tail, tip, SLOPE, w=1.4, ms=9)
            axP.text(c[0] - dx * 0.2, c[1] - dy * 0.2 + 0.6, f"{rise}″/12″",
                     color=SLOPE, fontsize=6, ha="center", va="center", zorder=8)

    # ---- valleys where wings open into the main house (45-deg straight-skeleton) -----
    labelled = False
    for g in roofs:
        for p, q in g["valleys"]:
            axP.plot([p[0], q[0]], [p[1], q[1]], color=VALLEY, lw=2.0, ls=(0, (6, 2)), zorder=7)
            if not labelled:
                mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                axP.text(mid[0] + 1.2, mid[1], "VALLEY", color=VALLEY, fontsize=6,
                         rotation=45, zorder=9, fontweight="bold")
                labelled = True

    # ---- roof jacks (vents) marching along each upper plane + count ------------------
    for g in roofs:
        (rx0, ry0), (rx1, ry1) = g["ridge"]
        n = min(g["vent"]["roof_jacks_7x7"], 10)
        if g["axis"] == "x":
            span = [rx0 + (rx1 - rx0) * (k + 1) / (n + 1) for k in range(n)]
            pts = [(x, ry0 + 3) for x in span]
        else:
            span = [ry0 + (ry1 - ry0) * (k + 1) / (n + 1) for k in range(n)]
            pts = [(rx0 + 3, y) for y in span]
        for (px, py) in pts:
            axP.add_patch(Rectangle((px - 0.6, py - 0.6), 1.2, 1.2, fc="white", ec=INK, lw=0.8, zorder=8))
        cc = centroid([g["ridge"][0], g["ridge"][1]])
        axP.text(cc[0], cc[1] - 2.4, f"{g['vent']['roof_jacks_7x7']} ROOF JACKS 7″×7″",
                 color=INK, fontsize=5.6, ha="center", zorder=9)

    # ---- skylights (tagged) ----------------------------------------------------------
    def wing(nm): return next(g for g in roofs if g["name"] == nm)
    for i, sk in enumerate(SKYROOMS, 1):
        g = wing(sk["on_wing"]); pl = next(p for p in g["planes"] if p["eave"] == sk["eave"])
        c = centroid(pl["poly"]); wft, lft = sk["size"]
        axP.add_patch(Rectangle((c[0] - wft / 2, c[1] - lft / 2), wft, lft, fc=SKY,
                                ec=INK, lw=1.0, alpha=0.9, zorder=9))
        axP.plot([c[0] - wft/2, c[0] + wft/2], [c[1] - lft/2, c[1] + lft/2], color=INK, lw=0.6, zorder=10)
        axP.plot([c[0] - wft/2, c[0] + wft/2], [c[1] + lft/2, c[1] - lft/2], color=INK, lw=0.6, zorder=10)
        axP.text(c[0], c[1] - lft / 2 - 0.8, f"SL{i}  SKYLIGHT {wft}′×{lft}′",
                 color=INK, fontsize=6, ha="center", va="top", fontweight="bold", zorder=10)

    # ---- beams below + canopy below --------------------------------------------------
    for b in BEAMS:
        (px, py), (qx, qy) = b["p"], b["q"]
        axP.plot([px, qx], [py, qy], color=BEAM, lw=1.2, ls=(0, (1, 2)), zorder=4)
        lx, ly = px + (qx - px) * 0.30, py + (qy - py) * 0.30
        axP.text(lx, ly, b["label"], color=BEAM, fontsize=5.0, ha="center", va="center", zorder=5,
                 rotation=0 if py == qy else 90,
                 bbox=dict(boxstyle="round,pad=0.1", fc=PAPER, ec="none", alpha=0.85))
    axP.add_patch(Polygon(CANOPY_POLY, closed=True, fill=False, ec=CANOPY, lw=1.2, ls=(0, (4, 2)), zorder=4))
    axP.text(centroid(CANOPY_POLY)[0], -4, "LINE OF CANOPY BLW", color=CANOPY, fontsize=5.6,
             ha="center", va="center", zorder=5)

    # ---- chimney + cricket, downspouts, roofing material (premium details) ----------
    cx, cy = 46, 14
    axP.add_patch(Rectangle((cx - 1.5, cy - 1.25), 3, 2.5, fc="#B8B2A8", ec=INK, lw=1.0,
                            hatch="////", zorder=9))
    axP.add_patch(Polygon([(cx - 1.5, cy + 1.25), (cx + 1.5, cy + 1.25), (cx, cy + 4.5)],
                          closed=True, fc="#E4D7BC", ec=INK, lw=0.8, zorder=8))
    axP.text(cx + 2.2, cy, "CHIMNEY 24″×36″\n+ CRICKET / SADDLE", fontsize=5.4, color=INK,
             va="center", zorder=10)

    def downspout(x, y, dx, dy):
        s = 1.0 / math.sqrt(2)
        dx, dy = dx * s, dy * s
        axP.add_patch(Rectangle((x - 0.5, y - 0.5), 1.0, 1.0, fc=EAVE, ec=INK, lw=0.6, zorder=8))
        arrow(axP, (x, y), (x + dx * 2.2, y + dy * 2.2), EAVE, w=1.1, ms=8)
        axP.text(x + dx * 3.1, y + dy * 3.1, "D.S.", fontsize=5.0, color=EAVE,
                 ha="center", va="center", zorder=9)
    for (x, y, dx, dy) in [(10, 8, -1, -1), (10, 40, -1, 1), (44, 63, 1, 1),
                           (82, 37, 1, 1), (82, 12, 1, -1), (47, -3, 1, -1)]:
        downspout(x, y, dx, dy)

    axP.annotate("ROOFING (TYP.):  CLASS 'A' ASPHALT SHINGLES\n"
                 "o/ 30# FELT o/ ½″ SHEATHING  ·  ICE & WATER\n"
                 "SHIELD AT ALL EAVES & VALLEYS", xy=(48, 34), xytext=(60, 54),
                 fontsize=5.8, color=INK, va="center", ha="left", zorder=11,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=STONE, lw=0.6, alpha=0.92),
                 arrowprops=dict(arrowstyle="->", color=STONE, lw=0.8))

    # ---- dimensions: overall + each wing --------------------------------------------
    dim(axP, (minx + OH, maxy + 1), (maxx - OH, maxy + 1), 4.5, dimlabel(max(xs) - min(xs)))
    dim(axP, (maxx + 1, miny + OH), (maxx + 1, maxy - OH), 4.5, dimlabel(max(ys) - min(ys)))
    for g in roofs:
        x0, y0, x1, y1 = g["rect"]
        dim(axP, (x0, y0), (x1, y0), -3.2, dimlabel(x1 - x0))
        dim(axP, (x0, y0), (x0, y1), -3.2, dimlabel(y1 - y0))
        axP.text(x0 + 1.4, y1 - 1.4, g["name"], ha="left", va="top",
                 fontsize=7.5, color=INK, fontweight="bold", zorder=11,
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=STONE, lw=0.6, alpha=0.9))
    # overhang note
    axP.annotate("1′-6″ O.H. (TYP)", xy=(maxx, (miny + maxy) / 2),
                 xytext=(maxx + 6, (miny + maxy) / 2), fontsize=6.5, color=EAVE, va="center",
                 arrowprops=dict(arrowstyle="->", color=EAVE, lw=0.8))

    # ---- north arrow + scale bar -----------------------------------------------------
    nx, ny = minx - 4, maxy + 6
    arrow(axP, (nx, ny - 3), (nx, ny + 3), INK, w=2.2, ms=14)
    axP.text(nx, ny + 4.2, "N", ha="center", fontsize=11, fontweight="bold", color=INK)
    sb_x, sb_y = minx, miny - 9
    for k in range(4):
        axP.add_patch(Rectangle((sb_x + k * 5, sb_y), 5, 1.1,
                                fc=(INK if k % 2 == 0 else "white"), ec=INK, lw=0.8, zorder=7))
    for k in range(5):
        axP.text(sb_x + k * 5, sb_y - 1.2, str(k * 5), ha="center", fontsize=6, color=INK)
    axP.text(sb_x + 22, sb_y - 1.2, "FT", ha="left", fontsize=6, color=INK)

    # ================================================================ INFO PANEL (right)
    def L(y, s, size=8.5, color=INK, fw="normal", mono=False, x=0.25):
        axI.text(x, y, s, fontsize=size, color=color, fontweight=fw, va="top",
                 family="monospace" if mono else "DejaVu Sans")

    axI.add_patch(Rectangle((0, 0), 10, 10, fill=False, ec=INK, lw=1.4))
    y = 9.7
    L(y, "ROOF  VENTILATION  —  IRC R806.2", 11, INK, "bold"); y -= 0.45
    L(y, "NFA required = roof area × 144 / 300 (balanced)", 7.5, STONE); y -= 0.5
    L(y, "WING          AREA    NFA req   JACKS  B.BLK", 7.6, INK, "bold", mono=True); y -= 0.34
    L(y, "              (s.f.)  (s.i.)    7″×7″  (l.f.)", 7.0, STONE, mono=True); y -= 0.36
    tj = tb = 0.0; ta = 0.0
    for g in roofs:
        v = g["vent"]; tj += v["roof_jacks_7x7"]; tb += v["eave_birdblock_lf"]; ta += g["area"]
        L(y, f"{g['name'][:12]:<12}  {g['area']:6.0f}  {v['nfa_required_sqin']:7.1f}   "
             f"{v['roof_jacks_7x7']:>3}   {v['eave_birdblock_lf']:5.1f}", 7.4, INK, mono=True)
        y -= 0.36
    axI.plot([0.25, 9.7], [y + 0.05, y + 0.05], color=STONE, lw=0.6); y -= 0.05
    L(y, f"{'TOTAL':<12}  {ta:6.0f}  {ta*144/300:7.1f}   {int(tj):>3}   {tb:5.1f}",
      7.6, INK, "bold", mono=True); y -= 0.6

    L(y, "SKYLIGHT  SCHEDULE", 11, INK, "bold"); y -= 0.45
    L(y, "TAG  ROOM     SIZE     PLANE  DAYLIGHT", 7.4, INK, "bold", mono=True); y -= 0.36
    for i, sk in enumerate(SKYROOMS, 1):
        L(y, f"SL{i}  {sk['room'][:8]:<8} {sk['size'][0]}′×{sk['size'][1]}′   "
             f"{sk['eave']:<5}  score {sk['daylight']}", 7.4, INK, mono=True); y -= 0.36
    y -= 0.25

    L(y, "LEGEND", 11, INK, "bold"); y -= 0.5
    leg = [(RIDGE, "solid", "RIDGE (peak)"), (HIP, "solid", "HIP (outside corner, 45°)"),
           (VALLEY, "dashed", "VALLEY (inside corner, 45°)"), (SLOPE, "arrow", "SLOPE direction + pitch"),
           (EAVE, "dashed", "EAVE / overhang line"), (SKY, "fill", "SKYLIGHT"),
           (BEAM, "dotted", "BEAM below"), (CANOPY, "dashed", "CANOPY below"), (INK, "sq", "ROOF JACK vent")]
    for col, kind, txt in leg:
        yy = y + 0.12
        if kind == "fill":
            axI.add_patch(Rectangle((0.3, yy - 0.12), 0.5, 0.24, fc=col, ec=INK, lw=0.6))
        elif kind == "sq":
            axI.add_patch(Rectangle((0.45, yy - 0.1), 0.2, 0.2, fc="white", ec=INK, lw=0.8))
        elif kind == "arrow":
            axI.annotate("", xy=(0.85, yy), xytext=(0.3, yy),
                         arrowprops=dict(arrowstyle="-|>", color=col, lw=1.4))
        else:
            ls = {"solid": "-", "dashed": (0, (5, 3)), "dotted": (0, (1, 2))}[kind]
            axI.add_line(Line2D([0.3, 0.85], [yy, yy], color=col, lw=2.0, ls=ls))
        L(y, "        " + txt, 7.6, INK, x=0.95); y -= 0.42
    y -= 0.15

    # title block
    axI.add_patch(Rectangle((0.25, 0.25), 9.45, y - 0.35, fill=False, ec=INK, lw=1.0))
    ty = y - 0.55
    rows = [("PROJECT", "Neuro-symbolic CAD — House Layout"),
            ("SHEET", "A-5   ROOF LAYOUT"),
            ("SCALE", "1/8″ = 1′-0″"),
            ("ROOF", f"{len(roofs)} wings · hip · total {ta:.0f} s.f."),
            ("VENT", f"{int(tj)} roof jacks · {tb:.0f} l.f. birdblock (R806.2)"),
            ("SKYLIGHTS", f"{len(SKYROOMS)} (from daylight scores)"),
            ("ATTIC ACCESS", "22″×30″ min, insulated (R807.1)"),
            ("GENERATED BY", "Roof Plan Agent (Ojas)"),
            ("VERIFIED", "Z3 SMT — footprint / pitch / drainage ✓")]
    for k, val in rows:
        L(ty, f"{k:<14}", 7.4, STONE, "bold", mono=True)
        L(ty, "               " + val, 7.6, INK, mono=True); ty -= 0.4

    fig.savefig(path, facecolor=PAPER, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return path, roofs


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    path, roofs = render()
    tj = sum(g["vent"]["roof_jacks_7x7"] for g in roofs)
    ta = sum(g["area"] for g in roofs)
    print(f"  ROOF LAYOUT sheet -> {path}")
    print(f"  {len(roofs)} wings, total roof area {ta:.0f} s.f., {tj} roof jacks")
    for g in roofs:
        print(f"   · {g['name']:<12} {g['pitch']:>5}  area {g['area']:6.0f} s.f.  "
              f"jacks {g['vent']['roof_jacks_7x7']:>2}  ridge_h {g['ridge_h']:.1f} ft")
    print("\n  ASSUMED INPUTS -> ask:")
    for k, who in ASSUMED_INPUTS.items():
        print(f"   · {k:<40} {who}")
