/**
 * PS1 Presentation builder — Midnight Executive palette
 * 13 slides for the 3pm IST 2026-05-31 demo
 */
const path = require("path");
const pptxgen = require("pptxgenjs");

const NAVY   = "1E2761";  // primary
const ICE    = "CADCFC";  // secondary
const WHITE  = "FFFFFF";  // accent
const RED    = "B85042";  // plot color
const GREEN  = "2C5F2D";  // tree color
const ORANGE = "F96167";  // alert color
const MUTED  = "64748B";
const DARK   = "0F172A";

const SLIDE_W = 13.333;   // LAYOUT_WIDE
const SLIDE_H = 7.5;
const PROJ = "/Users/ojas/ps1-house-layout";
const IMG = (n) => path.join(PROJ, "output/slides", n);

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Ojas";
pres.title  = "PS1 — Engineering Drawing Verification";

// ============================================================================
// Helpers
// ============================================================================
// Auto page-numbering: mkSlide() counts every slide; addPageNumber() defers the
// footer so the total is correct no matter how many slides we add/insert.
let pageCount = 0;
const deferredFooters = [];
function mkSlide() {
  const s = pres.addSlide();
  pageCount += 1;
  s.__page = pageCount;
  return s;
}
function addPageNumber(slide) {
  deferredFooters.push(slide);
}
function stampFooters() {
  for (const slide of deferredFooters) {
    slide.addText(`${slide.__page} / ${pageCount}`, {
      x: SLIDE_W - 1.2, y: SLIDE_H - 0.45, w: 0.9, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri", align: "right",
    });
    slide.addText("PS1 · House Layout · Ojas", {
      x: 0.5, y: SLIDE_H - 0.45, w: 6, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri",
    });
  }
}

function titleBlock(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.6, y: 0.4, w: 12, h: 0.8,
    fontSize: 30, bold: true, color: NAVY, fontFace: "Cambria", margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6, y: 1.15, w: 12, h: 0.5,
      fontSize: 16, color: MUTED, fontFace: "Calibri", italic: true, margin: 0,
    });
  }
}

function statCard(slide, x, y, w, h, value, label, accent = NAVY) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: WHITE },
    line: { color: ICE, width: 1.5 },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.08, h,
    fill: { color: accent }, line: { color: accent, width: 0 },
  });
  slide.addText(value, {
    x: x + 0.25, y: y + 0.2, w: w - 0.4, h: h * 0.55,
    fontSize: 32, bold: true, color: accent, fontFace: "Cambria",
    align: "left", valign: "middle", margin: 0,
  });
  slide.addText(label, {
    x: x + 0.25, y: y + h * 0.55, w: w - 0.4, h: h * 0.4,
    fontSize: 11, color: MUTED, fontFace: "Calibri",
    align: "left", valign: "top", margin: 0,
  });
}

// ============================================================================
// SLIDE 1 — Title
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: NAVY };

  // ICE-blue accent block on left
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.35, h: SLIDE_H,
    fill: { color: ICE }, line: { color: ICE, width: 0 },
  });

  s.addText("PS1", {
    x: 1.0, y: 1.4, w: 11, h: 1.0,
    fontSize: 22, color: ICE, fontFace: "Cambria", bold: false,
    charSpacing: 12, margin: 0,
  });
  s.addText("Engineering Drawing Verification", {
    x: 1.0, y: 2.2, w: 11, h: 1.4,
    fontSize: 52, bold: true, color: WHITE, fontFace: "Cambria", margin: 0,
  });
  s.addText("Automated workflow: a verified exterior shell + a verified interior floor plan", {
    x: 1.0, y: 3.7, w: 11, h: 0.7,
    fontSize: 20, italic: true, color: ICE, fontFace: "Calibri", margin: 0,
  });

  // bottom strip
  s.addShape(pres.shapes.RECTANGLE, {
    x: 1.0, y: 5.6, w: 4, h: 0.04,
    fill: { color: ICE }, line: { color: ICE, width: 0 },
  });
  s.addText("Ojas  ·  Cohort PS1  ·  Two-phase loop: exterior  →  interior", {
    x: 1.0, y: 5.7, w: 11, h: 0.5,
    fontSize: 14, color: ICE, fontFace: "Calibri", margin: 0,
  });
  s.addText("Generator: Gemini 2.5 Flash  ·  Verifier: Llama 3.3 70B (Groq) + Z3", {
    x: 1.0, y: 6.15, w: 11, h: 0.5,
    fontSize: 13, color: WHITE, fontFace: "Consolas", margin: 0,
  });
}

