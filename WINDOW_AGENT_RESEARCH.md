# Window Agent — Design Decisions & Justification

**Context:** Aadi's Window Agent is a *deterministic daylight scorer/suggester*
(sun-weight curves + window-to-floor ratio + tree shading; no LLM, reproducible).
The mentor's feedback asks us to (1) follow "LAC" design guidelines, (2) **shift-left**
lighting + window rules into constraints to cut latency, (3) decide whether lighting
verification should be **deterministic**, and (4) formalise the hard window rules
(egress, safety glazing, sill/header, per-room placement) with the Constraint Engine
and Floor Plan teams. This memo records the decisions, the reasoning, and what was
built.

---

## 0. The LAC guideline — Latency · Accuracy · Concurrency
"LAC" is the mentor's **systems-design trilemma: Latency, Accuracy, Concurrency** — the
three properties a pipeline agent must balance. It is not a separate task; it *is* the
rationale for the three decisions below, one leg each:

| Leg | What it demands | Decision that serves it |
|---|---|---|
| **Latency** | don't stall the pipeline in retry loops | **Decision 2 — shift-left** the hard rules into constraints, so illegal windows aren't generated in the first place → far fewer generate→verify→fail rounds |
| **Accuracy** | verdicts must be correct and reproducible | **Decision 1 — deterministic** verification: a provable, same-input→same-verdict gate (a stochastic sim can't guarantee this) |
| **Concurrency** | agents run in parallel; nothing blocks | **Decision 2 (soft tier)** — the daylight *score* is **non-blocking**, so Livability runs concurrently and only a genuine hard-rule violation ever gates |

---

## Decision 1 — Lighting/compliance verification is **DETERMINISTIC**

**Options considered**
| | Approach | Reproducible | Provable | Latency |
|---|---|---|---|---|
| A | Deterministic analytic (WWR, sun-weight, shading, code predicates) — *what Aadi has* | ✅ | ✅ (Z3-encodable) | ✅ ms |
| B | Physically-based daylight sim (Radiance ray-trace, Monte-Carlo sDA/UDI) | ⚠️ (stochastic) | ❌ | ❌ seconds–min |
| C | LLM / ML judge of "is the lighting ok" | ❌ | ❌ | ❌ + cost |

**Decision:** **A** for the *compliance gate*. Keep **B** as an *optional, offline
"quality enrichment"* for the final report only. Never **C** on a gate.

**Justification**
1. **A permit system needs same-input → same-verdict.** A stochastic simulator or an
   LLM can pass a design one run and fail it the next — unacceptable for a legal gate.
2. **Shift-left *requires* determinism.** You can only hand a rule to a solver/generator
   as a *constraint* if it is a **decidable predicate**. A Monte-Carlo daylight score is
   not a predicate, so it can never be shift-lefted — it can only ever be a post-hoc
   score. This is the single most important reason the gate must be deterministic.
3. **Latency & cost.** No ray-tracing, no LLM round-trips. Our verifier runs in ~10 ms.

---

## Decision 2 — **Shift-left**: split HARD constraints from the SOFT score

**Decision:** Split every window requirement into two tiers:
- **HARD (compliance):** egress, natural light ≥ 8%, ventilation ≥ 4%, safety glazing,
  sill limits. These are **deterministic constraints given to the generator up front**
  (correct-by-construction) *and* proved by the verifier.
- **SOFT (quality):** daylight score, orientation bias, tree-shade avoidance,
  cross-ventilation comfort, aesthetic glazing by budget. This stays **Aadi's Window /
  Livability agent** — **non-blocking**, attached to the report, never a gate.

**Justification (the latency argument the mentor raised).** The cost is the
`generate → verify → fail → regenerate` loop — and with LLM generation each failed round
is a *full* regeneration. If the hard rules are only checked *after* generation, an
illegal window forces another expensive loop. Encoding them as **constraints the
generator must satisfy** means it rarely emits an illegal window, so the compliance loop
mostly disappears. The soft score, being non-blocking, *never* triggers a regeneration.
Net: the only thing that can loop is genuine hard-rule violation, and that is now rare
by construction. This is exactly "shift-left the lighting constraints to reduce latency."

---

## Decision 3 — The window rule set, formalised (IRC-grounded, city-parameterised)

Every hard rule cites its International Residential Code section, so it is auditable and
jurisdiction-tunable (the `(city)` values are overridable by the Constraint Engine).

| Feedback item | Tier | Rule (and IRC basis) |
|---|---|---|
| Bedrooms need fire-escape windows | **HARD** | `egress_window`: each sleeping room ≥1 operable window, net clear ≥ **5.7 sq ft**, ≥ **24 in** H, ≥ **20 in** W, sill ≤ **44 in** — **R310** |
| Enough light/air per room | **HARD** | `natural_light` glazing ≥ **8%** floor, `natural_ventilation` openable ≥ **4%** — **R303.1** |
| Tempered glass below height X | **HARD** | `safety_glazing`: sill < **18 in** (city X), wet rooms, or adjacent-to-door → must be tempered — **R308.4** |
| Sill/header height | **HARD** | `sill_height_ft` field; enforced by egress (≤44 in) + tempered (<18 in) |
| Fire-egress ⇒ operable (sliding/openable) | **HARD** | egress requires an **operable** window type (fixed/picture rejected) |
| Bathroom window near shower / 3×2 max; master bath around tub; closet small/high; kitchen above sink; bedroom not behind bed | **SOFT** | placement heuristics that need **fixture coordinates** (sink, bed, tub) from the **Floor Plan agent** — advisory until those are emitted |
| Aesthetic glazing scales with budget | **SOFT** | a Livability-score dimension, not code |
| Garage window; patio ⇒ sliding *door* | **OPT / other agent** | garage optional; patio openings are doors (Floor Plan) |

**Coordination points:** the `(city)` thresholds + a `windows` block belong in the
**Constraint Engine** ruleset (Harshit); the **SOFT placement** rules need **fixture
positions** from the **Floor Plan** (Prasad). Until Floor Plan emits fixtures, placement
stays advisory in the Livability score.

---

## What was built (plugs into the Z3 Verifier tool)

- **`window_rules.py`** — the IRC-cited, city-parameterisable window code (egress, light,
  vent, safety-glazing thresholds) + `params_from_ruleset()` (Constraint-Engine override).
- **`window_verifier_z3.py`** — `check_windows(windows, rooms, params)`: deterministic
  Z3 proofs of the hard rules.
- **`verify_windows(windows, rooms, constraints=…)`** in `verifier_tool.py` — the callable
  the Verifier Agent / generator uses; returns `{ok, n_failed, violations[…]}`.

Verified: a compliant window set passes; a bad one trips `egress_window`, `natural_light`,
`natural_ventilation`, `safety_glazing` with exact measured-vs-required numbers; a 48-in
sill trips egress. ~10 ms, deterministic.

**Input contract** (feet): window = `{room, type, width_ft, height_ft, sill_height_ft,
operable_type, tempered, adjacent_to_door, egress_clear_sqft?}`; room = `{id, type,
floor_area_sqft}`.

---

## Research framing (for a possible paper)

The prevailing approach to daylight/window handling in generative building design is
**generate-then-simulate** (LLM or diffusion model proposes; a physically-based simulator
scores). Our contribution is **constraints-first residential window compliance**: a
**deterministic, formally-verifiable constraint system** that serves as **both** a
generator input (correct-by-construction) *and* a verifier, with the code grounded in the
IRC and parameterised by jurisdiction. The novel claim is the *duality* — the same
predicate is used to constrain generation and to prove compliance — which is only possible
because the rules are deterministic (Decision 1). The soft, simulation-style daylight
score is retained but demoted to a non-blocking quality signal, cleanly separating
"is it legal" (provable) from "is it nice" (scored).

## Open items to confirm
1. **LAC** — confirm the mentor's intended meaning (assumed Light-Air-Circulation).
2. **City X** for tempered-glazing sill and egress sill (per-jurisdiction; currently IRC).
3. **Fixture coordinates** from Floor Plan → promotes the SOFT placement rules to HARD.
4. **Egress net-clear reduction** — a slider's openable area ≈ half its rough size; we
   accept an optional `egress_clear_sqft`, else use nominal area. Decide the default.

---

### Sources
- IRC R310 (emergency escape & rescue): https://codes.iccsafe.org/s/IRC2021P2/chapter-3-building-planning/IRC2021P2-Pt03-Ch03-SecR310.1 · https://up.codes/s/emergency-escape-and-rescue-opening-required
- IRC R303.1 (light & ventilation): https://codes.iccsafe.org/s/IRC2021P2/part-iii-building-planning-and-construction/IRC2021P2-Pt03-Ch03-SecR303.1
- IRC R308 (safety glazing): https://codes.iccsafe.org/s/IRC2021P2/chapter-3-building-planning/IRC2021P2-Pt03-Ch03-SecR308
- Daylighting background: https://www.wbdg.org/resources/daylighting · https://www.mdpi.com/2673-8945/5/4/125
