# Window Agent & Roof Plan Agent — Explained

A plain-language, complete guide to both agents: what they do, why, how they
work, what we built, and how to explain it. Read top-to-bottom once and you'll be
able to present either agent confidently. Jargon is defined inline and in the
**Glossary** at the end.

---

## 0. The big picture (read this first)

Our project turns a homeowner's request into a **city-submittable house design**.
It's a pipeline of small "agents", each owning one job. Two of those are:

- **Window Agent** — decides/*checks* the **windows** (where they go, and whether
  they're legal: fire-escape, enough light, safety glass).
- **Roof Plan Agent** — designs the **roof** (shape, slope, drainage) and now adds
  **skylights** where rooms are dark.

Both are **deterministic tools** — no AI/LLM inside, no randomness. *Same input
always gives the same output.* That matters because this is going toward **legal
permit approval**, where "the computer said yes yesterday and no today" is
unacceptable.

**One-line each:**
- Window Agent → *"Are the windows legal, and where should they go for light/air?"*
- Roof Plan Agent → *"What roof covers this house, and where do skylights go to fix dark rooms?"*

---

# PART A — THE WINDOW AGENT

## A1. What it started as (before our work)

A teammate (Aadi) built a **daylight scorer**. Given a house layout, for every
room it:
1. finds the room's **exterior walls** (walls facing outside),
2. ranks them by **sun exposure** and **tree shade**,
3. suggests windows to hit a target **window-to-floor ratio** (how much glass vs
   floor space), and
4. gives the room a **daylight score from 0 to 100**.

It's smart and deterministic — but it only answers *"how nice is the light?"* It
does **not** check the **legal, safety rules** a window must obey (fire escape,
minimum light, safety glass). That was the gap.

## A2. The window concepts you need (so the rules make sense)

- **Daylight / WWR (window-to-floor ratio):** how much window area a room has,
  relative to its floor area. More glass → more daylight.
- **Egress window:** a window big enough and low enough that a person can **climb
  out in a fire**. Every bedroom legally needs one.
- **Sill height:** how high the **bottom** of the window is above the floor.
- **Safety glazing / tempered glass:** special glass that shatters into blunt
  pebbles instead of sharp shards. Required where someone could fall into a
  window (low windows, bathrooms, next to doors).
- **Operable window:** a window that **opens** (slider, casement). A **fixed**
  window (like a picture window) doesn't open — so it can't be a fire escape or
  provide ventilation.
- **IRC:** the **International Residential Code** — the actual rulebook cities use.
  We grounded every rule in a specific IRC section, so our checks are defensible.

## A3. The problem (what the mentor asked for)

The mentor's feedback, in plain terms:
1. **Follow the "LAC" guideline** (explained next).
2. Checking lighting *after* the design is generated **adds latency** — if it
   fails, you regenerate and check again, round after round.
3. **Shift-left:** give the lighting/window rules to the generator **as
   constraints up front**, so it builds it right the first time.
4. Decide: should this checking be **deterministic** (fixed math) or
   **non-deterministic** (AI/simulation)?
5. **Formalise the real window rules** (egress, tempered glass, sill height,
   per-room placement) and coordinate with the Constraint Engine + Floor Plan
   teams.

## A4. The two big ideas, explained simply

### LAC = Latency · Accuracy · Concurrency
"LAC" is a **systems trade-off triangle** — three things a pipeline should be
good at:
- **Latency** — be fast; don't get stuck in retry loops.
- **Accuracy** — be correct and repeatable.
- **Concurrency** — let agents run in parallel; don't block each other.

Everything we decided serves one of these three legs.

### Shift-left (the key idea)
Imagine two ways to get a legal window:
- **Check after (slow):** the generator makes windows → we check → it's illegal →
  it regenerates → we check again... Each loop is expensive (especially if an AI
  is regenerating). This is high **Latency**.
- **Constrain first (fast):** we hand the generator the rules *before* it starts,
  so it makes legal windows the first time. Almost no loops. This is "shift-left"
  — move the checking **earlier** (to the left in the timeline). Low **Latency**.

Analogy: instead of baking a cake, tasting it, and re-baking if it's wrong
(check-after), you write the recipe with the constraints baked in so it comes out
right (constrain-first).

### Why deterministic (the clever part)
Here's the punchline that ties it together: **you can only shift-left if the rule
is deterministic.** A rule can only be handed to a generator as a *constraint* if
it's a clear yes/no you can compute (a "decidable predicate"). A fuzzy,
random AI/simulation score can never be a constraint — it can only be a *score you
compute afterward.* So **deterministic verification is what makes shift-left
possible.** That's why we chose deterministic (it also gives **Accuracy** —
repeatable, provable).

## A5. What we built — the constraint layer

We split every window requirement into two buckets:

- **HARD (the legal gate):** deterministic, provable, given to the generator as
  constraints. *These we built.*
- **SOFT (the quality score):** Aadi's daylight score — kept as a **non-blocking**
  signal in the report (this gives **Concurrency**: it never stops the pipeline).

The HARD rules (each cites its IRC section, and the `(city)` numbers can be tuned
per jurisdiction):

| Rule | Plain meaning | IRC |
|---|---|---|
| `egress_window` | every bedroom needs one **operable** window ≥ 5.7 sq ft, ≥ 24 in tall, ≥ 20 in wide, sill ≤ 44 in | R310 |
| `natural_light` | each habitable room's glass ≥ **8%** of its floor area | R303.1 |
| `natural_ventilation` | openable window area ≥ **4%** of floor area | R303.1 |
| `safety_glazing` | windows that are low (sill < 18 in), in wet rooms, or next to a door **must be tempered** | R308.4 |

**Files (in the Z3 verifier tool):** `window_rules.py` (the numbers + IRC
citations), `window_verifier_z3.py` (the deterministic checks), and the callable
`verify_windows(...)` in `verifier_tool.py`.

## A6. How to run it

```python
from verifier_tool import verify_windows

rooms   = [{"id": "bed1", "type": "bedroom", "floor_area_sqft": 150}, ...]
windows = [{"room": "bed1", "type": "sliding", "width_ft": 3, "height_ft": 4,
            "sill_height_ft": 3.0, "operable_type": "sliding", "tempered": False}, ...]

res = verify_windows(windows, rooms, constraints=ruleset)   # ruleset = Constraint Engine JSON (optional)
# res["ok"]  -> True/False
# res["violations"] -> [{rule, measured, required, message}, ...]
```

It returns a pass/fail (`ok`) plus, for each failure, **what was measured, what
was required, and the IRC section** — so a generator can fix it, or a reviewer can
read it.

## A7. Demo results (what it actually did)

- **Compliant windows** → `ok=True`, 0 failures, ~6 ms.
- **Non-compliant** (a fixed tiny bedroom window, undersized living-room glass, a
  low untempered bathroom window) → `ok=False`, **6 violations**, each exact:
  - `egress_window` (bedroom, R310)
  - `natural_light` — 4 sq ft < 12 required (bedroom, R303)
  - `natural_ventilation` — 0 < 6 required (bedroom)
  - `natural_light` — 4 < 24 (living room)
  - `natural_ventilation` — 4 < 12 (living room)
  - `safety_glazing` — sill 12 in < 18 in (bathroom, R308)

## A8. Every feedback item → what we did

| Feedback | Our response |
|---|---|
| Follow LAC | Identified LAC = Latency·Accuracy·Concurrency; mapped all 3 decisions to it |
| Lighting checks add latency | Confirmed; the generate→verify→fail loop is the cost |
| Shift-left as constraints | Built `verify_windows` — hard rules given to the generator, not post-checks |
| Deterministic vs not | Chose **deterministic** (needed for shift-left; also accurate/repeatable) |
| Bedroom fire-escape windows | `egress_window` (IRC R310) — HARD |
| Tempered glass below height X | `safety_glazing` (IRC R308.4), city-tunable — HARD |
| Sill/header height | `sill_height_ft` field, enforced by egress + tempered rules — HARD |
| Enough light/air | `natural_light` ≥8%, `natural_ventilation` ≥4% (IRC R303) — HARD |
| Fire-egress ⇒ operable | egress requires an operable window type — HARD |
| Bathroom near shower / master bath / closet / kitchen-above-sink / bed placement | **SOFT** — need fixture positions (sink, bed, tub) from the Floor Plan agent; promote to HARD once available |
| Aesthetic windows by budget | **SOFT** — a Livability-score dimension, not code |
| Garage window; patio ⇒ sliding door | Optional / handled by Floor Plan (doors) |

---

# PART B — THE ROOF PLAN AGENT

## B1. What it is / where it sits

The Roof Plan Agent designs the **roof** as its own deliverable (separate from the
floor plan and side views). It sits in the "Output & Export" cluster: it takes the
**final footprint(s) + heights** from the Elevation/Multi-floor step, produces a
**roof drawing** tagged `"view_type":"roof"`, and hands it to the **DXF Generator**
and the PDF report.

## B2. The roof concepts you need

- **Footprint:** the outline of the house from above. The roof must match it
  **exactly** — no overhang errors, no gaps.
- **Pitch:** the roof's **steepness**, written like `5:12` = rises 5 inches for
  every 12 inches across. Steeper = bigger number.
- **Ridge:** the **top horizontal line** where two roof slopes meet (the peak).
- **Eave:** the **bottom edge** of a roof slope (where gutters go).
- **Hip:** a slanted ridge line running down a corner (on a hip roof).
- **Drainage:** the direction water runs **off** each roof surface.
- **Roof types:** **gable** (two slopes meeting at a ridge — the classic "house"
  shape), **hip** (four slopes), **shed** (one slope — common over a garage),
  **flat** (nearly flat, with a slight slope so water still drains).
- **Stepped roof:** when a house has parts at **different heights** (e.g. a garage
  lower than the main house), each part gets its own roof section at its own level.
- **Skylight / sunroof:** a window **in the roof** that brings daylight straight
  down into a room.

## B3. What it generates

For each building level it produces a **roof section** containing: the outline
(exactly the footprint), the ridge line, hip lines, each sloping **plane** with its
**pitch and drainage direction**, and the **eave & ridge heights**. It supports
gable/hip/shed/flat, and different roof types per level (e.g. gable house + shed
garage).

## B4. How it checks itself (before handing off)

Like the other agents, it **proves its own output is correct** using Z3 (a math
solver) before passing it on. The checks:

| Check | Meaning |
|---|---|
| `roof_matches_footprint` | the roof outline equals the footprint (no overhang/gap) |
| `stepped_roof_downward` | a lower section never pokes up into a higher one |
| `roof_eave_setback` | any roof overhang stays within the legal setback (fire clearance) |
| `pitch_specified` | every section actually has a drainage slope |
| `drainage_specified` | every roof surface names which way it drains |
| `skylight_within_roof` | every skylight sits inside the roof |

## B5. The skylight ↔ Window Agent link (the new part)

The mentor asked: *use the lighting info to decide where to put a sunroof.* So the
Roof Plan Agent now **reads the daylight scores from the Window Agent** and:
1. finds the **under-lit top-floor rooms** (daylight score below ~45 — Aadi's
   "poor" cutoff),
2. places a **skylight over each one**, on that room's **sunniest roof plane**
   (prefers south/east/west-facing, which get the most sun in our hemisphere).

This is the two agents cooperating: the Window Agent measures *where light is
weak*, and the Roof Plan Agent *fixes it from above* with a sunroof — all
deterministically (same scores → same skylights).

## B6. How to run it

```python
from roof_tool import roof_plan

payload = {
  "levels": [
    {"level": 1, "name": "main", "top_height_ft": 20,
     "footprint": [[x,y], ...],
     "rooms": [{"name": "family_room", "type": "family_room",
                "polygon": [[x,y],...], "daylight_score": 34}]}    # score from Window Agent
  ],
  "roof_spec": {"type": "gable", "pitch": "5:12"}
}
roof = roof_plan(payload, emit_dxf="out.dxf", emit_svg="out.svg")
# roof["roof_sections"][*]["skylights"], roof["verified"], roof["violations"]
```

Outputs a `"view_type":"roof"` JSON (for the DXF Generator) + a DXF and an SVG/PNG
drawing.

## B7. Demo results

A demo house — **gable** main roof (5:12 pitch, ridge 28.8 ft) + a **stepped shed**
garage (lower) — came out **VERIFIED ✓**, and because the top-floor `family_room`
scored a low **34** for daylight, the agent automatically placed a **skylight over
it on the sun-facing east plane** (the `bedroom` at 71 correctly got none). The
skylight shows up as an orange square in `output/roof_plan.png`.

---

# PART C — HOW THE TWO AGENTS CONNECT

```
Window Agent ── daylight scores ──▶ Roof Plan Agent ── roof + skylights ──▶ DXF / PDF
     │                                                          ▲
     └── hard window constraints ──▶ Z3 Verifier ◀── roof self-checks ──┘
```

- The **Window Agent** produces (a) hard window constraints (legal gate) and (b)
  daylight scores (soft signal).
- The **Roof Plan Agent** consumes the daylight scores to place skylights, and
  produces the roof geometry.
- Both are **provable** (Z3-checked) and feed the **DXF/PDF** permit outputs.

---

# PART D — HOW TO EXPLAIN IT (your talking points)

If someone asks *"what did you do?"*, say:

> "I worked on two agents. The **Window Agent** used to only *score* daylight; I
> turned the real **legal window rules** — fire-escape windows, minimum light and
> air, safety glass — into a **deterministic, provable checker** grounded in the
> building code. And crucially I **shift-left**ed them: instead of checking after
> the design and looping on failures (slow), the rules are given to the generator
> up front so it builds it right the first time. That's only possible *because*
> the checks are deterministic — a fuzzy AI score can't be a constraint. This maps
> onto the **LAC** guideline: shift-left = **Latency**, deterministic =
> **Accuracy**, the non-blocking daylight score = **Concurrency**.
>
> The **Roof Plan Agent** builds the roof — shape, pitch, drainage, and stepped
> roofs for multi-level houses — and **verifies its own geometry** with Z3. Then,
> per the mentor's ask, it now reads the **daylight scores from the Window Agent**
> and **places a skylight over any dark room**, on its sunniest roof plane. So the
> two agents cooperate: one finds where light is weak, the other fixes it from the
> roof."

---

# GLOSSARY

| Term | Meaning |
|---|---|
| **Deterministic** | same input always gives the same output; no randomness/AI |
| **Shift-left** | move checking earlier — give rules as constraints so it's built right first time |
| **LAC** | Latency · Accuracy · Concurrency — a systems trade-off triangle |
| **Constraint** | a rule the generator must satisfy while building |
| **Predicate** | a clear true/false condition you can compute |
| **Z3** | a mathematical solver that *proves* whether conditions hold |
| **IRC** | International Residential Code — the building rulebook |
| **Egress window** | a bedroom window big/low enough to escape a fire through |
| **Sill height** | height of the bottom of a window above the floor |
| **Tempered / safety glazing** | shatter-safe glass, required in hazardous spots |
| **Operable window** | a window that opens (vs a fixed/picture window) |
| **WWR** | window-to-floor ratio — glass area ÷ floor area |
| **Habitable room** | a room people live in (bedroom, living, kitchen…) |
| **Footprint** | the outline of the building seen from above |
| **Pitch** | roof steepness, e.g. `5:12` |
| **Ridge / eave** | top peak line / bottom edge of a roof slope |
| **Gable / hip / shed / flat** | the four roof shapes |
| **Stepped roof** | separate roof sections at different heights (multi-level) |
| **Skylight / sunroof** | a window in the roof that brings light down into a room |
| **Setback** | required clear distance from the property line |