// ============================================================================
// SLIDE 2 — The Problem
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The problem",
             "Build a two-agent system that produces a verified house drawing on a tricky plot");

  // Left: the brief in plain language
  s.addText("WHAT THE BRIEF ASKS", {
    x: 0.6, y: 1.9, w: 6.0, h: 0.4,
    fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addText([
    { text: "Agent 1 (Generator)", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "Write Python (ezdxf) that draws the outer periphery of a house on the plot.",
      options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Agent 2 (Verifier)", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "Check the design against Seattle Building Code (SBC) using Z3. On fail, send actionable feedback to A1.",
      options: { color: DARK } },
  ], { x: 0.6, y: 2.3, w: 6.0, h: 2.4, fontSize: 14, fontFace: "Calibri", margin: 0 });

  s.addText("HARD REQUIREMENTS", {
    x: 0.6, y: 4.9, w: 6.0, h: 0.4,
    fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addText([
    { text: "Protected tree cannot be touched (~$50k fine)", options: { bullet: true, breakLine: true } },
    { text: "Setbacks per SBC", options: { bullet: true, breakLine: true } },
    { text: "Single entry side: door + parking together (fire egress)", options: { bullet: true, breakLine: true } },
    { text: "Maximize area coverage", options: { bullet: true, breakLine: true } },
    { text: "Complete interior: 3 bedrooms · 1 kitchen · 2 bathrooms · 1 living", options: { bullet: true, bold: true, color: NAVY } },
  ], { x: 0.6, y: 5.3, w: 6.0, h: 1.8, fontSize: 13, color: DARK, fontFace: "Calibri", margin: 0 });

  // Right: plot image
  s.addImage({ path: IMG("plot_only.png"), x: 7.2, y: 1.9, w: 5.6, h: 5.0, sizing: { type: "contain", w: 5.6, h: 5.0 } });

  addPageNumber(s, 2, 13);
}

// ============================================================================
// SLIDE 3 — Design principle
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Design principle",
             "Z3 is the judge. LLMs only generate and explain.");

  // The trap (left)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.9, w: 5.9, h: 4.7,
    fill: { color: "FEF2F2" }, line: { color: ORANGE, width: 1.5 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.9, w: 0.1, h: 4.7,
    fill: { color: ORANGE }, line: { color: ORANGE, width: 0 },
  });
  s.addText("THE TRAP", {
    x: 0.95, y: 2.1, w: 5.4, h: 0.4,
    fontSize: 12, bold: true, color: ORANGE, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addText("LLM-as-verifier", {
    x: 0.95, y: 2.5, w: 5.4, h: 0.6,
    fontSize: 22, bold: true, color: DARK, fontFace: "Cambria", margin: 0,
  });
  s.addText([
    { text: "The verifier is also an LLM, so it agrees too easily, hallucinates measurements, and you cannot reproduce its decisions.",
      options: { breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Two chatbots discussing whether one number is bigger than another." },
  ], { x: 0.95, y: 3.2, w: 5.4, h: 3.2, fontSize: 13, color: DARK, fontFace: "Calibri", italic: false, margin: 0 });

  // Our split (right)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 1.9, w: 5.9, h: 4.7,
    fill: { color: "F0FDF4" }, line: { color: GREEN, width: 1.5 },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 1.9, w: 0.1, h: 4.7,
    fill: { color: GREEN }, line: { color: GREEN, width: 0 },
  });
  s.addText("OUR SPLIT", {
    x: 7.2, y: 2.1, w: 5.4, h: 0.4,
    fontSize: 12, bold: true, color: GREEN, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addText("Judge ≠ Explainer", {
    x: 7.2, y: 2.5, w: 5.4, h: 0.6,
    fontSize: 22, bold: true, color: DARK, fontFace: "Cambria", margin: 0,
  });
  s.addText([
    { text: "Generation = LLM job (Gemini)", options: { bullet: true, breakLine: true } },
    { text: "Judging = SMT solver job (Z3)", options: { bullet: true, breakLine: true, bold: true } },
    { text: "Explanation = LLM job (Llama on Groq)", options: { bullet: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Z3 is deterministic: same house + same rules → same verdict every time. Reproducible, traceable.",
      options: { italic: true, color: NAVY } },
  ], { x: 7.2, y: 3.2, w: 5.4, h: 3.2, fontSize: 13, color: DARK, fontFace: "Calibri", margin: 0 });

  addPageNumber(s, 3, 13);
}

// ============================================================================
// SLIDE 4 — Architecture
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Architecture",
             "Agent 1 generates · Agent 2 (parser + Z3 + Llama) verifies · loop");

  // ASCII-ish boxed diagram — we draw real shapes
  const cy = 4.0;
  const boxH = 1.1;

  // A1 box
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: cy - boxH/2, w: 2.4, h: boxH,
    fill: { color: NAVY }, line: { color: NAVY, width: 0 }, rectRadius: 0.1,
  });
  s.addText([
    { text: "Agent 1", options: { bold: true, color: WHITE, breakLine: true, fontSize: 16 } },
    { text: "Gemini 2.5 Flash", options: { color: ICE, fontSize: 11 } },
  ], { x: 0.6, y: cy - boxH/2, w: 2.4, h: boxH, fontFace: "Cambria", align: "center", valign: "middle", margin: 0 });

  // A2 grouped box (parser + Z3 + Llama)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 4.6, y: 2.0, w: 8.2, h: 4.2,
    fill: { color: "F8FAFC" }, line: { color: NAVY, width: 1.5, dashType: "dash" }, rectRadius: 0.12,
  });
  s.addText("AGENT 2 — Verifier", {
    x: 4.75, y: 2.05, w: 7, h: 0.4,
    fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });

  // Inside A2: three small boxes — parser, Z3, llama
  const sub = [
    { x: 4.85, y: 2.6, label: "Parser",  sub: "regex on magic\n comments", color: MUTED },
    { x: 7.05, y: 2.6, label: "Z3",      sub: "verifier + optimizer\n(judge)", color: NAVY },
    { x: 9.25, y: 2.6, label: "Llama",   sub: "feedback writer\non Groq", color: GREEN },
  ];
  for (const b of sub) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: b.x, y: b.y, w: 1.9, h: 1.5,
      fill: { color: WHITE }, line: { color: b.color, width: 1.5 }, rectRadius: 0.08,
    });
    s.addText(b.label, {
      x: b.x, y: b.y + 0.15, w: 1.9, h: 0.5,
      fontSize: 16, bold: true, color: b.color, fontFace: "Cambria",
      align: "center", margin: 0,
    });
    s.addText(b.sub, {
      x: b.x, y: b.y + 0.75, w: 1.9, h: 0.7,
      fontSize: 10, color: MUTED, fontFace: "Calibri",
      align: "center", margin: 0,
    });
  }

  // Z3 verdict labels
  s.addText("✓ PASS  →  emit .dxf", {
    x: 4.85, y: 4.3, w: 7.7, h: 0.4,
    fontSize: 11, color: GREEN, fontFace: "Consolas", align: "center", margin: 0,
  });
  s.addText("✗ FAIL  →  violations sent to Llama", {
    x: 4.85, y: 4.7, w: 7.7, h: 0.4,
    fontSize: 11, color: ORANGE, fontFace: "Consolas", align: "center", margin: 0,
  });
  s.addText('"Out of 9 constraints, you missed N — fix and regenerate."', {
    x: 4.85, y: 5.15, w: 7.7, h: 0.6,
    fontSize: 12, italic: true, color: DARK, fontFace: "Calibri", align: "center", margin: 0,
  });

  // Arrow A1 → A2 (top arrow into A2)
  s.addShape(pres.shapes.LINE, {
    x: 3.0, y: cy, w: 1.6, h: 0,
    line: { color: NAVY, width: 2, endArrowType: "triangle" },
  });
  s.addText("ezdxf code", {
    x: 3.0, y: cy - 0.4, w: 1.6, h: 0.3,
    fontSize: 9, color: MUTED, fontFace: "Consolas", align: "center", margin: 0,
  });

  // Feedback loop arrow (A2 back to A1)
  s.addShape(pres.shapes.LINE, {
    x: 1.8, y: 5.9, w: 0, h: -1.0,
    line: { color: ORANGE, width: 2 },
  });
  s.addShape(pres.shapes.LINE, {
    x: 1.8, y: 5.9, w: 7.05, h: 0,
    line: { color: ORANGE, width: 2 },
  });
  s.addShape(pres.shapes.LINE, {
    x: 8.85, y: 5.9, w: 0, h: -0.2,
    line: { color: ORANGE, width: 2, endArrowType: "triangle" },
  });
  s.addText("feedback (only on fail)", {
    x: 3.0, y: 6.0, w: 4, h: 0.3,
    fontSize: 10, color: ORANGE, fontFace: "Calibri", italic: true, margin: 0,
  });

  addPageNumber(s, 4, 13);
}

