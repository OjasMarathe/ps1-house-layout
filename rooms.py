"""The building 'program' — what rooms the interior must contain.

The exterior pipeline (plot.py / optimizer_z3.py / verifier_z3.py) produces a
single SBC-legal house *footprint*. The interior stage then has to subdivide
that footprint into actual rooms. This file encodes WHICH rooms are required
and the minimum size each must be, as plain data — exactly the same philosophy
as constraints.py (cite a defensible source, encode a small subset).

Requirement (from the assignment brief): the interior must contain
    3 bedrooms + 1 kitchen + 2 bathrooms + 1 living room   (7 rooms).

Minimum sizes are loosely modeled on the International Residential Code (IRC):
  - IRC R304: habitable rooms ≥ 70 sq ft, with no horizontal dimension < 7 ft.
  - A primary "living" habitable room ≥ 120 sq ft (IRC R304.1 historic value).
  - Bathrooms / kitchens are non-habitable service spaces with smaller minimums.
We round these up to comfortable, defensible residential numbers.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoomSpec:
    kind: str          # "bedroom" | "kitchen" | "bathroom" | "living"
    count: int         # how many of this kind are required
    min_area_ft2: float
    min_side_ft: float  # no horizontal dimension may be smaller than this
    label: str          # human-friendly display name stem


# The required interior program. Order matters only for display.
PROGRAM: tuple[RoomSpec, ...] = (
    RoomSpec(kind="living",   count=1, min_area_ft2=200.0, min_side_ft=12.0, label="Living"),
    RoomSpec(kind="kitchen",  count=1, min_area_ft2=80.0,  min_side_ft=7.0,  label="Kitchen"),
    RoomSpec(kind="bathroom", count=2, min_area_ft2=40.0,  min_side_ft=5.0,  label="Bath"),
    RoomSpec(kind="bedroom",  count=3, min_area_ft2=100.0, min_side_ft=9.0,  label="Bedroom"),
)

# Quick lookups
SPEC_BY_KIND: dict[str, RoomSpec] = {s.kind: s for s in PROGRAM}
REQUIRED_COUNT: dict[str, int] = {s.kind: s.count for s in PROGRAM}
TOTAL_ROOMS: int = sum(s.count for s in PROGRAM)  # 7

# Minimum floor area the program needs (a feasibility lower bound). The
# exterior footprint is ~3,770 sq ft, far above this, so a legal interior
# always exists — the interior loop is about a *good* partition, not a
# feasibility miracle.
MIN_TOTAL_AREA: float = sum(s.min_area_ft2 * s.count for s in PROGRAM)

# A doorway/shared-wall must be at least this long for two rooms to count as
# "connected" (you can't walk through a 6-inch gap). Used by adjacency rules.
DOORWAY_FT: float = 2.5


if __name__ == "__main__":
    print("Interior program:")
    for s in PROGRAM:
        print(f"  {s.count}× {s.kind:9s} — min {s.min_area_ft2:.0f} sq ft, "
              f"min side {s.min_side_ft:.0f} ft")
    print(f"  total rooms      : {TOTAL_ROOMS}")
    print(f"  min total area   : {MIN_TOTAL_AREA:.0f} sq ft")
