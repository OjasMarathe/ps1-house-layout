"""Smoke test for the interior verifier — no LLM/API calls.

Builds the Z3-synthesized reference layout (which must pass) and then mutates it
to trigger each rule, asserting the expected violation fires. Run:
    python smoketest_interior.py
"""

from constraints import SBC
from interior_verifier_z3 import (Room, InteriorLayout, check_interior)
from interior_synth_z3 import synthesize

FP = (5.0, 20.0, 70.0, 78.0)
DOOR = (40.0, 20.0)


def rules(layout) -> set[str]:
    return {v.rule for v in check_interior(layout, SBC)}


def replace(rooms, name, **kw):
    """Return a new room tuple with `name` replaced by a mutated copy."""
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
    ref = synthesize(FP, DOOR, SBC)
    base = ref.rooms
    cases: list[tuple[str, InteriorLayout, str | None]] = []

    # 1. Reference is clean.
    cases.append(("valid reference", ref, None))

    # 2. Gap — shrink the kitchen's east wall, leaving dead space.
    cases.append(("gap (under-tiled)",
                  InteriorLayout(FP, DOOR, replace(base, "Kitchen", x_max=68.0)),
                  "exact_tiling"))

    # 3. Overlap — stretch Bath 1 across Bath 2.
    cases.append(("overlap",
                  InteriorLayout(FP, DOOR, replace(base, "Bath 1", x_max=50.0)),
                  "no_overlap"))

    # 4. Wrong count — relabel a bedroom as a second kitchen.
    cases.append(("wrong room count",
                  InteriorLayout(FP, DOOR, replace(base, "Bedroom 3", kind="kitchen")),
                  "room_count"))

    # 5. Door not in the living room — push it east into the kitchen span.
    cases.append(("door not in living",
                  InteriorLayout(FP, (66.0, 20.0), base),
                  "door_in_living"))

    # 6. Sliver — make a bedroom too narrow.
    cases.append(("sliver bedroom (min side)",
                  InteriorLayout(FP, DOOR, replace(base, "Bedroom 1", x_max=12.0)),
                  "room_min_side"))

    # 7. Disconnected — two rooms touching only at a corner.
    disc = InteriorLayout((0.0, 0.0, 20.0, 20.0), (5.0, 0.0), (
        Room("Living", "living", 0, 0, 10, 10),
        Room("Kitchen", "kitchen", 10, 10, 20, 20),
    ))
    cases.append(("disconnected rooms", disc, "connected"))

    ok = True
    for label, layout, expect in cases:
        rs = rules(layout)
        if expect is None:
            passed = (len(rs) == 0)
        else:
            passed = (expect in rs)
        flag = "PASS" if passed else "FAIL"
        if not passed:
            ok = False
        detail = "0 violations" if not rs else ", ".join(sorted(rs))
        want = "(clean)" if expect is None else f"expect '{expect}'"
        print(f"  [{flag}] {label:28s} {want:22s} -> {detail}")

    print("\nALL PASS" if ok else "\nSOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
