"""Human-in-the-loop interior layout.

The MILP/CBC solver enforces the code rules; YOU set the comfort choices (room
sizes). Each round it solves, renders a PNG, Z3-verifies, prints the schedule,
and waits for your adjustment. Run in a real terminal:

    python interior_hitl.py

Commands at the prompt:
    living_w 24        kitchen_w 16        public_depth 18
    bed_depth 22       bath_w 8            bath_depth 12
    bath 8x12          (sets bath_w and bath_depth together)
    reset              (back to balanced defaults)
    accept             (write the .dxf and finish)
    quit               (exit without writing)
"""

import sys
from pathlib import Path

from constraints import SBC
from plot import PLOT
from verifier_z3 import HouseGeometry
import interior_milp
import interior_verifier_z3
import interior_render
import dxf_full

OUT = Path(__file__).parent / "output"
FOOTPRINT = (5.0, 20.0, 68.0, 78.0)   # converged exterior footprint (63 × 58 ft)
DOOR = (40.0, 20.0)

_KEYS = {"living_w", "kitchen_w", "public_depth", "bed_depth", "bath_w", "bath_depth"}
_ALIASES = {"living": "living_w", "kitchen": "kitchen_w",
            "bedroom_depth": "bed_depth", "bedroom": "bed_depth"}


def _print_schedule(res, viol):
    p = res.params
    print(f"\n  Sizes: public_depth={p['public_depth']:.0f}  living_w={p['living_w']:.0f}  "
          f"kitchen_w={p['kitchen_w']:.0f}  bed_depth={p['bed_depth']:.0f}  "
          f"bath={p['bath_w']:.0f}x{p['bath_depth']:.0f}")
    print(f"  {'Room':12s}{'W×H':>10s}{'Area':>9s}")
    for r in res.layout.rooms:
        print(f"  {r.name:12s}{f'{r.width:.0f}×{r.depth:.0f}':>10s}{f'{r.area:.0f}':>9s}")
    print(f"  fill {res.fill_frac*100:.0f}% of footprint  "
          f"({(1-res.fill_frac)*100:.0f}% open/flex)")
    if viol:
        print("  ❌ Z3 violations: " + ", ".join(sorted({v.rule for v in viol})))
    else:
        print("  ✅ Z3: all interior rules satisfied (open mode)")


def _apply(params, line) -> str | None:
    """Mutate params in place from a command line. Return error string or None."""
    toks = line.split()
    if not toks:
        return "empty"
    head = toks[0].lower()
    if head == "bath" and len(toks) == 2 and "x" in toks[1].lower():
        try:
            w, h = toks[1].lower().split("x")
            params["bath_w"], params["bath_depth"] = float(w), float(h)
            return None
        except ValueError:
            return "use: bath 8x12"
    key = _ALIASES.get(head, head)
    if key in _KEYS and len(toks) == 2:
        try:
            params[key] = float(toks[1])
            return None
        except ValueError:
            return f"{toks[1]} is not a number"
    return f"unknown command '{line}'"


def main() -> int:
    params = interior_milp.default_params(FOOTPRINT)
    last_good = dict(params)
    print("== Human-in-the-loop interior layout ==")
    print(f"   footprint {FOOTPRINT[2]-FOOTPRINT[0]:.0f} × {FOOTPRINT[3]-FOOTPRINT[1]:.0f} ft, "
          f"door {DOOR}\n   (type 'help' for commands)")

    while True:
        try:
            res = interior_milp.solve_layout(FOOTPRINT, DOOR, SBC, params=params)
        except RuntimeError as e:
            print(f"\n  ⚠️  {e}\n  reverting to the last working sizes.")
            params = dict(last_good)
            continue
        last_good = dict(params)
        viol = interior_verifier_z3.check_interior(res.layout, SBC, require_full_coverage=False)
        png = interior_render.render(res.layout, OUT / "slides" / "hitl_layout.png",
                                     title="Interior (human-in-the-loop)", fill_frac=res.fill_frac)
        _print_schedule(res, viol)
        print(f"  rendered → {png}")

        try:
            cmd = input("\n  adjust / accept / reset / quit > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  bye."); return 0
        low = cmd.lower()
        if low in ("accept", "a", "ok", "done"):
            house = HouseGeometry(
                corners=((FOOTPRINT[0], FOOTPRINT[1]), (FOOTPRINT[2], FOOTPRINT[1]),
                         (FOOTPRINT[2], FOOTPRINT[3]), (FOOTPRINT[0], FOOTPRINT[3])), door=DOOR)
            dxf = dxf_full.emit_full_dxf(house, res.layout, PLOT, OUT / "hitl_layout.dxf")
            print(f"\n  ✅ accepted. .dxf → {dxf}\n     final PNG → {png}")
            return 0
        if low in ("quit", "q", "exit"):
            print("  bye."); return 0
        if low in ("reset", "r"):
            params = interior_milp.default_params(FOOTPRINT); continue
        if low in ("help", "h", "?"):
            print(__doc__); continue
        err = _apply(params, cmd)
        if err:
            print(f"  ?? {err}")


if __name__ == "__main__":
    sys.exit(main())
