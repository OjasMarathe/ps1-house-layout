/**
 * Problem 2 presentation — built from Problem2_Documentation_Ours.docx
 * MILP / cutting-plane interior + 25+4 Z3 constraints. Midnight Executive palette.
 * Output: Problem2_presentation.pptx
 */
const path = require("path");
const pptxgen = require("pptxgenjs");

const NAVY = "1E2761", ICE = "CADCFC", WHITE = "FFFFFF", RED = "B85042",
      GREEN = "2C5F2D", ORANGE = "F96167", MUTED = "64748B", DARK = "0F172A",
      TEAL = "0E7490";
const SLIDE_W = 13.333, SLIDE_H = 7.5;
const PROJ = "/Users/ojas/ps1-house-layout";
const IMG = (n) => path.join(PROJ, "output/slides", n);

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Ojas Marathe";
pres.title = "Problem 2 — MILP-Verified CAD Floor Plans";

let pageCount = 0;
const footers = [];
function mkSlide() { const s = pres.addSlide(); pageCount++; s.__p = pageCount; return s; }
function addFooter(s) { footers.push(s); }
function stamp() {
  for (const s of footers) {
    s.addText(`${s.__p} / ${pageCount}`, { x: SLIDE_W - 1.2, y: SLIDE_H - 0.42, w: 0.9, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri", align: "right" });
    s.addText("PS1 · Problem 2 · Ojas", { x: 0.5, y: SLIDE_H - 0.42, w: 6, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri" });
  }
}
function titleBlock(s, t, sub) {
  s.addText(t, { x: 0.6, y: 0.38, w: 12.1, h: 0.8, fontSize: 30, bold: true,
    color: NAVY, fontFace: "Cambria", margin: 0 });
  if (sub) s.addText(sub, { x: 0.6, y: 1.12, w: 12.1, h: 0.5, fontSize: 15,
    color: MUTED, italic: true, fontFace: "Calibri", margin: 0 });
}
function statCard(s, x, y, w, h, val, lab, accent = NAVY) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: WHITE }, line: { color: ICE, width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h, fill: { color: accent }, line: { color: accent, width: 0 } });
  s.addText(val, { x: x + 0.22, y: y + 0.14, w: w - 0.36, h: h * 0.56, fontSize: 26, bold: true,
    color: accent, fontFace: "Cambria", valign: "middle", margin: 0 });
  s.addText(lab, { x: x + 0.22, y: y + h * 0.56, w: w - 0.36, h: h * 0.4, fontSize: 10.5,
    color: MUTED, fontFace: "Calibri", valign: "top", margin: 0 });
}

// ============================================================ S1 Title
{
  const s = mkSlide();
  s.background = { color: NAVY };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.35, h: SLIDE_H, fill: { color: ICE }, line: { color: ICE, width: 0 } });
  s.addText("PROBLEM 2", { x: 1.0, y: 1.3, w: 11, h: 0.6, fontSize: 22, color: ICE,
    fontFace: "Cambria", charSpacing: 12, margin: 0 });
  s.addText("MILP-Verified CAD Floor Plans", { x: 1.0, y: 2.05, w: 11.5, h: 1.3, fontSize: 50,
    bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
  s.addText("Generate-and-guarantee interiors: CBC cutting planes propose, Z3 proves",
    { x: 1.0, y: 3.55, w: 11.5, h: 0.7, fontSize: 19, italic: true, color: ICE, fontFace: "Calibri", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 1.0, y: 5.5, w: 4, h: 0.04, fill: { color: ICE }, line: { color: ICE, width: 0 } });
  s.addText("Ojas Marathe  ·  7 June 2026", { x: 1.0, y: 5.62, w: 11, h: 0.5, fontSize: 14, color: ICE, fontFace: "Calibri", margin: 0 });
  s.addText("Generator: PuLP + CBC  ·  Judge: Z3 SMT  ·  LLMs: Gemini 2.5 Flash + Llama 3.3 70B (Groq)",
    { x: 1.0, y: 6.05, w: 11.5, h: 0.5, fontSize: 13, color: WHITE, fontFace: "Consolas", margin: 0 });
}

// ============================================================ S2 The problem
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The problem", "Extend the verified exterior to a complete, code-checked interior");
  s.addText("WHAT THE BRIEF ASKS", { x: 0.6, y: 1.9, w: 6, h: 0.35, fontSize: 12, bold: true,
    color: NAVY, charSpacing: 4, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "Generate a full residential floor plan:", options: { color: DARK, breakLine: true } },
    { text: "3 bedrooms · 2 bathrooms · 1 kitchen · 1 living · 1 corridor", options: { bold: true, color: NAVY, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Formally verify it against IRC R304/R305 room-size rules and architectural spatial rules (ensuite, sanitation, circulation).", options: { color: DARK } },
  ], { x: 0.6, y: 2.3, w: 6.0, h: 2.0, fontSize: 14, fontFace: "Calibri", margin: 0 });

  // key shift callout
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.5, w: 6.0, h: 2.2, fill: { color: "F0FDFA" },
    line: { color: TEAL, width: 1.5 }, rectRadius: 0.1 });
  s.addText("THE KEY SHIFT", { x: 0.85, y: 4.65, w: 5.5, h: 0.35, fontSize: 12, bold: true, color: TEAL, charSpacing: 4, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "Don't let the LLM guess and then repair (verify-and-fix). ", options: { color: DARK } },
    { text: "Have a MILP solver generate a layout that is guaranteed correct by construction (generate-and-guarantee). ", options: { color: NAVY, bold: true } },
    { text: "Z3 stays the independent judge.", options: { color: DARK, italic: true } },
  ], { x: 0.85, y: 5.05, w: 5.5, h: 1.5, fontSize: 13.5, fontFace: "Calibri", valign: "top", margin: 0 });

  s.addImage({ path: IMG("milp_result.png"), x: 7.15, y: 1.85, w: 5.6, h: 5.0, sizing: { type: "contain", w: 5.6, h: 5.0 } });
  addFooter(s);
}

