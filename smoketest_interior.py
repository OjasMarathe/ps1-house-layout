"""Smoke test for the interior verifier — no LLM/API calls.

Generates the balanced MILP/CBC layout (open-mode: rooms + open/flex space) and
mutates it to trip each rule. Also checks that full-coverage (tiling) mode flags
the open space as under-fill. Run:
    python smoketest_interior.py
"""

from constraints import SBC
from interior_verifier_z3 import Room, InteriorLayout, check_interior
from interior_milp import solve_layout

FP = (5.0, 20.0, 68.0, 78.0)
DOOR = (40.0, 20.0)


def rules(layout, full_cov=False) -> set[str]:
    return {v.rule for v in check_interior(layout, SBC, require_full_coverage=full_cov)}


def repl(rooms, name, **kw):
    out = []
    for r in rooms:
        if r.name == name:
            out.append(Room(r.name, kw.get("kind", r.kind),
                            kw.get("x_min", r.x_min), kw.get("y_min", r.y_min),
                            kw.get("x_max", r.x_max), kw.get("y_max", r.y_max)))
        else:
            out.append(r)
    return tuple(out)


def main() -> int:
    base = solve_layout(FP, DOOR, SBC).layout
    rs = base.rooms
    kit = next(r for r in rs if r.kind == "kitchen")
    bed1 = next(r for r in rs if r.name == "Bedroom 1")

    # (label, layout, expected_rule|None, full_coverage_mode)
    cases = [
        ("valid layout (open mode)", base, None, False),
        ("under-fill flagged (tiling mode)", base, "coverage", True),
        ("overlap", InteriorLayout(FP, DOOR, repl(rs, "Bath 1", x_max=bed1.x_max)), "no_overlap", False),
        ("wrong room count", InteriorLayout(FP, DOOR, repl(rs, "Bedroom 3", kind="kitchen")), "room_count", False),
        ("door not in living", InteriorLayout(FP, (66.0, 20.0), rs), "door_in_living", False),
        ("bath max side", InteriorLayout(FP, DOOR, repl(rs, "Bath 1", x_max=rs[0].x_min + 33)), "room_max_side", False),
        ("ensuite detached", InteriorLayout(FP, DOOR,
            repl(rs, "Bath 2", x_min=20.0, x_max=28.0, y_min=bed1.y_max + 1, y_max=bed1.y_max + 11)),
            "ensuite_attached", False),
        ("bath adjacent to kitchen", InteriorLayout(FP, DOOR,
            repl(rs, "Bath 2", x_min=kit.x_min + 2, x_max=kit.x_min + 10, y_min=kit.y_max, y_max=kit.y_max + 10)),
            "bath_not_adj_kitchen", False),
    ]

    ok = True
    for label, layout, expect, fc in cases:
        rset = rules(layout, full_cov=fc)
        passed = (len(rset) == 0) if expect is None else (expect in rset)
        ok = ok and passed
        detail = "0 violations" if not rset else ", ".join(sorted(rset))
        want = "(clean)" if expect is None else f"expect '{expect}'"
        print(f"  [{'PASS' if passed else 'FAIL'}] {label:34s} {want:26s} -> {detail}")

    print("\nALL PASS" if ok else "\nSOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
