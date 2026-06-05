"""Z3-backed interior verifier — the deterministic judge for the floor plan.

The exterior verifier (verifier_z3.py) checks a single house *footprint*. This
module checks the *interior subdivision* of that footprint into rooms. Given a
concrete `InteriorLayout` (a list of axis-aligned `Room` rectangles) it returns
a list of `InteriorViolation` records; an empty list means the floor plan is
legal and well-formed.

Split of labor (same convention as verifier_z3.py):
  - Scalar/algebraic checks (min area, min side, doorway width) go through Z3
    via `_violated`, so the SMT solver stays the single source of truth on the
    numeric comparisons.
  - Pure geometry (rectangle overlap, exact tiling, adjacency-graph
    connectivity) is plain Python — Z3 adds nothing when the rectangles are
    already concrete numbers.

The rule set:
  R1  room_count        — exactly 3 bedroom + 1 kitchen + 2 bathroom + 1 living
  R2  room_in_footprint — every room lies inside the verified house footprint
  R3  room_min_area     — every room meets its program minimum area
  R4  room_min_side     — no room has a horizontal dimension below its minimum
  R5  no_overlap        — no two rooms overlap (positive-area intersection)
  R6  exact_tiling      — rooms cover the footprint with no gaps
  R7  door_in_living    — the front door opens into the living room (egress)
  R8  kitchen_by_living — kitchen shares a real wall with the living room
  R9  wet_wall          — kitchen shares a wall with at least one bathroom
  R10 connected         — every room is reachable from every other (doorways)
"""

from dataclasses import dataclass

from verifier_z3 import _violated, HouseGeometry  # reuse the Z3 scalar judge
from constraints import SBCConstraints
import rooms as program

EPS = 1e-6


# --------------------------------------------------------------------------- #
#  Data types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Room:
    name: str          # e.g. "Bedroom 1"
    kind: str          # "bedroom" | "kitchen" | "bathroom" | "living"
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:   # E-W extent
        return self.x_max - self.x_min

    @property
    def depth(self) -> float:   # N-S extent
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.depth

    @property
    def min_side(self) -> float:
        return min(self.width, self.depth)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)


@dataclass(frozen=True)
class InteriorLayout:
    footprint: tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max)
    door: tuple[float, float]
    rooms: tuple[Room, ...]

    @property
    def footprint_area(self) -> float:
        x0, y0, x1, y1 = self.footprint
        return (x1 - x0) * (y1 - y0)


@dataclass(frozen=True)
class InteriorViolation:
    rule: str
    measured_ft: float
    required_ft: float
    message: str


# --------------------------------------------------------------------------- #
#  Geometry helpers (pure Python)
# --------------------------------------------------------------------------- #
def _overlap_area(a: Room, b: Room) -> float:
    ox = min(a.x_max, b.x_max) - max(a.x_min, b.x_min)
    oy = min(a.y_max, b.y_max) - max(a.y_min, b.y_min)
    if ox > EPS and oy > EPS:
        return ox * oy
    return 0.0


def _shared_wall(a: Room, b: Room) -> float:
    """Length of the wall the two rooms share (0 if they only touch at a corner
    or don't touch at all). Assumes the rooms do not overlap."""
    # Vertical shared wall: a's east edge == b's west edge (or vice versa)
    if abs(a.x_max - b.x_min) < EPS or abs(b.x_max - a.x_min) < EPS:
        lo = max(a.y_min, b.y_min)
        hi = min(a.y_max, b.y_max)
        return max(0.0, hi - lo)
    # Horizontal shared wall: a's north edge == b's south edge (or vice versa)
    if abs(a.y_max - b.y_min) < EPS or abs(b.y_max - a.y_min) < EPS:
        lo = max(a.x_min, b.x_min)
        hi = min(a.x_max, b.x_max)
        return max(0.0, hi - lo)
    return 0.0