// ============================================================ S3 System overview
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "System overview — two automated phases", "A generator proposes geometry · Z3 is the deterministic judge · an LLM explains failures");
  const boxY = 2.05, boxH = 3.3;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: boxY, w: 5.7, h: boxH, fill: { color: "F8FAFC" }, line: { color: NAVY, width: 1.5 }, rectRadius: 0.12 });
  s.addText("PHASE 1 — EXTERIOR", { x: 0.85, y: boxY + 0.15, w: 5.2, h: 0.4, fontSize: 13, bold: true, color: NAVY, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "Z3 Optimize → provable max-area target", options: { bullet: true, breakLine: true } },
    { text: "Gemini draws the outline; parser extracts coords", options: { bullet: true, breakLine: true } },
    { text: "Z3 verifies 9 SBC rules", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "Llama explains failures → loop", options: { bullet: true } },
  ], { x: 0.95, y: boxY + 0.6, w: 5.1, h: 1.9, fontSize: 13, color: DARK, fontFace: "Calibri", margin: 0 });
  s.addText("→  verified footprint + door", { x: 0.85, y: boxY + 2.7, w: 5.4, h: 0.5, fontSize: 13, italic: true, bold: true, color: GREEN, fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.LINE, { x: 6.35, y: boxY + boxH / 2, w: 0.6, h: 0, line: { color: NAVY, width: 2.5, endArrowType: "triangle" } });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.05, y: boxY, w: 5.7, h: boxH, fill: { color: "F0FDFA" }, line: { color: TEAL, width: 1.5 }, rectRadius: 0.12 });
  s.addText("PHASE 2 — INTERIOR (MILP)", { x: 7.3, y: boxY + 0.15, w: 5.2, h: 0.4, fontSize: 13, bold: true, color: TEAL, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "PuLP + CBC solve the 8-room layout (cutting planes)", options: { bullet: true, breakLine: true } },
    { text: "Guaranteed valid by construction", options: { bullet: true, breakLine: true, bold: true, color: TEAL } },
    { text: "Z3 verifies 25 + 4 interior rules", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "LLM verify-and-fix optional (MILP = fallback)", options: { bullet: true } },
  ], { x: 7.4, y: boxY + 0.6, w: 5.1, h: 1.9, fontSize: 13, color: DARK, fontFace: "Calibri", margin: 0 });
  s.addText("→  complete floor plan + layered .dxf", { x: 7.3, y: boxY + 2.7, w: 5.4, h: 0.5, fontSize: 13, italic: true, bold: true, color: GREEN, fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.65, w: 12.2, h: 1.15, fill: { color: ICE }, line: { color: NAVY, width: 1 }, rectRadius: 0.1 });
  s.addText([
    { text: "Same neuro-symbolic principle both phases: ", options: { color: DARK } },
    { text: "a generator proposes · Z3 proves · an LLM explains.", options: { color: NAVY, bold: true } },
  ], { x: 0.9, y: 5.75, w: 11.6, h: 0.95, fontSize: 15, fontFace: "Calibri", valign: "middle", margin: 0 });
  addFooter(s);
}

