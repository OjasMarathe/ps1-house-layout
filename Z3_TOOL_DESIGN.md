# Z3 Verifier — Design & Usage

The deterministic constraint checker. A generator proposes a layout; this tool
**proves** it legal (SAT) or returns the exact violations (UNSAT). Same input →
same verdict, every time. One import, three functions.

```python
import verifier_tool as vz
vz.optimize_area(...)     # max buildable area
vz.verify_site(...)       # exterior shell  -> sat/unsat + per-rule results
vz.verify_interior(...)   # interior layout -> sat/unsat + violations
```

---

## Quick answers (the questions you asked)

| Question | Answer |
|---|---|
| **Is it modular?** | Yes. You can pass the **constraints directly** (the Constraint Engine's ruleset), not just a city name. You can also restrict it to a **subset of rules** with `rules=[...]`. |
| **Does it support all constraints from the ruleset?** | It enforces every rule it has a **check implemented** for (full lists below). The *values* are 100% configurable. **Unknown keys are ignored**, so the Constraint Engine can add new keys without breaking the tool. A brand-new *rule type* needs a one-time check added on our side. |
| **Send layout + the constraints used → it evaluates sat/unsat?** | Yes — exactly that. `verify_site(shell, constraints=...)` / `verify_interior(layout, constraints=...)`. |
| **Does it give the amount of violation? (esp. interior)** | Yes. Every result has `ok` (sat/unsat) + `n_failed` (count) + a per-violation **`measured` vs `required`** so you see *how far off* each rule is. Interior returns the full `violations` list. |
| **Why so many files in the zip?** | You only ever import **`verifier_tool.py`** — everything else is internals it uses. File guide at the bottom. |

---

## API

### `verify_site(house, city=None, *, constraints=None, rules=None, tolerance_ft=None)`
Check an exterior shell.
```python
house = {"corners": [[5,20],[75,20],[75,78],[5,78]], "door": [40,20]}   # feet, plot SW origin
```
Provide **either** `city="seattle"` (loads `citycodes/seattle.json`) **or**
`constraints={...}` (your ruleset, used directly).

**Returns**
```python
{
  "source": "Seattle",            # city / jurisdiction / "custom-constraints"
  "mode": "site/exterior",
  "ok": True,                     # SAT — every checked rule passes
  "n_checked": 13,
  "n_failed": 0,                  # how many constraints were violated
  "constraints": [               # EVERY checked rule, pass or fail
     {"rule": "front_setback_south", "pass": True,
      "measured": None, "required": None, "message": "satisfied"},
     {"rule": "max_lot_coverage", "pass": False,
      "measured": 4060.0, "required": 2247.0,
      "message": "Footprint 4060 sq ft is 63% of the lot; cap is 35% ..."},
     ...
  ],
  "unknown_rules": [],            # any rule names you asked for that we don't implement
  "max_buildable_area_sqft": 2247.0,
  "tolerance_ft": 1e-06,
  "solve_time_s": 0.009
}
```

### `verify_interior(layout, city=None, *, constraints=None, rules=None, mode="freeform", tolerance_ft=None)`
Check an interior layout.
```python
layout = {"footprint": [0,0,65,58], "door": [32,0],          # [x0,y0,x1,y1]
          "rooms": [["Bedroom 1","bedroom",0,0,20,18], ...]}  # [name,kind,x_min,y_min,x_max,y_max]
```
**Returns**
```python
{
  "source": "Seattle",
  "mode": "interior/freeform",
  "ok": False,                   # UNSAT
  "n_failed": 1,                 # number of violated rules
  "violations": [                # ONLY the failures, with the magnitude
     {"rule": "corridor_fraction", "measured": 360.0, "required": 226.0,
      "message": "Corridor is 16% of usable area; must stay <= 15%."}
  ],
  "unknown_rules": [],
  "tolerance_ft": 1e-06,
  "solve_time_s": 0.03
}
```
> `mode`: `"freeform"` (default — leftover open space allowed; the right mode for
> generator output) or `"strict"` (rooms must tile + the full ensuite/adjacency family).

### `optimize_area(city=None, *, constraints=None)`
Max buildable area for the plot (no layout input). Returns
`{source, max_buildable_area_sqft, optimal_corners, coverage_threshold_sqft, solve_time_s}`.

---

## Modularity — 3 ways to use it

**1. By city** (loads a bundled ruleset):
```python
vz.verify_site(house, "seattle")
```

**2. By constraints** — pass the Constraint Engine's ruleset directly (the
single-source-of-truth path). Shape = `CONSTRAINT_SCHEMA.md`:
```python
ruleset = {
  "jurisdiction": "Seattle Downtown NR", "tolerance_ft": 1e-6,
  "exterior": {"front_setback_ft":15, "rear_setback_ft":15, "side_setback_ft":5,
               "min_house_width_ft":20, "min_house_depth_ft":20, "door_corner_margin_ft":2,
               "max_lot_coverage_fraction":0.35, "min_area_fraction_of_max":0.90},
  "interior": {"corridor_max_fraction_of_usable":0.15, "coverage_tol_fraction":0.05}
}
vz.verify_site(house, constraints=ruleset)
vz.verify_interior(layout, constraints=ruleset)
```
Unknown keys in `exterior`/`interior` are **ignored** (forward-compatible).