// ============================================================================
// SLIDE 5 — The plot
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The plot",
             "L-shape from Anupam's hand-drawn sketch — closes exactly to 6,420 sq ft");

  s.addImage({ path: IMG("plot_only.png"),
               x: 0.6, y: 1.9, w: 6.5, h: 5.0, sizing: { type: "contain", w: 6.5, h: 5.0 } });

  // Right: dimensions table
  s.addText("CLOCKWISE FROM TOP-LEFT", {
    x: 7.4, y: 1.9, w: 5.5, h: 0.4,
    fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addTable([
    [{ text: "Edge", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Length", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ["top E",            "75 ft"],
    ["step up",          "4 ft"],
    ["tree-notch top",   "5 ft"],
    ["right edge S",     "80 ft"],
    ["bottom-right inset W", "5 ft"],
    ["entry tab right",  "8 ft"],
    ["entry tab bottom W", "40 ft (door + parking)"],
    ["entry tab left",   "8 ft"],
    ["bottom-left W",    "35 ft"],
    ["left edge N",      "76 ft (closes ✓)"],
  ], {
    x: 7.4, y: 2.35, w: 5.5, h: 4.0,
    fontSize: 11, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE },
    rowH: 0.32, colW: [2.5, 3.0],
  });

  s.addText("Plot area = 6,420 sq ft", {
    x: 7.4, y: 6.45, w: 5.5, h: 0.5,
    fontSize: 16, bold: true, color: NAVY, fontFace: "Cambria", margin: 0,
  });

  addPageNumber(s, 5, 13);
}

// ============================================================================
// SLIDE 6 — Constraints encoded
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "9 SBC constraints encoded in Z3",
             "Every rule has a numeric threshold, a Z3 expression, and a citation");

  // Wide table
  const data = [
    [{ text: "#", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Rule", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Z3 expression", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Source", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ["1", "Front (south) setback ≥ 20 ft",          "y_min - 0 ≥ 20",        "SDCI Tip 320"],
    ["2", "Rear (north) setback ≥ 10 ft",           "88 - y_max ≥ 10",        "SDCI Tip 320"],
    ["3", "Side setbacks ≥ 5 ft (each)",            "x_min ≥ 5 ∧ 80 - x_max ≥ 5", "SDCI Tip 320"],
    ["4", "Minimum footprint ≥ 20 × 20 ft",         "(x_max-x_min) ≥ 20 ∧ ...", "derived"],
    ["5", "All 4 corners inside L-shape polygon",   "ray-cast point-in-polygon", "sketch"],
    ["6", "Distance to tree ≥ 4 ft",                "dx² + dy² ≥ 16",          "SMC 25.11.090"],
    ["7", "Door on south wall, inset ≥ 2 ft",       "door_y = y_min ∧ ...",   "IBC 2021 §1006"],
    ["8", "Door in entry segment x ∈ [35, 75]",     "35 ≤ door_x ≤ 75",       "fire egress"],
    [{ text: "9", options: { bold: true, color: NAVY } },
     { text: "Footprint ≥ 90% of Z3-computed max", options: { bold: true, color: NAVY } },
     { text: "area ≥ 0.9 · MAX", options: { bold: true, color: NAVY } },
     { text: 'brief: "maximize area"', options: { bold: true, color: NAVY } }],
  ];
  s.addTable(data, {
    x: 0.6, y: 1.8, w: 12.2, h: 4.4,
    fontSize: 11, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE },
    rowH: 0.4, colW: [0.5, 4.3, 4.6, 2.8],
    valign: "middle",
  });

  s.addText("Rule 9 turns the brief's vague 'maximize' from a prompt suggestion into a verifiable hard constraint.", {
    x: 0.6, y: 6.45, w: 12.2, h: 0.4,
    fontSize: 12, italic: true, color: MUTED, fontFace: "Calibri", margin: 0,
  });

  addPageNumber(s, 6, 13);
}

// ============================================================================
// SLIDE 7 — Z3 Optimize result
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Z3 doesn't just verify — it computes the maximum",
             "Declare house corners as symbolic Reals · Add all SBC rules · Optimize area");

  // Code block
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.9, w: 7.1, h: 3.2,
    fill: { color: DARK }, line: { color: DARK, width: 0 },
  });
  s.addText([
    { text: "from z3 import Real, Optimize\n", options: { color: "94A3B8" } },
    { text: "\n", options: {} },
    { text: "x_min, x_max, y_min, y_max = ", options: { color: "E2E8F0" } },
    { text: "Reals(...)\n", options: { color: "FBBF24" } },
    { text: "opt = ", options: { color: "E2E8F0" } },
    { text: "Optimize()\n", options: { color: "FBBF24" } },
    { text: "opt.add(x_min >= 5, x_max <= 75)   ", options: { color: "E2E8F0" } },
    { text: "# side setbacks\n", options: { color: "64748B" } },
    { text: "opt.add(y_min >= 20, y_max <= 78)  ", options: { color: "E2E8F0" } },
    { text: "# front+rear\n", options: { color: "64748B" } },
    { text: "opt.maximize(x_max - x_min)\n", options: { color: "E2E8F0" } },
    { text: "opt.maximize(y_max - y_min)\n", options: { color: "E2E8F0" } },
    { text: "opt.check()\n", options: { color: "E2E8F0" } },
  ], {
    x: 0.85, y: 2.05, w: 6.7, h: 3.0,
    fontSize: 12, fontFace: "Consolas", color: "E2E8F0",
    valign: "top", margin: 0,
  });

  // Result box
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 8.1, y: 1.9, w: 4.7, h: 3.2,
    fill: { color: "F0FDF4" }, line: { color: GREEN, width: 1.5 }, rectRadius: 0.1,
  });
  s.addText("Z3 OUTPUT", {
    x: 8.3, y: 2.0, w: 4.4, h: 0.4,
    fontSize: 12, bold: true, color: GREEN, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addText("4,060 sq ft", {
    x: 8.3, y: 2.4, w: 4.4, h: 0.9,
    fontSize: 44, bold: true, color: NAVY, fontFace: "Cambria", margin: 0,
  });
  s.addText("Provable maximum legal house", {
    x: 8.3, y: 3.3, w: 4.4, h: 0.4,
    fontSize: 13, color: MUTED, fontFace: "Calibri", margin: 0,
  });
  s.addText([
    { text: "Corners: (5, 20) → (75, 78)", options: { breakLine: true } },
    { text: "Dimensions: 70 × 58 ft" },
  ], { x: 8.3, y: 3.85, w: 4.4, h: 1.1, fontSize: 13, color: DARK, fontFace: "Consolas", margin: 0 });

  // Bottom: how this becomes a constraint
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 5.4, w: 12.2, h: 1.6,
    fill: { color: ICE }, line: { color: NAVY, width: 1 }, rectRadius: 0.1,
  });
  s.addText([
    { text: "Then we plug the Z3-computed max back into the verifier as rule #9: ", options: { color: DARK } },
    { text: "house_area ≥ 0.9 · 4060 = 3,654 sq ft", options: { color: NAVY, bold: true, fontFace: "Consolas" } },
    { text: ".", options: { color: DARK } },
    { text: " ", options: { breakLine: true } },
    { text: "Now A1 actually has to push, or Z3 will reject.", options: { color: NAVY, italic: true } },
  ], { x: 0.9, y: 5.55, w: 11.6, h: 1.3, fontSize: 16, fontFace: "Calibri", valign: "middle", margin: 0 });

  addPageNumber(s, 7, 13);
}

