"""Turn leftover footprint space into distributed circulation (halls).

The solver/LLM place the named rooms; whatever footprint area they don't cover
should read as pathways/halls woven between rooms — NOT one big empty chunk.
`fill_gaps` grids the footprint, finds uncovered cells, and greedily extracts
axis-aligned "Hall" rectangles that tile the leftover. Adding these to a layout
pushes coverage to ~100% with circulation spread where the gaps actually are.
"""
from math import ceil

from interior_verifier_z3 import Room


def _covered_grid(footprint, rooms, res):
    X0, Y0, X1, Y1 = footprint
    nx = int(round((X1 - X0) / res))
    ny = int(round((Y1 - Y0) / res))
    free = [[True] * nx for _ in range(ny)]
    for r in rooms:
        j0 = max(0, int((r.x_min - X0) / res))
        j1 = min(nx, int(ceil((r.x_max - X0) / res)))
        i0 = max(0, int((r.y_min - Y0) / res))
        i1 = min(ny, int(ceil((r.y_max - Y0) / res)))
        for i in range(i0, i1):
            cy = Y0 + (i + 0.5) * res
            for j in range(j0, j1):
                cx = X0 + (j + 0.5) * res
                if (r.x_min - 1e-9 <= cx <= r.x_max + 1e-9
                        and r.y_min - 1e-9 <= cy <= r.y_max + 1e-9):
                    free[i][j] = False
    return free, nx, ny


def fill_gaps(footprint, rooms, res: float = 1.0, min_area: float = 12.0,
              min_side: float = 4.0, max_halls: int = 8) -> list[Room]:
    """Return new 'Hall' (corridor-kind) Rooms covering the uncovered footprint.

    Greedy maximal-rectangle sweep over the uncovered grid cells. Only halls at
    least `min_side` ft wide are kept (a hall must be walkable); thinner slivers
    are left as open space."""
    X0, Y0, X1, Y1 = footprint
    free, nx, ny = _covered_grid(footprint, rooms, res)

    rects: list[tuple[float, float, float, float, float]] = []  # (area, x0,y0,x1,y1)
    for i in range(ny):
        for j in range(nx):
            if not free[i][j]:
                continue
            # widen
            w = 0
            while j + w < nx and free[i][j + w]:
                w += 1
            # deepen while the full width stays free
            h = 0
            while i + h < ny and all(free[i + h][j + k] for k in range(w)):
                h += 1
            for a in range(h):
                for b in range(w):
                    free[i + a][j + b] = False
            rx0, ry0 = X0 + j * res, Y0 + i * res
            rx1, ry1 = X0 + (j + w) * res, Y0 + (i + h) * res
            rects.append(((rx1 - rx0) * (ry1 - ry0), rx0, ry0, rx1, ry1))

    rects = [r for r in rects
             if r[0] >= min_area and (r[3] - r[1]) >= min_side and (r[4] - r[2]) >= min_side]
    rects.sort(reverse=True)            # biggest gaps first
    halls = []
    for idx, (_, x0, y0, x1, y1) in enumerate(rects[:max_halls], 1):
        halls.append(Room(f"Hall {idx}", "corridor",
                          round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)))
    return halls


if __name__ == "__main__":
    from constraints import SBC
    from interior_milp import solve_layout
    fp = (5.0, 20.0, 68.0, 78.0)
    res = solve_layout(fp, (40.0, 20.0), SBC)
    before = sum(r.area for r in res.layout.rooms) / res.layout.footprint_area
    halls = fill_gaps(fp, res.layout.rooms)
    after = (sum(r.area for r in res.layout.rooms) + sum(h.area for h in halls)) / res.layout.footprint_area
    print(f"rooms before: {before*100:.0f}% fill")
    print(f"added {len(halls)} hall(s): " + ", ".join(f"{h.width:.0f}×{h.depth:.0f}" for h in halls))
    print(f"after fill: {after*100:.0f}% fill")