// ============================================================ S4 Phase 1 exterior
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Phase 1 — exterior in numbers", "Z3 Optimize turns 'maximize area' into a hard, verifiable constraint");
  statCard(s, 0.6, 2.0, 6.0, 1.5, "6,420", "PLOT AREA (sq ft, L-shaped)", NAVY);
  statCard(s, 6.85, 2.0, 6.0, 1.5, "4,060", "Z3-PROVABLE MAX HOUSE (70 × 58 ft)", NAVY);
  statCard(s, 0.6, 3.7, 6.0, 1.5, "3,654", "CONVERGED FOOTPRINT — 90% of max", GREEN);
  statCard(s, 6.85, 3.7, 6.0, 1.5, "2", "ITERATIONS TO SAT", GREEN);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.5, w: 12.2, h: 1.2, fill: { color: "F8FAFC" }, line: { color: ICE, width: 1 }, rectRadius: 0.1 });
  s.addText([
    { text: "Z3 declares the 4 corners as symbolic reals, adds the setbacks, and maximizes the footprint. ", options: { color: DARK } },
    { text: "The verifier then demands ≥ 90% of that max — so the generator must push to the legal limit.", options: { color: NAVY, bold: true } },
  ], { x: 0.9, y: 5.6, w: 11.6, h: 1.0, fontSize: 14, fontFace: "Calibri", valign: "middle", margin: 0 });
  addFooter(s);
}