// ============================================================================
// SLIDE 8 — Prompt strategy comparison (memorable slide)
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Prompt strategy moved coverage from 29% → 59%",
             "Same model, same Z3, same plot — only the prompt to A1 changed");

  s.addImage({ path: IMG("comparison.png"),
               x: 0.4, y: 1.85, w: 12.6, h: 4.6, sizing: { type: "contain", w: 12.6, h: 4.6 } });

  s.addText([
    { text: "Verbose prompt anchored Gemini to the entry-tab x-range (35→70). ", options: { color: DARK } },
    { text: "Stripping the polygon coordinates and emphasizing the maximize-area objective freed it to push against legal limits. ", options: { color: DARK } },
    { text: "Adding the Z3 area constraint forced one feedback round and got us to 59%.", options: { color: NAVY, bold: true } },
  ], { x: 0.6, y: 6.55, w: 12.2, h: 0.7, fontSize: 13, fontFace: "Calibri", margin: 0 });

  addPageNumber(s, 8, 13);
}

// ============================================================================
// SLIDE 9 — Demo trace (loop in action)
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Demo trace — the loop in action",
             "Iter 1 fails area-coverage · A2 explains · iter 2 lands above threshold");

  // Iter 1 box (red)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 1.9, w: 6.0, h: 2.4,
    fill: { color: "FEF2F2" }, line: { color: ORANGE, width: 1.5 }, rectRadius: 0.1,
  });
  s.addText("ITER 1  —  ✗ Z3 rejected", {
    x: 0.85, y: 2.0, w: 5.6, h: 0.4,
    fontSize: 12, bold: true, color: ORANGE, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "Gemini → ", options: { color: MUTED } },
    { text: "3,190 sq ft  (78.6% of Z3 max)", options: { color: DARK, bold: true, fontFace: "Consolas", breakLine: true } },
    { text: "Z3: ", options: { color: MUTED } },
    { text: "min_area_coverage FAILS — need ≥ 3,654", options: { color: ORANGE, fontFace: "Consolas" } },
  ], { x: 0.85, y: 2.5, w: 5.6, h: 1.7, fontSize: 13, fontFace: "Calibri", margin: 0 });

  // A2 feedback box (navy)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.85, y: 1.9, w: 6.0, h: 2.4,
    fill: { color: NAVY }, line: { color: NAVY, width: 0 }, rectRadius: 0.1,
  });
  s.addText("A2 (Llama on Groq) writes:", {
    x: 7.1, y: 2.0, w: 5.6, h: 0.4,
    fontSize: 12, bold: true, color: ICE, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: '"Out of 9 SBC constraints, you missed 1 — fix and regenerate.', options: { color: WHITE, italic: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "* Increase house footprint to at least 3,654 sq ft by reducing setbacks; consider tightening any setback with available slack to expand the footprint by at least 464 sq ft.”", options: { color: WHITE, italic: true } },
  ], { x: 7.1, y: 2.5, w: 5.6, h: 1.7, fontSize: 11, fontFace: "Calibri", margin: 0 });

  // Iter 2 box (green)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 4.5, w: 12.2, h: 2.6,
    fill: { color: "F0FDF4" }, line: { color: GREEN, width: 1.5 }, rectRadius: 0.1,
  });
  s.addText("ITER 2  —  ✓ Z3 PASSES", {
    x: 0.85, y: 4.6, w: 11.6, h: 0.4,
    fontSize: 12, bold: true, color: GREEN, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "Gemini → ", options: { color: MUTED } },
    { text: "3,770 sq ft  (92.9% of Z3 max, 58.7% of plot)", options: { color: DARK, bold: true, fontFace: "Consolas", breakLine: true } },
    { text: "Z3: ", options: { color: MUTED } },
    { text: "ALL 9 constraints satisfied", options: { color: GREEN, fontFace: "Consolas", bold: true, breakLine: true } },
    { text: "Emitter writes final_iter_02.dxf — deterministic, decoupled from any LLM execution.", options: { color: DARK, italic: true } },
  ], { x: 0.85, y: 5.1, w: 11.6, h: 1.9, fontSize: 14, fontFace: "Calibri", margin: 0 });

  addPageNumber(s, 9, 13);
}