**3. Subset of rules** — check only the constraints you care about (so the
Verifier Agent doesn't have to reason about all of them):
```python
vz.verify_site(house, "seattle", rules=["front_setback_south", "max_lot_coverage"])
vz.verify_interior(layout, "seattle", rules=["corridor_fraction", "living_gt_bedroom"])
```
`ok` then reflects only the requested rules; anything you ask for that we don't
implement comes back in `unknown_rules`.

---

## The constraints it currently checks

**Exterior (13):** `front_setback_south`, `rear_setback_north`, `side_setback_west`,
`side_setback_east`, `min_width_ew`, `min_depth_ns`, `tree_buffer`,
`door_on_south_wall`, `door_corner_margin`, `door_within_entry_segment`,
`corner_inside_plot`, `min_area_coverage`, `max_lot_coverage`.

**Interior (17):** `room_count`, `room_in_footprint`, `room_min_area`,
`room_min_side`, `room_max_side`, `no_overlap`, `coverage`, `corridor_fraction`,
`ensuite_attached`, `bath_smaller`, `bath_not_adj_kitchen`, `baths_not_adjacent`,
`living_near_south`, `living_gt_bedroom`, `door_in_living`, `kitchen_by_living`,
`connected`.

These names are the contract — use them in `rules=[...]`, and they're the `rule`
field in every violation.

---

## What's configurable vs. fixed (be precise with this)

| Thing | Status |
|---|---|
| All exterior **values** (setbacks, buffers, coverage caps, tolerance) | ✅ fully modular — pass any numbers |
| Interior **corridor cap** + **coverage tolerance** | ✅ modular — override via `constraints["interior"]` |
| Interior **per-room min areas / sides, adjacency rules** | ⚠️ currently fixed to IRC (in `rooms.py`); value-overrides are the next step |
| A **new rule type** the Constraint Engine invents | ❌ needs a one-time check added here — tell me the rule and I'll wire it |

So: *values* are modular today; *new rule types* are a quick collaboration.

---

## File guide (you only import one)

| File | Role |
|---|---|
| **`verifier_tool.py`** | **THE entry point — import this.** The 3 functions + a CLI. |
| `verifier_z3.py` | exterior Z3 checks (internal) |
| `optimizer_z3.py` | max-area solver (internal) |
| `interior_verifier_z3.py` | interior Z3 checks (internal) |
| `constraints.py` | exterior constraint schema (a dataclass) |
| `rooms.py` | interior room program (IRC values) |
| `codeloader.py` | loads `citycodes/*.json` / builds constraints (internal) |
| `plot.py` | the lot geometry (internal) |
| `citycodes/*.json` | example per-city rulesets |
| `smoketest_*.py` | self-tests (`6/6` + `ALL PASS`) |
| `CONSTRAINT_SCHEMA.md` | the JSON shape for `constraints=` |
| `Z3_TOOL_DESIGN.md` | this document |

---

## CLI (for quick manual checks)
```bash
python verifier_tool.py verify   --city seattle --layout house.json
python verifier_tool.py interior --city seattle --layout rooms.json --json
python verifier_tool.py optimize --city seattle
```

## Properties
Deterministic (Z3 proof, not a guess) · per-rule `measured`/`required` so you see
the magnitude · configurable float tolerance (no false fails) · ~10 ms/call ·
pure function, safe to call directly from the Verifier Agent.
