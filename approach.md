# PS1 — Engineering Drawing Verification

**Approach by:** Ojas | **A1 / A2:** Gemini 2.5 Flash + Kimi K2 (via Groq)
**Date:** 2026-05-30 | Checkpoint 9 am IST, final 3 pm IST 2026-05-31

---

## 1. Problem in one line

Given an L-shaped plot with a protected tree, build a two-agent system that
designs a house outline (outer periphery + door) respecting Seattle Building
Code (SBC) setbacks, tree protection, and fire-egress rules, and emits a
verified `.dxf` engineering drawing.

## 2. Design principle: **Z3 is the judge, the LLM is the explainer**

The most common failure mode of "verifier" LLMs is they narrate verification
instead of doing it — agreeable, untraceable, non-reproducible. We avoid that:

```
  ┌──────────────┐   code      ┌──────────────┐   geometry    ┌──────────────┐
  │  A1: Gemini  │ ──────────► │  Parser      │ ─────────────►│  Z3 verifier │
  │  (generator) │             │  (regex)     │               │  (judge)     │
  └──────────────┘             └──────────────┘               └──────┬───────┘
        ▲                                                            │
        │                                                            │ violations
        │  natural-language feedback         ┌──────────────────┐    │
        └──────────────────────────────────  │   A2: Kimi K2    │ ◄──┘
                                             │   (explainer)    │
                                             └──────────────────┘
```

- **A1 (Gemini)** generates `ezdxf` Python that draws the house. Output starts
  with two structured comment lines containing the chosen corners and door —
  static metadata, *not* `print()` output.
- **Geometry parser** regex-extracts those numbers without executing untrusted
  LLM code.
- **Z3** is the only thing whose `sat`/`unsat` decides whether the design
  passes. Every SBC rule is a Z3 expression with measured-vs-required values.
- **A2 (Kimi K2 on Groq)** takes Z3's violation list and rewrites it as
  actionable feedback ("shift the south wall north by 3 ft"), which goes back
  to A1 for the next iteration.

The LLMs disagree → the Z3 model is rebuilt each iteration → loop terminates
when Z3 returns the empty violation set.

## 3. Plot geometry (sketch v2, closes exactly)

```
Origin: SW of entry tab. +x East, +y North. Units: feet.
Clockwise polygon vertices:

  (0,84) ─ 75 ─ (75,84) ─┐
                          │ 4  (step up)
                  (75,88) ─ 5 ─ (80,88)         ← tree notch (75..80, 84..88)
                                        │
                                        │ 80   (right edge total)
                                        │
                                 (80,8) ─ 5 ─ (75,8)
                                                 │ 8
                                          (75,0) ─ 40 ─ (35,0)   ← entry tab
                                                 │ 8
                                          (35,8) ─ 35 ─ (0,8)
  (0,84) ──── 76 (left edge total) ──── (0,8)
```

Tree protection zone: center (77.5, 86), trunk radius 1 ft, SBC buffer 3 ft.
Entry segment: x ∈ [35, 75] at y = 0 (40 ft, main door + driveway).

## 4. SBC constraint set encoded

| # | Rule | Z3 expression | Source |
|---|---|---|---|
| 1 | Front (S) setback ≥ 20 ft | `y_min - 0 >= 20` | SDCI Tip 320 |
| 2 | Rear (N) setback ≥ 10 ft | `88 - y_max >= 10` | SDCI Tip 320 |
| 3 | Side (E, W) setbacks ≥ 5 ft each | `x_min >= 5 ∧ 80 - x_max >= 5` | SDCI Tip 320 |
| 4 | Min footprint ≥ 20×20 ft | `x_max - x_min >= 20 ∧ y_max - y_min >= 20` | derived |
| 5 | All four corners inside L-shape polygon | ray-cast point-in-polygon (Python) | sketch |
| 6 | Distance to tree ≥ trunk + 3 ft buffer | `(dx² + dy²) >= 16` (quadratic, Z3-friendly) | SMC 25.11.090 |
| 7 | Door on S wall, in entry segment, ≥ 2 ft from corners | `door_y == y_min ∧ 35 ≤ door_x ≤ 75 ∧ x_min+2 ≤ door_x ≤ x_max−2` | IBC 2021 §1006 |
| 8 | Maximize footprint area | objective passed to A1 in the prompt | brief |

Z3 evaluates 1–4, 6, 7 algebraically; 5 is pure Python (point-in-polygon adds
no value when corners are concrete, but the principle is the same).

## 5. Why this design

| Choice | Alternative considered | Why we chose it |
|---|---|---|
| Z3 as final judge | LLM-as-verifier (A2 alone) | Reproducible. Same house + same rules → same verdict, always. |
| Magic comments at top of file | Execute A1's code to extract geometry | Doesn't run untrusted LLM output. Parser is 20 lines of regex. |
| A2 = LLM-as-explainer | A2 = LLM verifier | LLMs are good at writing actionable prose ("move the south wall north 3 ft"); they're bad at deciding when a geometry is correct. Play to strengths. |
| Disable Gemini thinking mode | Let 2.5-flash think by default | Code generation, not reasoning — thinking just adds latency. |
| Retry with exponential backoff | Fail on first 503 | Gemini 2.5 has demand spikes; 4 retries at 2/4/8/16 s cleared every one we hit. |

## 6. State of the implementation

```
ps1-house-layout/
├── plot.py             # L-shape polygon (closes exactly per v2 sketch)
├── constraints.py      # SBC rule constants with citations
├── verifier_z3.py      # Z3 checker — 5/5 smoke tests passing
├── geometry_parser.py  # Regex extractor
├── agent1_gemini.py    # Gemini call (thinking off, retry on 503/429)
├── agent2_groq.py      # Kimi K2 call (with offline fallback)
├── loop.py             # Orchestrator
├── smoketest_verifier.py
└── output/             # per-iteration .py + .dxf
```

- Z3 verifier: **5/5 smoke tests green** (good house, near-tree, wrong door
  wall, too-small, door outside entry segment).
- Loop runs end-to-end with `python loop.py`. Iteration 1 produced parseable
  geometry after the prompt was rewritten with concrete numeric example.
- Average per-iteration latency ~5–8 s on Gemini 2.5 Flash + Kimi K2 / Groq.

## 7. What's left before the 3 pm demo

1. **Two end-to-end converging runs** captured with intermediate `.dxf` files
   for the slide deck.
2. **Footprint area in violation feedback** — A2 should mention the achieved
   area so successive iterations push it up rather than just satisfying rules.
3. **Optional stretch:** swap the concrete-geometry check for a Z3 *synthesis*
   pass — declare corners as `Real` variables, add all constraints, solve for
   maximum area. Compares the LLM's design to the SMT-optimal one.

## 8. Prompt-engineering note (Anupam's tip applied)

A1's iteration-N prompt explicitly rebuilds state rather than letting the
model carry over its own (often wrong) assumptions:

> Iteration N. Your previous attempt violated SBC constraints. **Z3 (not
> you) reports these violations.** Fix every listed violation and re-emit
> HOUSE_CORNERS and DOOR. The previous corners and door are stale; do not
> reuse them as-is.

This kills self-anchoring — the model treats each iteration as a clean
problem with new constraints rather than incrementally patching its old
answer.