// ============================================================================
// SLIDE 10 — Final result (visual)
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Final result",
             "3,770 sq ft house — 92.9% of the formal optimum");

  s.addImage({ path: IMG("vs_optimal.png"),
               x: 0.6, y: 1.85, w: 12.2, h: 4.8, sizing: { type: "contain", w: 12.2, h: 4.8 } });

  addPageNumber(s, 10, 13);
}

// ============================================================================
// SLIDE 11 — Full workflow (two phases)  [INTERIOR]
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "One automated workflow, two phases",
             "The same neuro-symbolic loop runs twice — exterior shell, then interior plan");

  const boxY = 2.0, boxH = 3.3;

  // Phase 1 (exterior)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: boxY, w: 5.7, h: boxH,
    fill: { color: "F8FAFC" }, line: { color: NAVY, width: 1.5 }, rectRadius: 0.12,
  });
  s.addText("PHASE 1 — EXTERIOR", {
    x: 0.85, y: boxY + 0.15, w: 5.2, h: 0.4,
    fontSize: 13, bold: true, color: NAVY, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "Z3 Optimize → provable max-area target", options: { bullet: true, breakLine: true } },
    { text: "A1 (Gemini) draws the house outline", options: { bullet: true, breakLine: true } },
    { text: "Z3 verifies 9 SBC rules", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "A2 (Llama) explains any failure → loop", options: { bullet: true } },
  ], { x: 0.95, y: boxY + 0.6, w: 5.1, h: 1.9, fontSize: 13, color: DARK, fontFace: "Calibri", margin: 0 });
  s.addText("→  verified 63 × 58 ft footprint + door", {
    x: 0.85, y: boxY + 2.7, w: 5.4, h: 0.5,
    fontSize: 13, italic: true, bold: true, color: GREEN, fontFace: "Calibri", margin: 0,
  });

  // Handoff arrow
  s.addShape(pres.shapes.LINE, {
    x: 6.35, y: boxY + boxH / 2, w: 0.6, h: 0,
    line: { color: NAVY, width: 2.5, endArrowType: "triangle" },
  });

  // Phase 2 (interior)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 7.05, y: boxY, w: 5.7, h: boxH,
    fill: { color: "F0FDF4" }, line: { color: GREEN, width: 1.5 }, rectRadius: 0.12,
  });
  s.addText("PHASE 2 — INTERIOR", {
    x: 7.3, y: boxY + 0.15, w: 5.2, h: 0.4,
    fontSize: 13, bold: true, color: GREEN, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "Z3 synthesizes a provable 7-room tiling", options: { bullet: true, breakLine: true } },
    { text: "A1 (Gemini) partitions the footprint", options: { bullet: true, breakLine: true } },
    { text: "Z3 verifies 10 interior rules", options: { bullet: true, breakLine: true, bold: true, color: GREEN } },
    { text: "A2 (Llama) explains any failure → loop", options: { bullet: true } },
  ], { x: 7.4, y: boxY + 0.6, w: 5.1, h: 1.9, fontSize: 13, color: DARK, fontFace: "Calibri", margin: 0 });
  s.addText("→  complete 7-room floor plan + .dxf", {
    x: 7.3, y: boxY + 2.7, w: 5.4, h: 0.5,
    fontSize: 13, italic: true, bold: true, color: GREEN, fontFace: "Calibri", margin: 0,
  });

  // Bottom takeaway band
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 5.6, w: 12.2, h: 1.3,
    fill: { color: ICE }, line: { color: NAVY, width: 1 }, rectRadius: 0.1,
  });
  s.addText([
    { text: "Same pattern both phases: ", options: { color: DARK } },
    { text: "LLM proposes · Z3 proves · LLM explains.", options: { color: NAVY, bold: true } },
    { text: "  If A1 ever stalls, the Z3-synthesized layout is a guaranteed fallback — the run always ends Z3-verified.",
      options: { color: DARK, italic: true } },
  ], { x: 0.9, y: 5.7, w: 11.6, h: 1.1, fontSize: 15, fontFace: "Calibri", valign: "middle", margin: 0 });

  addPageNumber(s);
}