// ============================================================ S5 generate vs verify
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The big idea: generate-and-guarantee", "A cutting-plane MILP places the rooms; the LLM no longer has to get geometry right");
  // verify-and-fix
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.95, w: 5.9, h: 4.7, fill: { color: "FEF2F2" }, line: { color: ORANGE, width: 1.5 }, rectRadius: 0.1 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.95, w: 0.1, h: 4.7, fill: { color: ORANGE }, line: { color: ORANGE, width: 0 } });
  s.addText("VERIFY-AND-FIX (baseline)", { x: 0.95, y: 2.15, w: 5.4, h: 0.4, fontSize: 12, bold: true, color: ORANGE, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "LLM guesses a layout", options: { bullet: true, breakLine: true } },
    { text: "Z3 checks, sends back failures", options: { bullet: true, breakLine: true } },
    { text: "LLM tries again … (multiple rounds)", options: { bullet: true, breakLine: true } },
    { text: "output is non-deterministic", options: { bullet: true } },
  ], { x: 0.95, y: 2.6, w: 5.4, h: 3.8, fontSize: 14, color: DARK, fontFace: "Calibri", valign: "top", margin: 0 });

  // generate-and-guarantee
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 1.95, w: 5.9, h: 4.7, fill: { color: "F0FDFA" }, line: { color: TEAL, width: 1.5 }, rectRadius: 0.1 });
  s.addShape(pres.shapes.RECTANGLE, { x: 6.85, y: 1.95, w: 0.1, h: 4.7, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addText("GENERATE-AND-GUARANTEE (ours)", { x: 7.2, y: 2.15, w: 5.4, h: 0.4, fontSize: 12, bold: true, color: TEAL, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "CBC solves the layout as a MILP", options: { bullet: true, breakLine: true } },
    { text: "Cutting planes remove infeasible layouts until only valid ones remain", options: { bullet: true, breakLine: true } },
    { text: "valid on the first solve — no LLM loop", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "solver output is reproducible", options: { bullet: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Z3 independently confirms the result.", options: { italic: true, color: NAVY } },
  ], { x: 7.2, y: 2.6, w: 5.4, h: 3.8, fontSize: 14, color: DARK, fontFace: "Calibri", valign: "top", margin: 0 });
  addFooter(s);
}

// ============================================================ S6 band structure
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The 3-band structure makes the rules structural", "Encode the spatial rules in the topology so the optimum is always code-valid");
  // schematic
  const bx = 7.7, bw = 5.0;
  const bedY = 1.95, bedH = 1.7;
  const cols = [["Bath 1", "E3ECF7", "1D4ED8"], ["Bed 1", "E5F0E0", "2C5F2D"], ["Bed 3", "E5F0E0", "2C5F2D"], ["Bed 2", "E5F0E0", "2C5F2D"], ["Bath 2", "E3ECF7", "1D4ED8"]];
  const cw = bw / 5;
  cols.forEach((c, i) => {
    s.addShape(pres.shapes.RECTANGLE, { x: bx + i * cw, y: bedY, w: cw, h: bedH, fill: { color: c[1] }, line: { color: c[2], width: 1.3 } });
    s.addText(c[0], { x: bx + i * cw, y: bedY + bedH / 2 - 0.18, w: cw, h: 0.36, fontSize: 8.5, bold: true, color: c[2], align: "center", fontFace: "Calibri", margin: 0 });
  });
  s.addText("PRIVATE band (15 ft)", { x: bx, y: bedY - 0.32, w: bw, h: 0.3, fontSize: 9, color: MUTED, align: "center", italic: true, margin: 0 });
  const corY = bedY + bedH;
  s.addShape(pres.shapes.RECTANGLE, { x: bx, y: corY, w: bw, h: 0.7, fill: { color: "E5E7EB" }, line: { color: MUTED, width: 1.0 } });
  s.addText("Corridor (4 ft)", { x: bx, y: corY + 0.2, w: bw, h: 0.3, fontSize: 9, italic: true, color: "475569", align: "center", margin: 0 });
  const pubY = corY + 0.7, pubH = 1.7;
  s.addShape(pres.shapes.RECTANGLE, { x: bx, y: pubY, w: bw * 0.6, h: pubH, fill: { color: "DCEEF7" }, line: { color: "065A82", width: 1.3 } });
  s.addText("Living", { x: bx, y: pubY + pubH / 2 - 0.18, w: bw * 0.6, h: 0.36, fontSize: 9.5, bold: true, color: "065A82", align: "center", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: bx + bw * 0.6, y: pubY, w: bw * 0.4, h: pubH, fill: { color: "FBE3D6" }, line: { color: "C2410C", width: 1.3 } });
  s.addText("Kitchen", { x: bx + bw * 0.6, y: pubY + pubH / 2 - 0.18, w: bw * 0.4, h: 0.36, fontSize: 9, bold: true, color: "C2410C", align: "center", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: bx + bw * 0.27, y: pubY + pubH - 0.06, w: 0.5, h: 0.12, fill: { color: "065A82" }, line: { color: "065A82", width: 0 } });
  s.addText("door → living", { x: bx, y: pubY + pubH + 0.04, w: bw, h: 0.28, fontSize: 8.5, italic: true, color: "065A82", align: "center", margin: 0 });

  s.addText([
    { text: "Corridor between public & private  →  ", options: { color: DARK } },
    { text: "no bath can ever touch the kitchen (sanitation)", options: { color: NAVY, bold: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Each bath flanks only its own bedroom  →  ", options: { color: DARK } },
    { text: "ensuite by construction", options: { color: NAVY, bold: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Bedroom 3 sits between the two pairs  →  ", options: { color: DARK } },
    { text: "the two baths are never adjacent", options: { color: NAVY, bold: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Fixed band heights keep every area linear  →  ", options: { color: DARK } },
    { text: "CBC stays in the fast linear fragment; ~100% tiling", options: { color: NAVY, bold: true } },
  ], { x: 0.6, y: 2.0, w: 6.7, h: 4.6, fontSize: 14, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S7 MILP model
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The MILP model (PuLP + CBC)", "Big-M disjunctive non-overlap → a true branch-and-cut MILP");
  const rows = [
    ["Variables", "Room widths / band cut positions (continuous) · per-pair non-overlap selectors (binary)"],
    ["Non-overlap", "Big-M disjunction per pair: at least one of {i left / right / below / above j}"],
    ["Containment + tiling", "Every room inside the footprint; bands span full width & height → ~100% coverage"],
    ["Door / egress", "Living spans the door, inset ≥ 2 ft, on the south wall"],
    ["Ensuite / sanitation", "Band ordering: Bath_i flanks only Bed_i; corridor isolates baths from the kitchen"],
    ["Objective", "Maximise the smallest bedroom width (balanced bedrooms); keep the kitchen generous"],
  ];
  const data = [[
    { text: "Component", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
    { text: "Formulation", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ...rows.map(r => [r[0], r[1]])];
  s.addTable(data, { x: 0.6, y: 1.95, w: 12.2, h: 3.6, fontSize: 13, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE }, rowH: 0.5, colW: [3.0, 9.2], valign: "middle" });
  s.addText([
    { text: "CBC runs branch-and-cut, adding Gomory / clique / cover cutting planes to tighten the relaxation. ", options: { color: DARK } },
    { text: "That is the cutting-plane algorithm doing the work.", options: { color: NAVY, bold: true } },
  ], { x: 0.6, y: 5.95, w: 12.2, h: 0.7, fontSize: 14, italic: true, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S8 Z3 constraints
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Z3 verifies 25 + 4 interior constraints", "The independent judge — IRC room sizing plus architectural spatial rules");
  const groups = [
    ["1 · Room areas (7)", "living/kitchen/bed ≥ 70 · bath ≥ 25 sq ft", NAVY],
    ["2 · Min dimension (6)", "habitable ≥ 7 ft · bath ≥ 5 ft side", NAVY],
    ["3 · Max dimension (2)", "bathrooms ≤ 15 ft / side", NAVY],
    ["4 · Bath < bedroom (2)", "each ensuite smaller than its bedroom", NAVY],
    ["5 · Sanitation (3)", "baths not adj. kitchen, not adj. each other", TEAL],
    ["6 · Ensuite (2)", "each bath shares a wall with its bedroom", TEAL],
    ["7 · Spatial / coverage (3)", "living on south · inside · within ±5%", TEAL],
    ["8 · Ours, extra (4)", "door→living · kitchen↔living · connectivity · count", GREEN],
  ];
  const cols = 4, cw = 2.95, ch = 1.85, gx = 0.6, gy = 2.0, dx = 3.07, dy = 2.1;
  groups.forEach((g, i) => {
    const x = gx + (i % cols) * dx, y = gy + Math.floor(i / cols) * dy;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: ch, fill: { color: "F8FAFC" }, line: { color: g[2], width: 1.3 }, rectRadius: 0.08 });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: 0.1, fill: { color: g[2] }, line: { color: g[2], width: 0 } });
    s.addText(g[0], { x: x + 0.15, y: y + 0.22, w: cw - 0.3, h: 0.7, fontSize: 13, bold: true, color: g[2], fontFace: "Cambria", margin: 0 });
    s.addText(g[1], { x: x + 0.15, y: y + 0.85, w: cw - 0.3, h: 0.9, fontSize: 10.5, color: DARK, fontFace: "Calibri", margin: 0 });
  });
  s.addText("Scalar rules go through Z3 (measured < required); geometry (overlap, connectivity) is computed directly. Empty violation list = SAT.",
    { x: 0.6, y: 6.5, w: 12.2, h: 0.4, fontSize: 12, italic: true, color: MUTED, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S9 Result visual
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Result — MILP interior, Z3-verified", "8 rooms · 100% coverage · 0 violations · CBC Optimal");
  s.addImage({ path: IMG("milp_result.png"), x: 0.5, y: 1.8, w: 5.4, h: 5.1, sizing: { type: "contain", w: 5.4, h: 5.1 } });
  // schedule table on the right
  const data = [[
    { text: "Room", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
    { text: "W×H", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
    { text: "sq ft", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ["Living", "37×39", "1,443"],
    ["Kitchen", "26×39", "1,014"],
    ["Corridor", "63×4", "252"],
    ["Bath 1 → Bed 1", "6×15", "90"],
    ["Bedroom 1", "17×15", "255"],
    ["Bedroom 3", "17×15", "255"],
    ["Bedroom 2", "17×15", "255"],
    ["Bath 2 → Bed 2", "6×15", "90"],
    [{ text: "TOTAL", options: { bold: true, color: NAVY } },
     { text: "63×58", options: { bold: true, color: NAVY } },
     { text: "3,654", options: { bold: true, color: NAVY } }],
  ];
  s.addTable(data, { x: 6.3, y: 1.95, w: 6.5, h: 4.5, fontSize: 12.5, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE }, rowH: 0.42, colW: [3.0, 1.7, 1.8], valign: "middle" });
  s.addText("Every square foot is assigned; the corridor is the circulation.", { x: 6.3, y: 6.5, w: 6.5, h: 0.35,
    fontSize: 12, italic: true, color: MUTED, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S10 vs reference
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "What's novel vs the verify-and-fix baseline", "We built the part the reference only proposed — and matched its full checker");
  const data = [[
    { text: "", options: { fill: { color: NAVY } } },
    { text: "Verify-and-fix baseline", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
    { text: "Ours (MILP + Z3)", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ["Room placement", "Gemini guesses, Z3 checks", "CBC solves, Z3 confirms"],
    ["Constraint satisfaction", "after 1+ feedback rounds", "guaranteed on first solve"],
    ["Determinism", "LLM output varies", "solver output reproducible"],
    ["Cutting-plane MILP", "listed as future work", "implemented (PuLP + CBC)"],
    ["Interior constraints", "25 rules", "25 rules + 4 extras"],
  ];
  s.addTable(data, { x: 0.6, y: 2.0, w: 12.2, h: 3.6, fontSize: 13.5, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE }, rowH: 0.6, colW: [3.4, 4.4, 4.4], valign: "middle" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.85, w: 12.2, h: 0.95, fill: { color: "F0FDFA" }, line: { color: TEAL, width: 1 }, rectRadius: 0.1 });
  s.addText([
    { text: "Bottom line: ", options: { bold: true, color: TEAL } },
    { text: "the reference proposed cutting-plane MILP as a future direction; ours runs it today, with Z3 confirming all 29 constraints.", options: { color: DARK } },
  ], { x: 0.9, y: 5.95, w: 11.6, h: 0.75, fontSize: 14, fontFace: "Calibri", valign: "middle", margin: 0 });
  addFooter(s);
}

// ============================================================ S11 Takeaways (dark)
{
  const s = mkSlide();
  s.background = { color: NAVY };
  s.addText("Takeaways", { x: 0.8, y: 0.55, w: 12, h: 1.0, fontSize: 40, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.5, w: 3.0, h: 0.04, fill: { color: ICE }, line: { color: ICE, width: 0 } });
  const tk = [
    ["Generate-and-guarantee beats verify-and-fix", "A cutting-plane MILP returns a valid layout on the first solve — no LLM iteration, fully reproducible."],
    ["Z3 stays the judge", "The SMT solver independently confirms 25 IRC/spatial rules + 4 extras; same neuro-symbolic principle as the exterior."],
    ["Topology encodes the hard rules", "A corridor + ensuite band structure makes sanitation, ensuite and non-adjacency true by construction."],
    ["We built the proposed future work", "The reference listed cutting-plane MILP as future work; ours implements it end-to-end (PuLP + CBC)."],
  ];
  let y = 1.95;
  for (const t of tk) {
    s.addText(t[0], { x: 0.8, y, w: 11.8, h: 0.5, fontSize: 17, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
    s.addText(t[1], { x: 0.8, y: y + 0.5, w: 11.8, h: 0.6, fontSize: 13, color: ICE, fontFace: "Calibri", margin: 0 });
    y += 1.18;
  }
  s.addText("Repo: /Users/ojas/ps1-house-layout/   ·   Ojas   ·   Problem 2", { x: 0.8, y: SLIDE_H - 0.5, w: 12, h: 0.35,
    fontSize: 11, color: ICE, italic: true, fontFace: "Calibri", margin: 0 });
}

stamp();
pres.writeFile({ fileName: path.join(PROJ, "Problem2_presentation.pptx") })
  .then(p => console.log("wrote", p))
  .catch(e => { console.error(e); process.exit(1); });
