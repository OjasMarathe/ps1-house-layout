"""Render the before/after figures used in the Layout Studio deck."""
from pathlib import Path

from interior_verifier_z3 import Room, InteriorLayout
import interior_render
import templates

FP = (5.0, 20.0, 68.0, 78.0)
DOOR = (40.0, 20.0)
OUT = Path("output/slides")
OUT.mkdir(parents=True, exist_ok=True)


def lay(rooms):
    return InteriorLayout(FP, DOOR, tuple(Room(*r) for r in rooms))


# --- BEFORE 1: tiny bedrooms, enormous living/kitchen (first MILP) ----------
before_imbalance = lay([
    ("Living", "living", 5, 20, 42, 59), ("Kitchen", "kitchen", 42, 20, 68, 59),
    ("Corridor", "corridor", 5, 59, 68, 63),
    ("Bath 1", "bathroom", 5, 63, 11, 78), ("Bedroom 1", "bedroom", 11, 63, 28, 78),
    ("Bedroom 3", "bedroom", 28, 63, 45, 78), ("Bedroom 2", "bedroom", 45, 63, 62, 78),
    ("Bath 2", "bathroom", 62, 63, 68, 78),
])
ff = sum(r.area for r in before_imbalance.rooms) / before_imbalance.footprint_area
interior_render.render(before_imbalance, OUT / "before_imbalance.png",
                       title="Before — living 1443 vs bedroom 255", fill_frac=ff)

# --- BEFORE 2: big empty 'corridor' block + long bedrooms -------------------
before_block = lay([
    ("Bedroom 1", "bedroom", 5, 20, 25, 40), ("Living", "living", 27, 20, 47, 40),
    ("Kitchen", "kitchen", 49, 20, 68, 40),
    ("Bath 1", "bathroom", 5, 44, 18, 54), ("Bath 2", "bathroom", 55, 44, 68, 54),
    ("Bedroom 2", "bedroom", 5, 56, 27, 78), ("Bedroom 3", "bedroom", 46, 56, 68, 78),
    ("Corridor", "corridor", 27, 42, 46, 78),   # the big mislabeled block
])
ff = sum(r.area for r in before_block.rooms) / before_block.footprint_area
interior_render.render(before_block, OUT / "before_block.png",
                       title="Before — a big block of wasted 'corridor'", fill_frac=ff)

# --- AFTER: the four current tiled vibe templates ---------------------------
for vibe, fname in [("Balanced", "vibe_balanced"), ("Family home", "vibe_family"),
                    ("Entertainer", "vibe_entertainer"), ("Work from home", "vibe_wfh")]:
    L = templates.build(FP, DOOR, vibe)
    ff = sum(r.area for r in L.rooms) / L.footprint_area
    interior_render.render(L, OUT / f"{fname}.png", title=f"{vibe} — tiled, square-ish, verified",
                           fill_frac=ff)

print("wrote:", *(p.name for p in sorted(OUT.glob("before_*.png"))),
      *(f"{n}.png" for n in ("vibe_balanced", "vibe_family", "vibe_entertainer", "vibe_wfh")))
