"""Smoke test for the interior verifier — no LLM/API calls.

Generates the MILP/CBC reference layout (which must pass the full constraint
set) and then mutates it to trigger each rule, asserting the expected
violation fires. Run:
    python smoketest_interior.py
"""

from constraints import SBC
from interior_verifier_z3 import Room, InteriorLayout, check_interior
from interior_milp import solve_layout

FP = (5.0, 20.0, 68.0, 78.0)
DOOR = (40.0, 20.0)


def rules(layout) -> set[str]:
    return {v.rule for v in check_interior(layout, SBC)}


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
    cases: list[tuple[str, InteriorLayout, str | None]] = []

    cases.append(("valid MILP reference", base, None))

    # coverage gap — shrink the kitchen's east wall
    cases.append(("gap (coverage)",
                  InteriorLayout(FP, DOOR, repl(rs, "Kitchen", x_max=60.0)), "coverage"))

    # overlap — stretch Bath 1 east into Bedroom 1
    cases.append(("overlap",
                  InteriorLayout(FP, DOOR, repl(rs, "Bath 1", x_max=30.0)), "no_overlap"))

    # wrong count — relabel Bedroom 3 as a 2nd kitchen
    cases.append(("wrong room count",
                  InteriorLayout(FP, DOOR, repl(rs, "Bedroom 3", kind="kitchen")), "room_count"))

    # door not in living — push it into the kitchen span
    cases.append(("door not in living",
                  InteriorLayout(FP, (66.0, 20.0), rs), "door_in_living"))

    # bathroom too wide — 33 ft wide bath (passes min side, fails max side)
    cases.append(("bath max side",
                  InteriorLayout(FP, DOOR, repl(rs, "Bath 1", x_max=44.0)), "room_max_side"))

    # ensuite broken — detach Bath 2 from Bedroom 2 (slide it off to a corner)
    detached = repl(rs, "Bath 2", x_min=20.0, x_max=30.0, y_min=63.0, y_max=70.0)
    cases.append(("ensuite detached",
                  InteriorLayout(FP, DOOR, detached), "ensuite_attached"))

    # bathroom abuts kitchen — slide a bath flush onto the kitchen's north wall
    bad_bath = repl(rs, "Bath 2", x_min=48.0, x_max=56.0, y_min=59.0, y_max=67.0)
    cases.append(("bath adjacent to kitchen",
                  InteriorLayout(FP, DOOR, bad_bath), "bath_not_adj_kitchen"))

    ok = True
    for label, layout, expect in cases:
        rset = rules(layout)
        passed = (len(rset) == 0) if expect is None else (expect in rset)
        ok = ok and passed
        detail = "0 violations" if not rset else ", ".join(sorted(rset))
        want = "(clean)" if expect is None else f"expect '{expect}'"
        print(f"  [{'PASS' if passed else 'FAIL'}] {label:26s} {want:26s} -> {detail}")

    print("\nALL PASS" if ok else "\nSOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
