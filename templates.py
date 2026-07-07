"""Hand-designed starting layouts, one per 'vibe'.

Each template TILES the footprint: the named rooms fill it and the only leftover
is a thin hallway band, so there are no big empty "corridor" blocks. Bedrooms
are square-ish (aspect well under 1.5) and no two bedrooms share a wall.

Structure (all share it, so every plan is valid by construction, but the cut
positions differ per vibe so the four look clearly different):

    BOTTOM band(y 20–50): [ Bedroom 1 | Living (door) | Kitchen ]  (tall band, so
                            Living is the biggest room — larger than every bedroom)
    HALL band  (y 50–54): full-width 4 ft corridor (connects everything)
    TOP band   (y 54–78): [ Bedroom 2 | baths column | Bedroom 3 ]

Living always spans the front door. Bedroom 1 (bottom) is separated from
Bedrooms 2 & 3 (top) by the hall; Bedrooms 2 & 3 are separated by the bath
column — so no bedrooms are adjacent. Coordinates are authored for the
canonical 63 x 58 ft footprint and scaled if a different one is passed.
"""
from interior_verifier_z3 import Room, InteriorLayout
import interior_fill

CANON = (5.0, 20.0, 68.0, 78.0)
CANON_DOOR = (40.0, 20.0)

# Per vibe: cut positions on the canonical footprint.
#   b1,b2 = bottom band cuts (Bed1 | Living | Kitchen)
#   c1,c2 = top band cuts    (Bed2 | bath-column | Bed3)
# Bands: bottom y20–50, hall y50–54, top y54–78. Bath column splits at y66.
# Tuned so Living > every bedroom in all four vibes (Floor Plan acceptance rule).
VIBE_CUTS = {
    "Balanced":       dict(b1=25, b2=47, c1=30, c2=43),   # even, biggest living
    "Family home":    dict(b1=25, b2=46, c1=30, c2=43),   # bedrooms close behind living
    "Entertainer":    dict(b1=22, b2=50, c1=29, c2=42),   # large living, compact Bed1
    "Work from home": dict(b1=28, b2=52, c1=29, c2=42),   # big bottom-left study-bedroom
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def clamp_cuts(cuts: dict) -> dict:
    """Force cut positions into a valid range (door in living, min room widths,
    bath column 8-15 ft). Guarantees build_cuts produces a Z3-valid layout."""
    b1 = _clamp(cuts["b1"], 12, 38)            # Bed1 >= 7, living spans door (<=38)
    b2 = _clamp(cuts["b2"], max(b1 + 8, 42), 61)   # living >= 8, door (>=42), kitchen >= 7
    c1 = _clamp(cuts["c1"], 12, 50)            # Bed2 >= 7
    c2 = _clamp(cuts["c2"], c1 + 8, min(c1 + 15, 61))  # bath col 8-15, Bed3 >= 7
    return dict(b1=b1, b2=b2, c1=c1, c2=c2)


def adjust(cuts: dict, action: str) -> dict:
    """Deterministic, always-valid 'quick change' on the current cuts."""
    c = dict(cuts)
    if action == "beds":          # bigger bedrooms (shrink the bath column)
        c["b1"] += 2; c["c1"] += 2; c["c2"] -= 2
    elif action == "living":      # bigger living room
        c["b1"] -= 2; c["b2"] += 2
    elif action == "kitchen":     # bigger kitchen
        c["b2"] -= 3
    elif action == "baths":       # bigger bathrooms (widen the column)
        c["c1"] -= 1; c["c2"] += 1
    elif action == "even":        # reset to the symmetric layout
        c = dict(VIBE_CUTS["Balanced"])
    return clamp_cuts(c)


def _rooms(cuts) -> list[tuple]:
    b1, b2, c1, c2 = cuts["b1"], cuts["b2"], cuts["c1"], cuts["c2"]
    return [
        ("Bedroom 1", "bedroom",   5, 20, b1, 50),
        ("Living",    "living",   b1, 20, b2, 50),
        ("Kitchen",   "kitchen",  b2, 20, 68, 50),
        ("Corridor",  "corridor",  5, 50, 68, 54),
        ("Bedroom 2", "bedroom",   5, 54, c1, 78),
        ("Bath 1",    "bathroom", c1, 54, c2, 66),
        ("Bath 2",    "bathroom", c1, 66, c2, 78),
        ("Bedroom 3", "bedroom",  c2, 54, 68, 78),
    ]


def build(footprint, door, vibe: str) -> InteriorLayout:
    return build_cuts(footprint, door, VIBE_CUTS.get(vibe, VIBE_CUTS["Balanced"]))


def build_cuts(footprint, door, cuts: dict) -> InteriorLayout:
    cuts = clamp_cuts(cuts)
    cx0, cy0, cx1, cy1 = CANON
    fx0, fy0, fx1, fy1 = footprint
    sx = (fx1 - fx0) / (cx1 - cx0)
    sy = (fy1 - fy0) / (cy1 - cy0)

    def tx(x): return round(fx0 + (x - cx0) * sx, 2)
    def ty(y): return round(fy0 + (y - cy0) * sy, 2)

    rooms = [Room(n, k, tx(x0), ty(y0), tx(x1), ty(y1))
             for (n, k, x0, y0, x1, y1) in _rooms(cuts)]
    halls = interior_fill.fill_gaps(footprint, rooms)   # usually none — it tiles
    return InteriorLayout(footprint=footprint, door=door, rooms=tuple(rooms + halls))


if __name__ == "__main__":
    from constraints import SBC
    from interior_verifier_z3 import check_interior, _shared_wall
    fp, door = CANON, CANON_DOOR
    for vibe in VIBE_CUTS:
        lay = build(fp, door, vibe)
        beds = [r for r in lay.rooms if r.kind == "bedroom"]
        adj = [(a.name, b.name) for i, a in enumerate(beds) for b in beds[i+1:] if _shared_wall(a, b) > 0.5]
        corr = [r for r in lay.rooms if r.kind == "corridor"]
        viol = check_interior(lay, SBC, mode="freeform", require_full_coverage=True)
        asp = [f"{r.width:.0f}x{r.depth:.0f}({max(r.width,r.depth)/min(r.width,r.depth):.2f})" for r in beds]
        print(f"\n{vibe}: living {[r.area for r in lay.rooms if r.kind=='living'][0]:.0f}  "
              f"beds {', '.join(asp)}")
        print(f"  bedroom pairs sharing a wall: {adj if adj else 'none ✓'}")
        print(f"  corridor pieces: {len(corr)}  biggest {max((r.area for r in corr), default=0):.0f} sq ft  "
              f"fill {sum(r.area for r in lay.rooms)/lay.footprint_area*100:.0f}%")
        print(f"  Z3 freeform: {'PASS ✓' if not viol else 'FAIL → ' + ', '.join(sorted({v.rule for v in viol}))}")
