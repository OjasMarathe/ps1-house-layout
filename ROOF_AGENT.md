# Roof Plan Agent — design & I/O

**Cluster 4 — Output & Export. Owner: Ojas.**

Generates the roof plan as its own deliverable on top of the floor plan and
elevations. Deterministic geometry → **Z3 self-verification** → tagged JSON +
DXF/SVG artifacts (same propose→prove pattern the generators use with the Z3 tool).

## Where it sits (pipeline wiring)

```
Elevation / Multi-floor cluster ──[top-floor footprint(s) + elevation data]──▶  Agent Manager
                                                                                   │
                                                                                   ▼
                                                                          ROOF PLAN AGENT
                                                                                   │
                             ──[roof polygon set, "view_type":"roof"]──▶  DXF Generator  +  PDF report
```
- **Input from:** Elevation Agent / Multi-floor Generator (via Agent Manager) — the final settled floor heights + footprints.
- **Also consumes (for skylights):** per-room **daylight scores from the Window / Livability Agent (Aadi)** — used to place sunroofs over under-lit top-floor rooms.
- **Output to:** DXF Generator (Harshit/Devam) as a tagged coordinate set, and a distinct artifact in the PDF (Anirudh).

## Skylights / sunroofs (lighting integration)
The agent reads the **Window Agent's daylight scores** and drops a **skylight over each
under-lit top-floor room** (score below ~45, Aadi's "poor"), on that room's **sunniest
roof plane** (prefers S/E/W-facing). This is how "put a sunroof where lighting is weak"
is done deterministically.

- **Extra input:** give the top level `rooms: [{name, type, polygon, daylight_score}]`,
  or a separate `daylight: {rooms:[{id, daylight_score}]}` block — the tool merges them.
- **Extra output:** `roof_sections[].skylights: [{room, center, width_ft, length_ft,
  outline, on_plane, faces, reason}]` + top-level `n_skylights`.
- **Z3 rule:** `skylight_within_roof` (each skylight sits inside the roof outline).
- **Artifacts:** drawn on a dedicated **`ROOF_SKYLIGHT`** DXF layer + on the SVG/PNG.

## Input (JSON)
```json
{
  "session_id": "abc",
  "levels": [
    { "level": 1, "name": "main", "footprint": [[x,y],...], "top_height_ft": 20.0,
      "roof_spec": { "type":"gable", "pitch":"5:12", "overhang_ft":0.0 } }   // roof_spec optional, per level
  ],
  "roof_spec": { "type":"gable", "pitch":"5:12", "ridge_axis":"auto", "drain_side":"N", "overhang_ft":0.0 },  // global default
  "constraints": { "exterior": { "side_setback_ft":5, "front_setback_ft":20, ... } }   // optional, for eave-setback check
}
```
- One entry in `levels` per building level → one **stepped** roof section. (A single-floor payload can also just pass top-level `footprint` + `top_height_ft`.)
- `roof_spec.type`: `gable` | `hip` | `shed` | `flat`. A per-level `roof_spec` overrides the global one (e.g. gable house + shed garage).

## Output (JSON, `view_type:"roof"` → DXF Generator)
```json
{
  "session_id": "abc", "view_type": "roof", "generated_by": "roof_plan_agent",
  "n_sections": 2,
  "roof_sections": [
    {
      "level": 1, "name": "main", "type": "gable",
      "pitch": "5:12", "pitch_ratio": 0.41667, "slope_pct": 41.7, "slope_angle_deg": 22.6,
      "outline": [[x,y],...],                 // EXACTLY the top-floor footprint
      "overhang_ft": 0.0, "is_rectangular": true,
      "ridge": [[x1,y1],[x2,y2]], "hips": [ ... ],
      "eave_height_ft": 20.0, "ridge_height_ft": 28.75,
      "drainage": ["E","W"],
      "planes": [ { "id":"west", "polygon":[[x,y],...], "drains_to":"W", "slope_pct":41.7, "azimuth_deg":270 }, ... ]
    }
  ],
  "verified": true, "n_failed": 0, "violations": [],
  "artifacts": { "dxf": "output/roof_plan.dxf", "svg": "output/roof_plan.svg" }
}
```

## Acceptance checklist → how it's met
| Requirement | How |
|---|---|
| Roof footprint matches top-floor boundary exactly (no overhang error / gap) | `outline` is set to the footprint; Z3 rule **`roof_matches_footprint`** proves area + bbox equality (overhang 0) or full coverage (overhang > 0) |
| Handles multi-floor / uneven elevation (stepped roof over garage) | one section per `level` at its own `top_height_ft`; per-level roof types; Z3 rule **`stepped_roof_downward`** proves lower ridge ≤ upper eave |
| Distinct artifact in DXF/PDF, separate from floor plan & side views | dedicated `roof_plan.dxf` (layers `ROOF_OUTLINE/RIDGE/HIP/SLOPE/TEXT`) + `roof_plan.svg` |
| Respects fire-safety/setback for roof structures | Z3 rule **`roof_eave_setback_*`** — an overhang eave must stay within the setback envelope |
| Roof pitch + drainage direction specified (not just an outline) | every section has a `pitch`/`slope_pct`; every `plane` has `drains_to` + `azimuth_deg`; Z3 rules **`pitch_specified`** + **`drainage_specified`** enforce it |

## Verification rules (Z3, `roof_verifier_z3.py`)
`roof_matches_footprint`, `roof_no_gap`, `pitch_specified`, `drainage_specified`,
`roof_eave_setback_{west,east,south,north}`, `stepped_roof_downward`. The agent
returns `verified:false` + `violations[]` (with `measured`/`required`) if any fire.

## Run it
```bash
python roof_tool.py --demo --dxf --svg          # main gable + stepped garage shed
python roof_tool.py --input roof_in.json --dxf --svg --json
```

## Files
`roof_agent.py` (geometry) · `roof_verifier_z3.py` (Z3 self-check) · `roof_dxf.py`
(DXF artifact) · `roof_render.py` (SVG render) · `roof_tool.py` (agent entry + CLI).