// ============================================================================
// SLIDE 12 — Interior program + 10 rules  [INTERIOR]
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The interior: 7 rooms, 10 Z3 rules",
             "A required room program, checked exactly the way the setbacks were");

  // Left — the room program
  s.addText("ROOM PROGRAM", {
    x: 0.6, y: 1.9, w: 5.6, h: 0.4,
    fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addTable([
    [{ text: "Count", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Room", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Minimum", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ["3 ×", "Bedroom", "≥ 100 sq ft, side ≥ 9 ft"],
    ["1 ×", "Kitchen", "≥ 80 sq ft, side ≥ 7 ft"],
    ["2 ×", "Bathroom", "≥ 40 sq ft, side ≥ 5 ft"],
    ["1 ×", "Living", "≥ 200 sq ft, side ≥ 12 ft"],
  ], {
    x: 0.6, y: 2.35, w: 5.9, h: 2.2,
    fontSize: 13, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE }, rowH: 0.45, colW: [0.9, 2.0, 3.0], valign: "middle",
  });
  s.addText("Minimums modeled on the International Residential Code (IRC R304).", {
    x: 0.6, y: 4.7, w: 5.9, h: 0.8,
    fontSize: 12, italic: true, color: MUTED, fontFace: "Calibri", margin: 0,
  });

  // Right — the 10 rules in 3 groups
  s.addText("10 RULES (Z3 rejects any violation)", {
    x: 6.85, y: 1.9, w: 6.0, h: 0.4,
    fontSize: 12, bold: true, color: NAVY, fontFace: "Calibri", charSpacing: 4, margin: 0,
  });
  s.addText([
    { text: "STRUCTURE", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "exact room counts · all rooms inside footprint · no overlaps · tiles the footprint with no gaps",
      options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "SIZE", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "each room meets its minimum area · and its minimum side (no slivers)",
      options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "DESIGN", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "front door opens into the living room · kitchen adjoins living · wet wall (kitchen ↔ a bathroom) · every room reachable through a ≥ 2.5 ft doorway",
      options: { color: DARK } },
  ], { x: 6.85, y: 2.35, w: 6.0, h: 4.4, fontSize: 13.5, fontFace: "Calibri", color: DARK, margin: 0 });

  addPageNumber(s);
}

// ============================================================================
// SLIDE 13 — Z3 synthesizes the interior  [INTERIOR]
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Z3 doesn't just check a plan — it proves one exists",
             "A 3-band slicing layout makes the tiling exact by construction; Z3 solves the cuts");

  // Left — explanation
  s.addText([
    { text: "The hard part of a floor plan is tiling — filling the footprint with no gaps or overlaps. ",
      options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "We fix the topology to three horizontal bands and let Z3 solve the cut positions. ",
      options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Any choice of cuts tiles exactly", options: { color: NAVY, bold: true } },
    { text: " — so feasibility is guaranteed. All the size rules are linear, so Z3 solves in the fast (LRA) fragment.",
      options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "The result is certified by the same verifier the agent loop uses, and serves as the guaranteed fallback.",
      options: { color: NAVY, italic: true } },
  ], { x: 0.6, y: 1.95, w: 6.6, h: 4.6, fontSize: 14.5, fontFace: "Calibri", margin: 0 });

  // Right — mini band schematic
  const bx = 7.7, bw = 5.0;       // schematic x, width
  // Bedroom band (top, green) — 3 columns
  const bedY = 1.95, bedH = 1.9;
  for (let i = 0; i < 3; i++) {
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx + i * (bw / 3), y: bedY, w: bw / 3, h: bedH,
      fill: { color: "E5F0E0" }, line: { color: GREEN, width: 1.5 },
    });
  }
  s.addText("3 × Bedroom", { x: bx, y: bedY + bedH / 2 - 0.2, w: bw, h: 0.4,
    fontSize: 12, bold: true, color: GREEN, fontFace: "Calibri", align: "center", margin: 0 });
  // Bath band (middle, blue) — 2 columns
  const batY = bedY + bedH, batH = 1.0;
  for (let i = 0; i < 2; i++) {
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx + i * (bw / 2), y: batY, w: bw / 2, h: batH,
      fill: { color: "E3ECF7" }, line: { color: "1D4ED8", width: 1.5 },
    });
  }
  s.addText("2 × Bathroom", { x: bx, y: batY + batH / 2 - 0.2, w: bw, h: 0.4,
    fontSize: 12, bold: true, color: "1D4ED8", fontFace: "Calibri", align: "center", margin: 0 });
  // Public band (bottom): living (cyan) + kitchen (orange)
  const pubY = batY + batH, pubH = 1.5;
  s.addShape(pres.shapes.RECTANGLE, {
    x: bx, y: pubY, w: bw * 0.62, h: pubH,
    fill: { color: "DCEEF7" }, line: { color: "065A82", width: 1.5 },
  });
  s.addText("Living", { x: bx, y: pubY + pubH / 2 - 0.2, w: bw * 0.62, h: 0.4,
    fontSize: 12, bold: true, color: "065A82", fontFace: "Calibri", align: "center", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, {
    x: bx + bw * 0.62, y: pubY, w: bw * 0.38, h: pubH,
    fill: { color: "FBE3D6" }, line: { color: "C2410C", width: 1.5 },
  });
  s.addText("Kitchen", { x: bx + bw * 0.62, y: pubY + pubH / 2 - 0.2, w: bw * 0.38, h: 0.4,
    fontSize: 11, bold: true, color: "C2410C", fontFace: "Calibri", align: "center", margin: 0 });
  // Door marker on south (bottom) wall of the living room
  s.addShape(pres.shapes.RECTANGLE, {
    x: bx + bw * 0.28, y: pubY + pubH - 0.05, w: 0.5, h: 0.1,
    fill: { color: "065A82" }, line: { color: "065A82", width: 0 },
  });
  s.addText("door → living", { x: bx, y: pubY + pubH + 0.08, w: bw, h: 0.3,
    fontSize: 10, italic: true, color: "065A82", fontFace: "Calibri", align: "center", margin: 0 });

  addPageNumber(s);
}