def _connected_components(rooms_list: list[Room], min_wall: float) -> list[set[int]]:
    """Indices grouped by reachability through walls of length >= min_wall."""
    n = len(rooms_list)
    adj: dict[int, set[int]] = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if _shared_wall(rooms_list[i], rooms_list[j]) >= min_wall - EPS:
                adj[i].add(j)
                adj[j].add(i)
    seen: set[int] = set()
    comps: list[set[int]] = []
    for start in range(n):
        if start in seen:
            continue
        stack, comp = [start], set()
        while stack:
            u = stack.pop()
            if u in comp:
                continue
            comp.add(u)
            seen.add(u)
            stack.extend(adj[u] - comp)
        comps.append(comp)
    return comps


# --------------------------------------------------------------------------- #
#  The check
# --------------------------------------------------------------------------- #
def check_interior(layout: InteriorLayout, sbc: SBCConstraints) -> list[InteriorViolation]:
    """Return list of interior violations; empty list == legal floor plan."""
    v: list[InteriorViolation] = []
    rs = list(layout.rooms)
    fx0, fy0, fx1, fy1 = layout.footprint
    door_x, door_y = layout.door

    # --- R1: room counts ----------------------------------------------------
    counts: dict[str, int] = {}
    for r in rs:
        counts[r.kind] = counts.get(r.kind, 0) + 1
    for kind, need in program.REQUIRED_COUNT.items():
        have = counts.get(kind, 0)
        if have != need:
            v.append(InteriorViolation(
                rule="room_count",
                measured_ft=float(have), required_ft=float(need),
                message=(f"Need exactly {need} {kind}(s); layout has {have}. "
                         f"Program: 3 bedroom + 1 kitchen + 2 bathroom + 1 living.")))
    unknown = sorted({r.kind for r in rs} - set(program.REQUIRED_COUNT))
    for k in unknown:
        v.append(InteriorViolation(
            rule="room_count", measured_ft=0.0, required_ft=0.0,
            message=f"Unknown room kind '{k}'. Allowed: bedroom, kitchen, bathroom, living."))

    # --- R2/R3/R4: per-room containment, min area, min side -----------------
    for r in rs:
        # containment in footprint (algebra via Z3)
        if (_violated(r.x_min, fx0) or _violated(fx1, r.x_max)
                or _violated(r.y_min, fy0) or _violated(fy1, r.y_max)):
            v.append(InteriorViolation(
                rule="room_in_footprint", measured_ft=0.0, required_ft=0.0,
                message=(f"{r.name} ({r.x_min:.1f},{r.y_min:.1f})-"
                         f"({r.x_max:.1f},{r.y_max:.1f}) sticks outside the house "
                         f"footprint x∈[{fx0:.1f},{fx1:.1f}], y∈[{fy0:.1f},{fy1:.1f}].")))
        spec = program.SPEC_BY_KIND.get(r.kind)
        if spec is None:
            continue
        if _violated(r.area, spec.min_area_ft2):
            v.append(InteriorViolation(
                rule="room_min_area",
                measured_ft=float(r.area), required_ft=float(spec.min_area_ft2),
                message=(f"{r.name} is {r.area:.0f} sq ft; a {r.kind} needs "
                         f"≥ {spec.min_area_ft2:.0f} sq ft.")))
        if _violated(r.min_side, spec.min_side_ft):
            v.append(InteriorViolation(
                rule="room_min_side",
                measured_ft=float(r.min_side), required_ft=float(spec.min_side_ft),
                message=(f"{r.name} narrowest side is {r.min_side:.1f} ft; a "
                         f"{r.kind} needs every side ≥ {spec.min_side_ft:.0f} ft "
                         "(no slivers).")))

    # --- R5: pairwise non-overlap -------------------------------------------
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            ov = _overlap_area(rs[i], rs[j])
            if ov > EPS:
                v.append(InteriorViolation(
                    rule="no_overlap",
                    measured_ft=float(ov), required_ft=0.0,
                    message=(f"{rs[i].name} and {rs[j].name} overlap by "
                             f"{ov:.0f} sq ft. Rooms must be disjoint.")))

    # --- R6: exact tiling (no gaps) -----------------------------------------
    # With containment (R2) and non-overlap (R5) holding, the rooms tile the
    # footprint exactly iff their areas sum to the footprint area.
    total = sum(r.area for r in rs)
    fp_area = layout.footprint_area
    if abs(total - fp_area) > 1.0:  # 1 sq ft slop
        gap = fp_area - total
        if gap > 0:
            msg = (f"Rooms cover {total:.0f} sq ft but the footprint is "
                   f"{fp_area:.0f} sq ft — {gap:.0f} sq ft of dead/unassigned "
                   "space. Rooms must tile the whole footprint (no gaps).")
        else:
            msg = (f"Rooms cover {total:.0f} sq ft, more than the "
                   f"{fp_area:.0f} sq ft footprint — they spill out or overlap.")
        v.append(InteriorViolation(
            rule="exact_tiling", measured_ft=float(total), required_ft=float(fp_area),
            message=msg))

    # --- R7: front door opens into the living room --------------------------
    livings = [r for r in rs if r.kind == "living"]
    if livings:
        lv = livings[0]
        on_south = abs(lv.y_min - fy0) < 0.5 and abs(door_y - fy0) < 0.5
        margin = sbc.door_corner_margin_ft
        in_span = (lv.x_min + margin - EPS) <= door_x <= (lv.x_max - margin + EPS)
        if not (on_south and in_span):
            v.append(InteriorViolation(
                rule="door_in_living",
                measured_ft=float(door_x), required_ft=float(margin),
                message=(f"Front door ({door_x:.1f},{door_y:.1f}) must open into "
                         f"the living room on the south wall. {lv.name} spans "
                         f"x∈[{lv.x_min:.1f},{lv.x_max:.1f}], south edge y="
                         f"{lv.y_min:.1f}. Place the living room across the door, "
                         f"inset ≥ {margin:.0f} ft from its side walls.")))

    # --- R8: kitchen shares a wall with the living room ---------------------
    kitchens = [r for r in rs if r.kind == "kitchen"]
    if kitchens and livings:
        kt = kitchens[0]
        wall = max(_shared_wall(kt, lv) for lv in livings)
        if _violated(wall, program.DOORWAY_FT):
            v.append(InteriorViolation(
                rule="kitchen_by_living",
                measured_ft=float(wall), required_ft=float(program.DOORWAY_FT),
                message=(f"Kitchen shares only {wall:.1f} ft of wall with the "
                         f"living room; need ≥ {program.DOORWAY_FT:.1f} ft "
                         "(open-plan kitchen/living adjacency).")))

    # --- R9: wet wall — kitchen adjacent to a bathroom ----------------------
    baths = [r for r in rs if r.kind == "bathroom"]
    if kitchens and baths:
        kt = kitchens[0]
        wall = max(_shared_wall(kt, b) for b in baths)
        if _violated(wall, program.DOORWAY_FT):
            v.append(InteriorViolation(
                rule="wet_wall",
                measured_ft=float(wall), required_ft=float(program.DOORWAY_FT),
                message=(f"Kitchen shares only {wall:.1f} ft of wall with any "
                         f"bathroom; need ≥ {program.DOORWAY_FT:.1f} ft so the "
                         "plumbing stacks share a wet wall.")))

    # --- R10: connectivity — every room reachable via doorways --------------
    if len(rs) >= 2:
        comps = _connected_components(rs, program.DOORWAY_FT)
        if len(comps) > 1:
            biggest = max(comps, key=len)
            stranded = [rs[i].name for c in comps if c is not biggest for i in c]
            v.append(InteriorViolation(
                rule="connected",
                measured_ft=float(len(comps)), required_ft=1.0,
                message=(f"Floor plan splits into {len(comps)} disconnected "
                         f"groups; {', '.join(stranded)} cannot be reached "
                         f"through a ≥ {program.DOORWAY_FT:.1f} ft doorway. "
                         "Every room must connect to the rest.")))

    return v


def passes_interior(layout: InteriorLayout, sbc: SBCConstraints) -> bool:
    return len(check_interior(layout, sbc)) == 0
