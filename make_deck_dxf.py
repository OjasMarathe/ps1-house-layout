"""Emit a DXF for every figure used in the report, into report/dxf/.

Each DXF is rendered deterministically from the same Z3-verified geometry as the
matching PNG, on layered DXF (PLOT / TREE / HOUSE / ROOM_* / CORRIDOR / DOOR /
LABELS) so it opens cleanly in any Autodesk / CAD viewer.
"""
from pathlib import Path

import ezdxf
from ezdxf.colors import RED, GREEN

from plot import PLOT
from constraints import SBC
from verifier_z3 import HouseGeometry
from interior_verifier_z3 import Room, InteriorLayout
import dxf_full
import dxf_emitter
import interior_milp
import interior_fill
import templates

FP = (5.0, 20.0, 68.0, 78.0)
DOOR = (40.0, 20.0)
OUT = Path("report/dxf")
OUT.mkdir(parents=True, exist_ok=True)


def house_of(fp, door):
    x0, y0, x1, y1 = fp
    return HouseGeometry(corners=((x0, y0), (x1, y0), (x1, y1), (x0, y1)), door=door)


def lay(rooms):
    return InteriorLayout(FP, DOOR, tuple(Room(*r) for r in rooms))


# 1. plot_only -> plot + tree only
def emit_plot(path):
    doc = ezdxf.new("R2010"); msp = doc.modelspace()
    msp.add_lwpolyline(list(PLOT.boundary) + [PLOT.boundary[0]], close=True,
                       dxfattribs={"layer": "PLOT", "color": RED})
    tcx, tcy = PLOT.tree_center
    msp.add_circle((tcx, tcy), PLOT.tree_radius, dxfattribs={"layer": "TREE", "color": GREEN})
    msp.add_circle((tcx, tcy), PLOT.tree_radius + 3.0,
                   dxfattribs={"layer": "TREE", "color": GREEN, "linetype": "DASHED"})
    path.parent.mkdir(parents=True, exist_ok=True); doc.saveas(str(path))


emit_plot(OUT / "plot_only.dxf")

# 2. labeled_result -> exterior house only (plot + tree + house + door + setbacks)
dxf_emitter.emit_dxf(house_of(FP, DOOR), PLOT, OUT / "labeled_result.dxf", max_legal_area=4060.0)

# 3. milp_result -> MILP interior (gap-filled), full layout
res = interior_milp.solve_layout(FP, DOOR, SBC)
milp_rooms = list(res.layout.rooms) + interior_fill.fill_gaps(FP, list(res.layout.rooms))
dxf_full.emit_full_dxf(house_of(FP, DOOR), InteriorLayout(FP, DOOR, tuple(milp_rooms)),
                       PLOT, OUT / "milp_result.dxf")

# 4-7. the four vibe templates
for vibe, fname in [("Balanced", "vibe_balanced"), ("Family home", "vibe_family"),
                    ("Entertainer", "vibe_entertainer"), ("Work from home", "vibe_wfh")]:
    dxf_full.emit_full_dxf(house_of(FP, DOOR), templates.build(FP, DOOR, vibe),
                           PLOT, OUT / f"{fname}.dxf")

# 8. before_block -> the wasted-corridor reconstruction
before_block = lay([
    ("Bedroom 1", "bedroom", 5, 20, 25, 40), ("Living", "living", 27, 20, 47, 40),
    ("Kitchen", "kitchen", 49, 20, 68, 40),
    ("Bath 1", "bathroom", 5, 44, 18, 54), ("Bath 2", "bathroom", 55, 44, 68, 54),
    ("Bedroom 2", "bedroom", 5, 56, 27, 78), ("Bedroom 3", "bedroom", 46, 56, 68, 78),
    ("Corridor", "corridor", 27, 42, 46, 78),
])
dxf_full.emit_full_dxf(house_of(FP, DOOR), before_block, PLOT, OUT / "before_block.dxf")

# 9. studio_layout -> copy the app's live output if present, else the MILP one
src = Path("output/studio_layout.dxf")
dst = OUT / "studio_layout.dxf"
if src.exists():
    dst.write_bytes(src.read_bytes())
else:
    dxf_full.emit_full_dxf(house_of(FP, DOOR), InteriorLayout(FP, DOOR, tuple(milp_rooms)),
                           PLOT, dst)

print("wrote DXF files to", OUT.resolve())
for p in sorted(OUT.glob("*.dxf")):
    print("  ", p.name)