// ============================================================================
// SLIDE 14 — Interior demo trace  [INTERIOR]
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Interior demo trace — Z3 catches a real mistake",
             "Iter 1 puts the door on the living-room corner · A2 explains · iter 2 passes all 10 rules");

  // Iter 1 (red)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 1.9, w: 6.0, h: 2.4,
    fill: { color: "FEF2F2" }, line: { color: ORANGE, width: 1.5 }, rectRadius: 0.1,
  });
  s.addText("ITER 1  —  ✗ Z3 rejected", {
    x: 0.85, y: 2.0, w: 5.6, h: 0.4,
    fontSize: 12, bold: true, color: ORANGE, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "Gemini → ", options: { color: MUTED } },
    { text: "living spans x∈[5,40], door at x=40", options: { color: DARK, bold: true, fontFace: "Consolas", breakLine: true } },
    { text: "Z3: ", options: { color: MUTED } },
    { text: "door_in_living FAILS — door sits on the corner, not inset ≥ 2 ft", options: { color: ORANGE, fontFace: "Consolas" } },
  ], { x: 0.85, y: 2.5, w: 5.6, h: 1.7, fontSize: 12.5, fontFace: "Calibri", margin: 0 });

  // A2 feedback (navy)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.85, y: 1.9, w: 6.0, h: 2.4,
    fill: { color: NAVY }, line: { color: NAVY, width: 0 }, rectRadius: 0.1,
  });
  s.addText("A2 (Llama on Groq) writes:", {
    x: 7.1, y: 2.0, w: 5.6, h: 0.4,
    fontSize: 12, bold: true, color: ICE, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: '"Out of 10 interior rules, you missed 1 — fix and regenerate.', options: { color: WHITE, italic: true, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "* Widen the living room east past the door (or move the living/kitchen split right) so the door is ≥ 2 ft inside the living room — and shrink the kitchen to match so there is no gap.”",
      options: { color: WHITE, italic: true } },
  ], { x: 7.1, y: 2.5, w: 5.6, h: 1.7, fontSize: 11, fontFace: "Calibri", margin: 0 });

  // Iter 2 (green)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.6, y: 4.5, w: 12.2, h: 2.4,
    fill: { color: "F0FDF4" }, line: { color: GREEN, width: 1.5 }, rectRadius: 0.1,
  });
  s.addText("ITER 2  —  ✓ Z3 PASSES", {
    x: 0.85, y: 4.6, w: 11.6, h: 0.4,
    fontSize: 12, bold: true, color: GREEN, fontFace: "Calibri", charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "Gemini → ", options: { color: MUTED } },
    { text: "7 rooms tiling 3,770 sq ft (living 989 · kitchen 506 · 2 baths 276 · 3 bedrooms ~575)",
      options: { color: DARK, bold: true, fontFace: "Consolas", breakLine: true } },
    { text: "Z3: ", options: { color: MUTED } },
    { text: "ALL 10 interior rules satisfied", options: { color: GREEN, fontFace: "Consolas", bold: true, breakLine: true } },
    { text: "Converged to Gemini's own layout — the Z3 fallback was not needed.", options: { color: DARK, italic: true } },
  ], { x: 0.85, y: 5.1, w: 11.6, h: 1.7, fontSize: 14, fontFace: "Calibri", margin: 0 });

  addPageNumber(s);
}

// ============================================================================
// SLIDE 15 — Complete layout (visual)  [INTERIOR]
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Complete layout — exterior + interior",
             "Plot · protected tree · house shell · 7 Z3-verified rooms · door into the living room");

  s.addImage({ path: IMG("interior_result.png"),
               x: 2.7, y: 1.75, w: 7.9, h: 5.4, sizing: { type: "contain", w: 7.9, h: 5.4 } });

  addPageNumber(s);
}

