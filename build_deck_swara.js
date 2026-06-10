/**
 * Swara Wankhede — Problem 2 presentation, built from her documentation
 * (Problem2_Documentation_6_june.docx). Verify-and-fix pipeline, sequential
 * room generation, 25 Z3 constraints, Bellevue test runs, cutting-plane future.
 * Output: Swara_Problem2_presentation.pptx
 */
const path = require("path");
const PG = require("pptxgenjs");

const NAVY = "1F3864", TEAL = "0E7490", INK = "0F172A", MUTED = "64748B",
      ICE = "DBE7F3", WHITE = "FFFFFF", GREEN = "2C7A4B", ORANGE = "C0392B";
const SLIDE_W = 13.333, SLIDE_H = 7.5;
const PROJ = "/Users/ojas/ps1-house-layout";
const IMG = (n) => path.join(PROJ, "output/swara", n);

const pres = new PG();
pres.layout = "LAYOUT_WIDE";
pres.author = "Swara Wankhede";
pres.title = "Problem 2 — Two-Agent Neuro-Symbolic CAD Verification";

let pageCount = 0;
const footers = [];
function mkSlide() { const s = pres.addSlide(); pageCount++; s.__p = pageCount; return s; }
function addFooter(s) { footers.push(s); }
function stamp() {
  for (const s of footers) {
    s.addText(`${s.__p} / ${pageCount}`, { x: SLIDE_W - 1.2, y: SLIDE_H - 0.42, w: 0.9, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri", align: "right" });
    s.addText("Problem 2 · Swara Wankhede", { x: 0.5, y: SLIDE_H - 0.42, w: 6, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri" });
  }
}
function titleBlock(s, t, sub) {
  s.addText(t, { x: 0.6, y: 0.38, w: 12.1, h: 0.8, fontSize: 29, bold: true, color: NAVY, fontFace: "Cambria", margin: 0 });
  if (sub) s.addText(sub, { x: 0.6, y: 1.12, w: 12.1, h: 0.5, fontSize: 15, color: MUTED, italic: true, fontFace: "Calibri", margin: 0 });
}
function statCard(s, x, y, w, h, val, lab, accent = NAVY) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: WHITE }, line: { color: ICE, width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h, fill: { color: accent }, line: { color: accent, width: 0 } });
  s.addText(val, { x: x + 0.22, y: y + 0.14, w: w - 0.36, h: h * 0.56, fontSize: 26, bold: true, color: accent, fontFace: "Cambria", valign: "middle", margin: 0 });
  s.addText(lab, { x: x + 0.22, y: y + h * 0.56, w: w - 0.36, h: h * 0.4, fontSize: 10.5, color: MUTED, fontFace: "Calibri", valign: "top", margin: 0 });
}

// ============================================================ S1 Title
{
  const s = mkSlide();
  s.background = { color: NAVY };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.35, h: SLIDE_H, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addText("PROBLEM 2", { x: 1.0, y: 1.2, w: 11, h: 0.6, fontSize: 22, color: ICE, fontFace: "Cambria", charSpacing: 12, margin: 0 });
  s.addText("Two-Agent Neuro-Symbolic Verification System for CAD Layout Generation with Interior Constraints",
    { x: 1.0, y: 1.95, w: 11.6, h: 1.9, fontSize: 38, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
  s.addText("Gemini generates · Mistral gives feedback · Z3 SMT formally verifies — across four locations",
    { x: 1.0, y: 4.0, w: 11.6, h: 0.7, fontSize: 18, italic: true, color: ICE, fontFace: "Calibri", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 1.0, y: 5.5, w: 4, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addText("Swara Wankhede   ·   6 June 2026", { x: 1.0, y: 5.62, w: 11, h: 0.5, fontSize: 14, color: ICE, fontFace: "Calibri", margin: 0 });
  s.addText("Agent 1: Gemini 2.5 Flash   ·   Agent 2: Mistral   ·   Verifier: Z3 SMT   ·   Locations: Seattle Downtown, Bellevue, Bothell, Redmond",
    { x: 1.0, y: 6.05, w: 11.8, h: 0.5, fontSize: 12.5, color: WHITE, fontFace: "Consolas", margin: 0 });
}

// ============================================================ S2 Problem statement
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "1. Problem Statement", "Extend the two-agent system from the outer boundary to the complete interior");
  s.addText([
    { text: "Building on Problem 1 (outer-boundary verification), the system must now generate and formally verify the full interior of the house.", options: { color: INK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Required floor plan:", options: { color: INK, breakLine: true } },
    { text: "3 bedrooms · 2 bathrooms · 1 kitchen · 1 living room · 1 corridor", options: { bold: true, color: NAVY, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "The layout must satisfy the given architectural constraints, verified by Z3.", options: { color: INK } },
  ], { x: 0.6, y: 2.0, w: 7.0, h: 3.0, fontSize: 16, fontFace: "Calibri", margin: 0 });
  statCard(s, 8.0, 2.0, 4.8, 1.3, "8 rooms", "INCLUDING THE CORRIDOR", NAVY);
  statCard(s, 8.0, 3.5, 4.8, 1.3, "25", "INTERIOR CONSTRAINTS IN Z3", TEAL);
  statCard(s, 8.0, 5.0, 4.8, 1.3, "4", "LOCATIONS WITH OWN CODES", NAVY);
  addFooter(s);
}

// ============================================================ S3 System overview
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "2. System Overview", "A fully automated two-agent pipeline with two Z3 verification stages");
  // three role chips
  const roles = [
    ["Agent 1 — Gemini 2.5 Flash", "Generates Python ezdxf code for the outer boundary, then the interior, room by room", NAVY],
    ["Agent 2 — Mistral", "Reads the Z3 output and writes specific fix instructions back to Agent 1", TEAL],
    ["Verifier — Z3 SMT", "Two stages: outer boundary vs location codes, interior vs IRC + spatial rules", GREEN],
  ];
  let y = 1.95;
  for (const r of roles) {
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 12.2, h: 1.0, fill: { color: "F6F9FC" }, line: { color: ICE, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 0.1, h: 1.0, fill: { color: r[2] }, line: { color: r[2], width: 0 } });
    s.addText(r[0], { x: 0.85, y: y + 0.12, w: 4.2, h: 0.76, fontSize: 15, bold: true, color: r[2], fontFace: "Cambria", valign: "middle", margin: 0 });
    s.addText(r[1], { x: 5.2, y: y + 0.12, w: 7.4, h: 0.76, fontSize: 13, color: INK, fontFace: "Calibri", valign: "middle", margin: 0 });
    y += 1.12;
  }
  s.addText([
    { text: "Flow: ", options: { bold: true, color: NAVY } },
    { text: "pick a location → A1 outer boundary → AST parser → Z3 (SAT/UNSAT + JSON) → A2 feedback loop (max 5) → A1 interior → Z3 interior (25 rules) → A2 loop → final .dxf in Autodesk Viewer.", options: { color: INK } },
  ], { x: 0.6, y: 5.55, w: 12.2, h: 1.2, fontSize: 13.5, fontFace: "Calibri", valign: "top", margin: 0 });
  addFooter(s);
}

// ============================================================ S4 Sequential generation
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "3.1 Sequential Room Generation", "Generate the interior room by room — not all at once (June 5 feedback)");
  s.addText("Generating the whole layout in one step makes it hard for the LLM to satisfy every spatial constraint simultaneously. A defined order improves spatial consistency.",
    { x: 0.6, y: 1.95, w: 12.2, h: 0.7, fontSize: 14, italic: true, color: INK, fontFace: "Calibri", margin: 0 });
  const order = [
    ["1", "Living room", "~20% — nearest the south entry"],
    ["2", "Kitchen", "~10% — adjacent to living, no corridor"],
    ["3", "Corridor", "~5% — 4 ft wide, public → bedroom zone"],
    ["4", "Bedroom 1 + Bath 1", "15% + 6% — ensuite pair"],
    ["5", "Bedroom 2 + Bath 2", "15% + 6% — ensuite pair"],
    ["6", "Bedroom 3", "~13% — remaining area"],
  ];
  let y = 2.75;
  for (const o of order) {
    s.addShape(pres.shapes.OVAL, { x: 0.7, y: y + 0.04, w: 0.55, h: 0.55, fill: { color: NAVY }, line: { color: NAVY, width: 0 } });
    s.addText(o[0], { x: 0.7, y: y + 0.04, w: 0.55, h: 0.55, fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: "Cambria", margin: 0 });
    s.addText(o[1], { x: 1.5, y: y, w: 4.2, h: 0.62, fontSize: 15, bold: true, color: NAVY, fontFace: "Cambria", valign: "middle", margin: 0 });
    s.addText(o[2], { x: 5.8, y: y, w: 7.0, h: 0.62, fontSize: 13.5, color: INK, fontFace: "Calibri", valign: "middle", margin: 0 });
    y += 0.7;
  }
  addFooter(s);
}

// ============================================================ S5 Layers + spatial rules
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "3.2 Layers & 3.3 Spatial Rules in the Prompt", "Each room type on its own DXF layer; the spatial rules are stated to Agent 1");
  s.addText("DXF LAYERS", { x: 0.6, y: 1.9, w: 5.6, h: 0.35, fontSize: 12, bold: true, color: NAVY, charSpacing: 4, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "LIVING · KITCHEN · CORRIDOR · BEDROOMS · BATHROOMS · WINDOWS · DOORS", options: { color: INK } },
  ], { x: 0.6, y: 2.25, w: 5.7, h: 1.2, fontSize: 14, fontFace: "Consolas", margin: 0 });
  s.addText("Each room type is drawn on a separate layer for clarity and independent verification.",
    { x: 0.6, y: 3.5, w: 5.7, h: 1.0, fontSize: 13, italic: true, color: MUTED, fontFace: "Calibri", margin: 0 });

  s.addText("SPATIAL RULES (in A1 prompt)", { x: 6.85, y: 1.9, w: 6.0, h: 0.35, fontSize: 12, bold: true, color: NAVY, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "Living nearest the entry, touching the south wall", options: { bullet: true, breakLine: true } },
    { text: "Kitchen adjacent to living, no corridor between", options: { bullet: true, breakLine: true } },
    { text: "Each bedroom has its own attached bathroom (shared wall)", options: { bullet: true, breakLine: true } },
    { text: "Bathrooms never adjacent to the kitchen", options: { bullet: true, breakLine: true } },
    { text: "The two bathrooms never adjacent to each other", options: { bullet: true, breakLine: true } },
    { text: "Each bathroom smaller than its attached bedroom", options: { bullet: true, breakLine: true } },
    { text: "Each bedroom: exactly 2 windows on different walls", options: { bullet: true, breakLine: true } },
    { text: "Corridor width ≥ 4 ft", options: { bullet: true } },
  ], { x: 6.85, y: 2.25, w: 6.0, h: 4.4, fontSize: 13.5, color: INK, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S6 Z3 framework
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "4. Z3 Interior Verification Framework", "Constraints sourced from IRC R304 and the meeting feedback; checked deterministically");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.95, w: 12.2, h: 1.5, fill: { color: "F0FDFA" }, line: { color: TEAL, width: 1.3 }, rectRadius: 0.1 });
  s.addText("4.1 Constraint sources", { x: 0.85, y: 2.1, w: 11, h: 0.35, fontSize: 13, bold: true, color: TEAL, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "IRC Section R304 — room area and minimum-dimension requirements.", options: { bullet: true, breakLine: true } },
    { text: "June 5 meeting feedback — adjacency, ensuite attachment and spatial placement rules.", options: { bullet: true } },
  ], { x: 0.85, y: 2.5, w: 11.6, h: 0.9, fontSize: 13.5, color: INK, fontFace: "Calibri", margin: 0 });

  s.addText("4.3 How Z3 verifies", { x: 0.6, y: 3.7, w: 11, h: 0.4, fontSize: 16, bold: true, color: NAVY, fontFace: "Cambria", margin: 0 });
  s.addText([
    { text: "A Python AST parser reads the generated interior file and extracts 32 coordinate variables (x, y, w, h for each of 8 rooms incl. the corridor).", options: { bullet: true, breakLine: true } },
    { text: "It computes room areas, adjacency relationships, containment and the living-room position.", options: { bullet: true, breakLine: true } },
    { text: "run_z3_interior() encodes each constraint as a Z3 boolean, adds them all under one And() clause, and calls solver.check().", options: { bullet: true, breakLine: true } },
    { text: "Returns SAT or UNSAT with a full JSON breakdown — including a fix instruction for each failed constraint.", options: { bullet: true } },
  ], { x: 0.6, y: 4.15, w: 12.2, h: 2.6, fontSize: 13.5, color: INK, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S7 the 25 constraints
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "4.2 The 25 Interior Constraints", "Seven groups — IRC sizing plus the meeting's adjacency and attachment rules");
  const groups = [
    ["Group 1 · Room areas (7)", "living/kitchen/bed ≥ 70 · bath ≥ 25 sq ft", NAVY],
    ["Group 2 · Min dimension (6)", "living & bedrooms ≥ 7 ft · baths ≥ 5 ft", NAVY],
    ["Group 3 · Max dimension (2)", "bathrooms ≤ 15 ft / side (added after testing)", ORANGE],
    ["Group 4 · Bath < bedroom (2)", "each ensuite smaller than its bedroom", NAVY],
    ["Group 5 · Bath adjacency (3)", "baths not adj. kitchen, not adj. each other", TEAL],
    ["Group 6 · Bath attachment (2)", "bath shares a wall with its bedroom", TEAL],
    ["Group 7 · Spatial & coverage (3)", "living near south · inside · ±5% area", GREEN],
  ];
  const cols = 4, cw = 2.95, ch = 1.8, gx = 0.6, gy = 2.0, dx = 3.07, dy = 2.05;
  groups.forEach((g, i) => {
    const x = gx + (i % cols) * dx, y = gy + Math.floor(i / cols) * dy;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: ch, fill: { color: "F6F9FC" }, line: { color: g[2], width: 1.3 }, rectRadius: 0.08 });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: 0.1, fill: { color: g[2] }, line: { color: g[2], width: 0 } });
    s.addText(g[0], { x: x + 0.15, y: y + 0.22, w: cw - 0.3, h: 0.7, fontSize: 12.5, bold: true, color: g[2], fontFace: "Cambria", margin: 0 });
    s.addText(g[1], { x: x + 0.15, y: y + 0.82, w: cw - 0.3, h: 0.9, fontSize: 10.5, color: INK, fontFace: "Calibri", margin: 0 });
  });
  // 8th cell: total
  const x = gx + 3 * dx, y = gy + 1 * dy;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: ch, fill: { color: NAVY }, line: { color: NAVY, width: 0 }, rectRadius: 0.08 });
  s.addText("25", { x: x + 0.15, y: y + 0.25, w: cw - 0.3, h: 0.8, fontSize: 34, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
  s.addText("constraints, all checked by Z3", { x: x + 0.15, y: y + 1.05, w: cw - 0.3, h: 0.6, fontSize: 11, color: ICE, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S8 Test Run 6
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "5. Test Run 6 — Bellevue (UNSAT → fix)", "Outer boundary reused (SAT, 2 iters); interior iteration 1 fails 2 of 25");
  s.addImage({ path: IMG("run6.png"), x: 0.5, y: 1.85, w: 7.2, h: 4.6, sizing: { type: "contain", w: 7.2, h: 4.6 } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.0, y: 1.95, w: 4.8, h: 2.0, fill: { color: "FEF3F2" }, line: { color: ORANGE, width: 1.3 }, rectRadius: 0.1 });
  s.addText("ITERATION 1 — UNSAT", { x: 8.2, y: 2.1, w: 4.4, h: 0.4, fontSize: 12, bold: true, color: ORANGE, charSpacing: 2, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "Passed 21 / 25", options: { color: INK, bold: true, breakLine: true } },
    { text: "Failed: bath1 & bath2 min dimension = 4 ft (need ≥ 5 ft).", options: { color: ORANGE } },
  ], { x: 8.2, y: 2.55, w: 4.4, h: 1.3, fontSize: 13, fontFace: "Calibri", margin: 0 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.0, y: 4.2, w: 4.8, h: 2.0, fill: { color: "F0FDFA" }, line: { color: TEAL, width: 1.3 }, rectRadius: 0.1 });
  s.addText("A2 FIX INSTRUCTION", { x: 8.2, y: 4.35, w: 4.4, h: 0.4, fontSize: 12, bold: true, color: TEAL, charSpacing: 2, fontFace: "Calibri", margin: 0 });
  s.addText("Increase each bathroom's smaller side to at least 5 ft while preserving the 21 passing constraints; regenerate.",
    { x: 8.2, y: 4.8, w: 4.4, h: 1.3, fontSize: 13, italic: true, color: INK, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S9 Test Run 7
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "6. Test Run 7 — Bellevue (SAT)", "First fully-verified run: interior converges in 2 iterations, 25 / 25 passed");
  s.addImage({ path: IMG("run7.png"), x: 0.5, y: 1.85, w: 7.2, h: 4.6, sizing: { type: "contain", w: 7.2, h: 4.6 } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.0, y: 1.95, w: 4.8, h: 1.5, fill: { color: "F0FDF4" }, line: { color: GREEN, width: 1.4 }, rectRadius: 0.1 });
  s.addText("FINAL — SAT", { x: 8.2, y: 2.1, w: 4.4, h: 0.4, fontSize: 12, bold: true, color: GREEN, charSpacing: 2, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "25 passed · 0 failed", options: { color: GREEN, bold: true, breakLine: true } },
    { text: "Iter 1 caught a 33 ft-wide bath; bath_max_dimension added.", options: { color: INK } },
  ], { x: 8.2, y: 2.55, w: 4.4, h: 0.9, fontSize: 13, fontFace: "Calibri", margin: 0 });
  s.addText("OBSERVATIONS", { x: 8.0, y: 3.7, w: 4.8, h: 0.35, fontSize: 12, bold: true, color: NAVY, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "The max-dimension constraint correctly flagged the 33 ft bathroom.", options: { bullet: true, breakLine: true } },
    { text: "Gemini repeatedly sets a bathroom's width equal to its bedroom's; the Z3 max-dimension rule is the enforcement layer.", options: { bullet: true } },
  ], { x: 8.0, y: 4.1, w: 4.8, h: 2.4, fontSize: 12.5, color: INK, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S10 cutting plane future
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "7. Cutting-Plane Algorithm — Future Direction", "From verify-and-fix to generate-and-guarantee with a MILP solver");
  s.addText("A cutting-plane algorithm (Mixed-Integer Linear Programming) starts from a relaxed layout, adds a linear cut whenever a constraint is violated, and repeats until only valid solutions remain. The solver would generate optimal layouts rather than verify existing ones.",
    { x: 0.6, y: 1.95, w: 12.2, h: 1.0, fontSize: 14, color: INK, fontFace: "Calibri", margin: 0 });
  const data = [[
    { text: "Current approach (Z3)", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
    { text: "Future approach (MILP + cutting planes)", options: { bold: true, color: WHITE, fill: { color: TEAL } } }],
    ["Gemini generates the layout, Z3 verifies", "MILP solver generates and guarantees satisfaction"],
    ["Verify-and-fix loop", "Generate-and-guarantee"],
    ["May take multiple iterations to converge", "Mathematically optimal on the first solve"],
    ["LLM output is non-deterministic", "Solver output is deterministic and reproducible"],
  ];
  s.addTable(data, { x: 0.6, y: 3.15, w: 12.2, h: 3.0, fontSize: 14, fontFace: "Calibri", color: INK,
    border: { pt: 0.5, color: ICE }, rowH: 0.62, colW: [6.1, 6.1], valign: "middle" });
  s.addText("Recommended tool: OR-Tools CP-SAT — native no-overlap support, scales to 20+ rooms.",
    { x: 0.6, y: 6.4, w: 12.2, h: 0.4, fontSize: 12.5, italic: true, color: MUTED, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S11 file/output structure
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "8–9. File & Output Structure", "Modular code; every iteration's artifacts are logged");
  s.addText("CODE", { x: 0.6, y: 1.9, w: 6, h: 0.35, fontSize: 12, bold: true, color: NAVY, charSpacing: 4, fontFace: "Calibri", margin: 0 });
  s.addTable([
    [{ text: "File", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Role", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ["main.py", "Orchestration, location selection, logging"],
    ["agent1.py", "Gemini prompts (outer + sequential interior)"],
    ["agent2.py", "Mistral feedback from Z3 JSON"],
    ["parser.py", "AST coordinate extractor"],
    ["z3_verifier.py", "run_z3 / run_z3_interior (25 rules)"],
    ["rules/", "4 location building-code files"],
  ], { x: 0.6, y: 2.25, w: 6.0, h: 3.4, fontSize: 11.5, fontFace: "Calibri", color: INK,
       border: { pt: 0.5, color: ICE }, rowH: 0.44, colW: [2.0, 4.0], valign: "middle" });

  s.addText("OUTPUTS (per iteration N)", { x: 6.95, y: 1.9, w: 6, h: 0.35, fontSize: 12, bold: true, color: NAVY, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "generated_layout_iterN.py / interior_iterN.py", options: { bullet: true, breakLine: true } },
    { text: "z3_output_iterN.json / z3_interior_iterN.json", options: { bullet: true, breakLine: true } },
    { text: "feedback_iterN.txt / interior_feedback_iterN.txt", options: { bullet: true, breakLine: true } },
    { text: "logs/run_log.json — token counts + timing per iteration", options: { bullet: true } },
  ], { x: 6.95, y: 2.3, w: 6.0, h: 3.4, fontSize: 13, color: INK, fontFace: "Calibri", margin: 0 });
  addFooter(s);
}

// ============================================================ S12 takeaways
{
  const s = mkSlide();
  s.background = { color: NAVY };
  s.addText("Takeaways", { x: 0.8, y: 0.55, w: 12, h: 1.0, fontSize: 40, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.5, w: 3.0, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  const tk = [
    ["Z3 is the formal judge", "25 interior constraints from IRC R304 and the meeting feedback are checked deterministically with SAT/UNSAT and a JSON fix breakdown."],
    ["Sequential generation improves consistency", "Generating room by room (living → kitchen → corridor → ensuite pairs → bedroom 3) helps the LLM satisfy spatial rules."],
    ["Testing hardened the constraints", "Test runs exposed a 4 ft bath and a 33 ft bath; min- and max-dimension rules were added so Z3 enforces what the prompt cannot."],
    ["Cutting-plane MILP is the next step", "Moving from verify-and-fix to generate-and-guarantee (PuLP / OR-Tools CP-SAT) for optimal, deterministic layouts."],
  ];
  let y = 1.95;
  for (const t of tk) {
    s.addText(t[0], { x: 0.8, y, w: 11.8, h: 0.5, fontSize: 17, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
    s.addText(t[1], { x: 0.8, y: y + 0.5, w: 11.8, h: 0.65, fontSize: 13, color: ICE, fontFace: "Calibri", margin: 0 });
    y += 1.2;
  }
  s.addText("Swara Wankhede   ·   Problem 2   ·   6 June 2026", { x: 0.8, y: SLIDE_H - 0.5, w: 12, h: 0.35,
    fontSize: 11, color: ICE, italic: true, fontFace: "Calibri", margin: 0 });
}

stamp();
pres.writeFile({ fileName: path.join(PROJ, "Swara_Problem2_presentation.pptx") })
  .then(p => console.log("wrote", p))
  .catch(e => { console.error(e); process.exit(1); });
