# Roof Plan Agent — Output Schema (v1)

**Producer:** `roof_plan_agent` (Ojas) · **Tag:** `view_type: "roof"`
**Contract:** one JSON object per request. All geometry is **plan-view (top-down)**.
A machine-readable sample is in **`roof_output.sample.json`** (this is real agent output, not a mock).

> Forward-compat rule: this schema is **additive-only**. Consumers must **ignore unknown
> fields** (new keys may appear); never hard-fail on an extra field.

---

## Units & conventions (read this first)
| Thing | Convention |
|---|---|
| Coordinates | `[x, y]` in **feet**, same plan grid / origin / orientation as the Floor-Plan & Site-Plan agents |
| Lengths / areas | feet / square feet |
| Vent areas | **square inches** (`*_sqin`) — that's how IRC vent math is expressed |
| `azimuth_deg` | compass of downslope: **N=0, E=90, S=180, W=270** |
| `slope_angle_deg` | angle from horizontal |
| `drainage` / `drains_to` | one or more of `"N" "S" "E" "W"` |
| `type` | `"gable" | "hip" | "shed" | "flat"` |

---

## Top-level object
| Field | Type | Meaning |
|---|---|---|
| `session_id` | string | echoed from the request |
| `view_type` | `"roof"` | **constant** — the Agent Manager routes on this |
| `generated_by` | `"roof_plan_agent"` | producer id |
| `n_sections` | int | number of roof sections (wings/levels) |
| `roof_sections` | `RoofSection[]` | the roof geometry — **the main payload** |
| `n_skylights` | int | total skylights across all sections |
| `verified` | bool | **Z3 self-verification** result (footprint match, pitch, drainage, eave setback, stepped-downward, skylight-in-roof) |
| `n_failed` | int | number of failed rules (0 when `verified`) |
| `violations` | `Violation[]` | empty when verified |
| `schedule` | `Schedule` | rolled-up quantities for the PDF report / title block |

## `RoofSection`
| Field | Type | Meaning |
|---|---|---|
| `level` | int | stack level (higher = taller mass); used for stepped roofs |
| `name` | string | wing name (`"main"`, `"garage"`, …) |
| `type` | enum | `gable / hip / shed / flat` |
| `pitch` | string | `"5:12"` |
| `pitch_ratio` | float | rise/run (0.41667) |
| `slope_pct` | float | pitch as % |
| `slope_angle_deg` | float | pitch as degrees |
| `outline` | `[[x,y]…]` | **structural roof footprint** (no overhang) |
| `eave_overhang_ft` | float | overhang distance (authoritative) |
| `overhang_ft` | float | legacy alias — **use `eave_overhang_ft`** |
| `eave_outline` | `[[x,y]…]` | outline grown by the overhang = **actual drip/eave edge** |
| `roof_area_sqft` | float | **sloped** area (footprint × slope factor) |
| `ventilation` | `Ventilation` | IRC R806.2 attic-vent sizing (see below) |
| `is_rectangular` | bool | fast flag for simple sections |
| `drainage` | `dir[]` | directions this section sheds water |
| `ridge` | `[[x,y],[x,y]]` | ridge line (peak). `[]`/degenerate for flat |
| `hips` | `[[[x,y],[x,y]]…]` | **hip lines** — populated for `hip`; `[]` for gable/shed |
| `planes` | `Plane[]` | each roof face (for DXF layers, solar, drainage) |
| `ridge_height_ft` | float | height of ridge above datum |
| `eave_height_ft` | float | height of eave (top-of-wall) above datum |
| `skylights` | `Skylight[] | null` | skylights on this section (from daylight scores) |

## `Plane`
| Field | Type | Meaning |
|---|---|---|
| `id` | string | `"west"`, `"north"`, … |
| `polygon` | `[[x,y]…]` | the face outline in plan |
| `drains_to` | dir | downslope direction |
| `slope_pct` | float | face slope |
| `azimuth_deg` | float | compass of downslope (for solar/skylight placement) |

## `Skylight`
`{ room, type:"skylight", center:[x,y], width_ft, length_ft, outline:[[x,y]…], on_plane, faces, reason }`
*(placed over low-daylight rooms; `reason` cites the daylight score from the Window/Livability Agent.)*

## `Ventilation` (IRC R806.2)
`{ code:"IRC R806.2", rule, roof_area_sqft, nfa_required_sqin, eave_required_sqin,
   upper_required_sqin, roof_jacks_7x7:int, eave_birdblock_lf, nfa_provided_sqin, ok:bool }`

## `Violation`
`{ rule, measured, required, message }`  — only present when `verified:false`.

## `Schedule`
`{ roof_types:[…], total_roof_area_sqft, ventilation:{ total_roof_jacks_7x7,
   total_eave_birdblock_lf, all_sections_ok }, skylights:[{room,size_ft,on_plane}], attic_access }`

## `elevation_profiles` — for the Side-View / Elevation Agent
The roof's **side-view silhouette pre-computed** for all four elevations, so the
Elevation Agent draws a polyline instead of doing its own 3D projection (guarantees
her side view matches this roof).
```
elevation_profiles: {
  note, units:"feet",
  views: {
    south | north | east | west : {
      horizontal_axis: "x"|"y",     // which plan coord is left-right in this view
      mirror: bool,                 // flip u for a conventional outside-looking-in view
      sections: [ {
        name, type, eave_height_ft, ridge_height_ft, overhang_ft,
        roof_silhouette: [[u, z]…], // DRAW THIS: u = horizontal plan coord, z = height (ft)
        eave_line:       [[u, z]…]  // top-of-wall; walls run from z=0 up to here
      } ]
    }
  }
}
```
Gable **end** → triangle; gable **side** → level ridge line; **hip** side → trapezoid;
**shed** → sloped line; **flat** → level line.

---

## Who consumes what
| Consumer | Fields to read |
|---|---|
| **DXF Generator** (Harshit/Devam) | `roof_sections[].outline`, `eave_outline`, `ridge`, `hips`, `planes[].polygon`, `skylights[].outline` → one layer each |
| **PDF report** | `schedule`, `verified`/`violations`, plus the SVG/PNG artifact |
| **Agent Manager** | route on `view_type:"roof"`; gate on `verified` |
| **Side-View / Elevation** (Dhwani) | `elevation_profiles.views[<dir>].sections[].roof_silhouette` + `eave_line` — draw directly, no projection needed |
| **Structural / MEP** | `planes[].drains_to`, `ridge_height_ft`, `eave_height_ft`, `roof_area_sqft` |
| **Solar / Window** | `planes[].azimuth_deg` + `slope_pct` |

## What I need as INPUT (for upstream agents)
`{ levels:[ { level, name, top_height_ft, footprint:[[x,y]…], rooms?:[…] } ],
   roof_spec:{ type, pitch, overhang_ft }, daylight?:{ rooms:[{id, daylight_score}] },
   constraints?:{…}, session_id }`
→ Floor-Plan/Multi-floor sends `levels[].footprint`; Window Agent (Aadi) sends `daylight`;
Constraint Engine sends `constraints`. Unknown keys are ignored.

**Version:** roof-schema v1 · additive-only · contact: Ojas (Roof Plan Agent).