// ============================================================================
// SLIDE 16 — Stats
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "The numbers",
             "Verified by Z3 — exterior footprint and interior floor plan");

  // 2x2 stat grid
  statCard(s, 0.6, 2.0, 6.0, 1.6, "6,420",       "PLOT AREA (sq ft)",                      NAVY);
  statCard(s, 6.85, 2.0, 6.0, 1.6, "4,060",       "Z3-PROVABLE MAX HOUSE (sq ft)",          NAVY);
  statCard(s, 0.6, 3.8, 6.0, 1.6, "3,770",       "OUR HOUSE (sq ft) — 92.9% of Z3 max",     GREEN);
  statCard(s, 6.85, 3.8, 6.0, 1.6, "58.7%",      "PLOT COVERAGE ACHIEVED",                  GREEN);

  // bottom row
  statCard(s, 0.6, 5.6, 4.0, 1.3, "2 + 2",       "ITERATIONS (exterior + interior)",        NAVY);
  statCard(s, 4.75, 5.6, 4.0, 1.3, "9 + 10",     "Z3 RULES (SBC + interior)",               NAVY);
  statCard(s, 8.9, 5.6, 3.95, 1.3, "7",          "ROOMS PLACED — ALL Z3-VERIFIED",          GREEN);

  addPageNumber(s, 11, 13);
}

// ============================================================================
// SLIDE 12 — Stack
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: WHITE };
  titleBlock(s, "Stack",
             "Assigned Claude + Kimi · Pivoted to Gemini + Groq mid-build (key availability)");

  const items = [
    { label: "Agent 1 — Generator",  v: "Gemini 2.5 Flash",
      d: "Exterior outline + interior room partition · thinking off · backoff" },
    { label: "Agent 2 — Verifier (judge)", v: "Z3 SMT solver",
      d: "Exterior: verify + optimize · Interior: verify + synthesize (tiling)" },
    { label: "Agent 2 — Verifier (explainer)", v: "Llama 3.3 70B (Groq)",
      d: "Rewrites Z3 violations as feedback · both phases · sub-second" },
    { label: "Drawing emitter",      v: "ezdxf 1.4",
      d: "dxf_full.py · plot + house + 7 rooms from verified numbers only" },
    { label: "Visualization",        v: "matplotlib",
      d: "Slide PNGs · plot + house + tree + labeled floor plan" },
    { label: "Orchestrator",         v: "Python 3.14 + python-dotenv",
      d: "loop_full.py · two-phase exterior → interior · Z3 fallback" },
  ];
  let y = 1.95;
  for (const it of items) {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y, w: 12.2, h: 0.78,
      fill: { color: "F8FAFC" }, line: { color: ICE, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y, w: 0.08, h: 0.78, fill: { color: NAVY }, line: { color: NAVY, width: 0 },
    });
    s.addText(it.label, {
      x: 0.85, y: y + 0.08, w: 4.0, h: 0.62,
      fontSize: 12, color: MUTED, fontFace: "Calibri", valign: "middle", margin: 0,
    });
    s.addText(it.v, {
      x: 4.85, y: y + 0.08, w: 3.6, h: 0.62,
      fontSize: 15, bold: true, color: NAVY, fontFace: "Cambria", valign: "middle", margin: 0,
    });
    s.addText(it.d, {
      x: 8.45, y: y + 0.08, w: 4.3, h: 0.62,
      fontSize: 11, italic: true, color: DARK, fontFace: "Calibri", valign: "middle", margin: 0,
    });
    y += 0.85;
  }

  addPageNumber(s, 12, 13);
}

// ============================================================================
// SLIDE 13 — Closing / takeaways
// ============================================================================
{
  const s = mkSlide();
  s.background = { color: NAVY };

  s.addText("Takeaways", {
    x: 0.8, y: 0.6, w: 12, h: 1.0,
    fontSize: 40, bold: true, color: WHITE, fontFace: "Cambria", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 1.55, w: 3.0, h: 0.04, fill: { color: ICE }, line: { color: ICE, width: 0 },
  });

  const takeaways = [
    {
      h: "Z3 is the judge — that's the whole point",
      d: "Using an LLM as a verifier collapses to two chatbots agreeing. A SMT solver gives reproducible, citable verdicts.",
    },
    {
      h: "One loop builds the whole house — exterior, then interior",
      d: "The same propose → prove → explain loop runs twice: 9 SBC rules for the shell, 10 room rules for the plan. Z3 even synthesizes a provable fallback layout.",
    },
    {
      h: "Make 'maximize area' a verifiable constraint, not a vibe",
      d: "Z3 Optimize computes the formal max once; the verifier enforces ≥ 90% of it. The brief's 'maximize' becomes something Z3 can reject.",
    },
    {
      h: "The prompt is part of the architecture",
      d: "Same model, same rules, +30 percentage points of coverage from rewriting A1's plot description from verbose to minimalist.",
    },
    {
      h: "Don't execute untrusted LLM code",
      d: "Magic comments + regex parser get the geometry without running anything. The .dxf is written from verified numbers only.",
    },
  ];
  let y = 1.75;
  for (const t of takeaways) {
    s.addText(t.h, {
      x: 0.8, y, w: 11.8, h: 0.45,
      fontSize: 16, bold: true, color: WHITE, fontFace: "Cambria", margin: 0,
    });
    s.addText(t.d, {
      x: 0.8, y: y + 0.46, w: 11.8, h: 0.55,
      fontSize: 12.5, color: ICE, fontFace: "Calibri", italic: false, margin: 0,
    });
    y += 1.02;
  }

  s.addText("Repo: /Users/ojas/ps1-house-layout/   ·   Ojas   ·   exterior + interior", {
    x: 0.8, y: SLIDE_H - 0.55, w: 12, h: 0.35,
    fontSize: 11, color: ICE, fontFace: "Calibri", italic: true, margin: 0,
  });
}

// ============================================================================
stampFooters();   // stamp "n / total" + footer on every content slide
pres.writeFile({ fileName: path.join(PROJ, "PS1_presentation.pptx") })
  .then(p => console.log("wrote", p))
  .catch(e => { console.error(e); process.exit(1); });
