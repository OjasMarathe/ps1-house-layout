/**
 * Layout Studio — full project presentation (pipeline, constraints, and the
 * problems-we-hit / how-we-fixed-them story). Midnight Executive palette.
 * Output: LayoutStudio_Presentation.pptx
 */
const path = require("path");
const PG = require("pptxgenjs");

const NAVY = "1E2761", ICE = "CADCFC", WHITE = "FFFFFF", RED = "B85042",
      GREEN = "2C5F2D", ORANGE = "C0392B", TEAL = "0E7490", MUTED = "64748B", DARK = "0F172A";
const SLIDE_W = 13.333, SLIDE_H = 7.5;
const PROJ = "/Users/ojas/ps1-house-layout";
const IMG = (n) => path.join(PROJ, "output/slides", n);

const pres = new PG();
pres.layout = "LAYOUT_WIDE";
pres.author = "Ojas Marathe";
pres.title = "Layout Studio — Neuro-Symbolic Floor Plans";

let page = 0; const footers = [];
function mk() { const s = pres.addSlide(); page++; s.__p = page; return s; }
function foot(s) { footers.push(s); }
function stamp() {
  for (const s of footers) {
    s.addText(`${s.__p} / ${page}`, { x: SLIDE_W - 1.2, y: SLIDE_H - 0.42, w: 0.9, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri", align: "right" });
    s.addText("Layout Studio · Ojas", { x: 0.5, y: SLIDE_H - 0.42, w: 6, h: 0.3,
      fontSize: 10, color: MUTED, fontFace: "Calibri" });
  }
}
function title(s, t, sub) {
  s.addText(t, { x: 0.6, y: 0.36, w: 12.1, h: 0.8, fontSize: 29, bold: true, color: NAVY, fontFace: "Cambria", margin: 0 });
  if (sub) s.addText(sub, { x: 0.6, y: 1.12, w: 12.1, h: 0.5, fontSize: 15, color: MUTED, italic: true, fontFace: "Calibri", margin: 0 });
}
function stat(s, x, y, w, h, v, l, accent = NAVY) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: WHITE }, line: { color: ICE, width: 1.5 } });
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h, fill: { color: accent }, line: { color: accent, width: 0 } });
  s.addText(v, { x: x + 0.22, y: y + 0.12, w: w - 0.36, h: h * 0.56, fontSize: 24, bold: true, color: accent, fontFace: "Cambria", valign: "middle", margin: 0 });
  s.addText(l, { x: x + 0.22, y: y + h * 0.56, w: w - 0.36, h: h * 0.4, fontSize: 10.5, color: MUTED, fontFace: "Calibri", margin: 0 });
}

// ===================================================== S1 Title
{
  const s = mk(); s.background = { color: NAVY };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.35, h: SLIDE_H, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addText("PS1 · ENGINEERING DRAWING", { x: 1.0, y: 1.2, w: 11, h: 0.5, fontSize: 20, color: ICE, fontFace: "Cambria", charSpacing: 10, margin: 0 });
  s.addText("Layout Studio", { x: 1.0, y: 1.85, w: 11.6, h: 1.2, fontSize: 52, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
  s.addText("Conversational, Z3-verified floor plans — an AI places the rooms, a solver proves every building rule",
    { x: 1.0, y: 3.25, w: 11.6, h: 0.9, fontSize: 19, italic: true, color: ICE, fontFace: "Calibri", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 1.0, y: 5.4, w: 4, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addText("Ojas Marathe", { x: 1.0, y: 5.5, w: 11, h: 0.5, fontSize: 15, color: ICE, fontFace: "Calibri", margin: 0 });
  s.addText("Z3 SMT · MILP (PuLP+CBC) · Gemini / Llama (Groq) · ezdxf · Streamlit",
    { x: 1.0, y: 5.95, w: 11.8, h: 0.5, fontSize: 13, color: WHITE, fontFace: "Consolas", margin: 0 });
}

// ===================================================== S2 The brief
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "The brief", "Generate a complete, code-compliant house drawing — and let a human steer it");
  s.addText([
    { text: "EXTERIOR", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "Draw the house outline on an L-shaped plot with a protected tree, respecting Seattle Building Code setbacks; maximise the footprint.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "INTERIOR", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "Subdivide it into 3 bedrooms + 2 bathrooms + 1 kitchen + 1 living room + circulation, satisfying IRC room-size and architectural rules.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "PRINCIPLE", options: { bold: true, color: TEAL, breakLine: true } },
    { text: "An LLM generates, the Z3 SMT solver is the deterministic judge, and the human stays in the loop — a conversational designer.", options: { color: DARK } },
  ], { x: 0.6, y: 2.0, w: 7.0, h: 4.6, fontSize: 14.5, fontFace: "Calibri", margin: 0 });
  s.addImage({ path: IMG("vibe_balanced.png"), x: 7.8, y: 1.85, w: 5.0, h: 5.0, sizing: { type: "contain", w: 5.0, h: 5.0 } });
  foot(s);
}

// ===================================================== S3 System overview / pipeline
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "The pipeline — two phases, one principle", "Generator proposes · Z3 proves · human/LLM explains");
  const boxY = 2.0, boxH = 3.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: boxY, w: 5.7, h: boxH, fill: { color: "F8FAFC" }, line: { color: NAVY, width: 1.5 }, rectRadius: 0.12 });
  s.addText("PHASE 1 — EXTERIOR", { x: 0.85, y: boxY + 0.15, w: 5.2, h: 0.4, fontSize: 13, bold: true, color: NAVY, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "Z3 Optimize → provable max-area footprint", options: { bullet: true, breakLine: true } },
    { text: "Gemini draws the outline; parser extracts coords", options: { bullet: true, breakLine: true } },
    { text: "Z3 verifies 9 SBC rules", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "Llama (Groq) writes feedback → loop", options: { bullet: true } },
  ], { x: 0.95, y: boxY + 0.6, w: 5.1, h: 1.9, fontSize: 12.5, color: DARK, fontFace: "Calibri", margin: 0 });
  s.addText("→  verified footprint + door", { x: 0.85, y: boxY + 2.55, w: 5.4, h: 0.45, fontSize: 12.5, italic: true, bold: true, color: GREEN, fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.LINE, { x: 6.35, y: boxY + boxH / 2, w: 0.6, h: 0, line: { color: NAVY, width: 2.5, endArrowType: "triangle" } });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.05, y: boxY, w: 5.7, h: boxH, fill: { color: "F0FDFA" }, line: { color: TEAL, width: 1.5 }, rectRadius: 0.12 });
  s.addText("PHASE 2 — INTERIOR", { x: 7.3, y: boxY + 0.15, w: 5.2, h: 0.4, fontSize: 13, bold: true, color: TEAL, charSpacing: 3, fontFace: "Calibri", margin: 0 });
  s.addText([
    { text: "Seed: tiled vibe template (instant) OR MILP/CBC", options: { bullet: true, breakLine: true } },
    { text: "Conversational edits: chips + free-text (LLM)", options: { bullet: true, breakLine: true } },
    { text: "Z3 verifies the interior rule set", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "Only VALID layouts are shown (else revert)", options: { bullet: true } },
  ], { x: 7.4, y: boxY + 0.6, w: 5.1, h: 1.9, fontSize: 12.5, color: DARK, fontFace: "Calibri", margin: 0 });
  s.addText("→  complete floor plan + layered .dxf", { x: 7.3, y: boxY + 2.55, w: 5.4, h: 0.45, fontSize: 12.5, italic: true, bold: true, color: GREEN, fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.5, w: 12.2, h: 1.2, fill: { color: ICE }, line: { color: NAVY, width: 1 }, rectRadius: 0.1 });
  s.addText([
    { text: "Never executes LLM code: ", options: { bold: true, color: NAVY } },
    { text: "geometry comes from parsed “magic comments”, and the .dxf is rendered deterministically from Z3-verified numbers.", options: { color: DARK } },
  ], { x: 0.9, y: 5.6, w: 11.6, h: 1.0, fontSize: 13.5, fontFace: "Calibri", valign: "middle", margin: 0 });
  foot(s);
}

// ===================================================== S4 Exterior constraints
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Exterior — Z3 turns “maximise area” into a hard rule", "9 Seattle Building Code constraints, plus a provable maximum");
  stat(s, 0.6, 2.0, 6.0, 1.4, "6,420", "PLOT AREA (sq ft, L-shaped)", NAVY);
  stat(s, 6.85, 2.0, 6.0, 1.4, "4,060", "Z3-PROVABLE MAX HOUSE (70×58 ft)", NAVY);
  stat(s, 0.6, 3.6, 6.0, 1.4, "≥ 90%", "OF MAX ENFORCED AS A HARD RULE", GREEN);
  stat(s, 6.85, 3.6, 6.0, 1.4, "2", "ITERATIONS TO CONVERGE", GREEN);
  s.addText("Constraints: front/rear/side setbacks · tree buffer (cannot be removed) · door + parking on the same entry side (fire egress) · minimum footprint · all corners inside the L-shape · footprint ≥ 90% of the Z3-computed maximum.",
    { x: 0.6, y: 5.3, w: 12.2, h: 1.3, fontSize: 13.5, color: DARK, fontFace: "Calibri", margin: 0 });
  foot(s);
}

// ===================================================== S5 Interior constraints
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Interior — the rules Z3 checks", "IRC room sizing + architectural spatial rules");
  const data = [[
    { text: "Group", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
    { text: "Rule", options: { bold: true, color: WHITE, fill: { color: NAVY } } }],
    ["Room areas", "living / kitchen / bedrooms ≥ 70 sq ft · bathrooms ≥ 25 sq ft (IRC R304)"],
    ["Dimensions", "habitable side ≥ 7 ft · bath side 5–15 ft (no slivers, no slabs)"],
    ["Containment", "every room inside the footprint · no two rooms overlap"],
    ["Door / egress", "the front door opens into the living room on the south wall"],
    ["Circulation", "≥ 4 ft corridor; every room reachable (connected)"],
    ["Coverage", "rooms tile the footprint — only thin halls left over"],
  ];
  s.addTable(data, { x: 0.6, y: 2.0, w: 12.2, h: 3.7, fontSize: 13, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE }, rowH: 0.55, colW: [2.6, 9.6], valign: "middle" });
  s.addText("The same verifier runs in a strict mode (ensuite/sanitation arrangement) and a freeform mode (user-driven layouts) — the geometry rules always hold.",
    { x: 0.6, y: 6.0, w: 12.2, h: 0.6, fontSize: 12.5, italic: true, color: MUTED, fontFace: "Calibri", margin: 0 });
  foot(s);
}

// ===================================================== S6 How we generate
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "How the interior is generated — three tools", "Each room is verified by Z3 no matter who proposes it");
  const cards = [
    ["Templates", "TEAL", "Hand-designed tiled layouts per “vibe”. Instant, always valid. The seed + the deterministic quick-changes."],
    ["MILP / CBC", "NAVY", "Cutting-plane solver places rooms with big-M non-overlap. Generate-and-guarantee, the approach sir suggested."],
    ["LLM (conversational)", "GREEN", "Gemini / Llama reads a natural-language description and places the rooms; Z3 confirms; loop on failure."],
  ];
  const cmap = { TEAL, NAVY, GREEN };
  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.1, w: 3.85, h: 3.7, fill: { color: "F8FAFC" }, line: { color: cmap[c[1]], width: 1.5 }, rectRadius: 0.1 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.1, w: 3.85, h: 0.12, fill: { color: cmap[c[1]] }, line: { color: cmap[c[1]], width: 0 } });
    s.addText(c[0], { x: x + 0.25, y: 2.4, w: 3.4, h: 0.6, fontSize: 18, bold: true, color: cmap[c[1]], fontFace: "Cambria", margin: 0 });
    s.addText(c[2], { x: x + 0.25, y: 3.05, w: 3.4, h: 2.6, fontSize: 13.5, color: DARK, fontFace: "Calibri", margin: 0 });
  });
  s.addText("Quick-changes use Templates (deterministic). Free-text uses the LLM. Both end on a Z3-verified plan.",
    { x: 0.6, y: 6.1, w: 12.2, h: 0.5, fontSize: 13, italic: true, color: MUTED, fontFace: "Calibri", margin: 0 });
  foot(s);
}

// ===================================================== S7 The app (HITL)
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "The app — a conversational design studio (Streamlit)", "“ChatGPT for floor plans”: describe it, the studio draws & proves it");
  s.addImage({ path: IMG("vibe_entertainer.png"), x: 0.5, y: 1.9, w: 5.1, h: 4.9, sizing: { type: "contain", w: 5.1, h: 4.9 } });
  s.addText([
    { text: "Pick a vibe", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "Family / Entertainer / Work-from-home / Balanced — an instant tiled starting plan.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Quick changes", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "“Bigger bedrooms / kitchen / bathrooms…” — instant, always valid.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Describe in words", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "“bedrooms in the three corners, kitchen between the top two” — the LLM lays it out; Z3 checks it.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Live Z3 badge + one-click .dxf download.", options: { italic: true, color: TEAL } },
  ], { x: 6.0, y: 1.95, w: 6.8, h: 4.9, fontSize: 14, fontFace: "Calibri", margin: 0 });
  foot(s);
}

// ===================================================== S8 Findings overview (problems & fixes)
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Findings — the problems we hit, and the fixes", "Most came out of live testing in the studio");
  const data = [[
    { text: "Problem observed", options: { bold: true, color: WHITE, fill: { color: ORANGE } } },
    { text: "Root cause", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
    { text: "Fix", options: { bold: true, color: WHITE, fill: { color: GREEN } } }],
    ["Tiny bedrooms, enormous living/kitchen", "fixed band dumped all depth into the public zone", "tunable room sizes + balanced templates"],
    ["~35% left empty as one big “corridor” block", "rooms floated; leftover dumped as one rectangle", "tiling templates (100%) + 4-ft-min halls"],
    ["Bedrooms too long & skinny (16×29)", "bedrooms filled the full band depth", "square-ish templates (aspect ≤ 1.3)"],
    ["All 4 vibes looked identical", "same layout with tiny size nudges", "4 genuinely distinct tiled templates"],
    ["Chat left broken plans (“✗ connected”)", "LLM broke a rule; app showed the best invalid try", "commit only if valid (else revert) + deterministic chips"],
    ["Gemini quota (20/day) ran out mid-demo", "free-tier daily cap", "switched generator to Llama 3.3 on Groq"],
  ];
  s.addTable(data, { x: 0.5, y: 1.95, w: 12.35, h: 4.7, fontSize: 11.5, fontFace: "Calibri", color: DARK,
    border: { pt: 0.5, color: ICE }, rowH: 0.62, colW: [4.35, 4.3, 3.7], valign: "middle" });
  foot(s);
}

// ===================================================== S9 Before/After 1 (balance + empty)
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Fix in pictures (1) — balance & wasted space", "No SBC reason for the empty space — it was a design choice, now fixed");
  s.addImage({ path: IMG("before_block.png"), x: 0.5, y: 1.95, w: 5.0, h: 4.6, sizing: { type: "contain", w: 5.0, h: 4.6 } });
  s.addText("BEFORE — 85% rooms, a big block of “corridor”", { x: 0.5, y: 6.55, w: 5.0, h: 0.4, fontSize: 12, bold: true, color: ORANGE, align: "center", fontFace: "Calibri", margin: 0 });
  s.addShape(pres.shapes.LINE, { x: 6.0, y: 4.2, w: 1.1, h: 0, line: { color: NAVY, width: 2.5, endArrowType: "triangle" } });
  s.addImage({ path: IMG("vibe_family.png"), x: 7.6, y: 1.95, w: 5.0, h: 4.6, sizing: { type: "contain", w: 5.0, h: 4.6 } });
  s.addText("AFTER — 100% tiled, thin hall, big square-ish rooms", { x: 7.6, y: 6.55, w: 5.0, h: 0.4, fontSize: 12, bold: true, color: GREEN, align: "center", fontFace: "Calibri", margin: 0 });
  foot(s);
}

// ===================================================== S10 The four vibes
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Fix in pictures (2) — four visibly different vibes", "Square-ish bedrooms · no two bedrooms adjacent · all Z3-verified");
  const figs = [["vibe_balanced.png", "Balanced"], ["vibe_family.png", "Family — big bedrooms"],
                ["vibe_entertainer.png", "Entertainer — big living"], ["vibe_wfh.png", "Work-from-home — big study"]];
  figs.forEach((f, i) => {
    const x = 0.5 + i * 3.16;
    s.addImage({ path: IMG(f[0]), x, y: 1.95, w: 3.0, h: 3.9, sizing: { type: "contain", w: 3.0, h: 3.9 } });
    s.addText(f[1], { x, y: 5.95, w: 3.0, h: 0.6, fontSize: 11.5, bold: true, color: NAVY, align: "center", fontFace: "Calibri", margin: 0 });
  });
  foot(s);
}

// ===================================================== S11 Reliability
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Reliability — the studio never shows a broken plan", "Two changes that fixed the “it does it then says error” problem");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 2.0, w: 5.9, h: 4.4, fill: { color: "F0FDFA" }, line: { color: TEAL, width: 1.5 }, rectRadius: 0.1 });
  s.addText("Quick changes → deterministic", { x: 0.85, y: 2.2, w: 5.4, h: 0.5, fontSize: 16, bold: true, color: TEAL, fontFace: "Cambria", margin: 0 });
  s.addText([
    { text: "Buttons adjust the layout’s cut positions with built-in clamping.", options: { bullet: true, breakLine: true } },
    { text: "Cannot break a rule. Cannot be declined.", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "Instant — no model call, no waiting.", options: { bullet: true } },
  ], { x: 0.95, y: 2.85, w: 5.4, h: 3.3, fontSize: 14, color: DARK, fontFace: "Calibri", margin: 0 });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 2.0, w: 5.9, h: 4.4, fill: { color: "F8FAFC" }, line: { color: NAVY, width: 1.5 }, rectRadius: 0.1 });
  s.addText("Free-text → commit only if valid", { x: 7.1, y: 2.2, w: 5.4, h: 0.5, fontSize: 16, bold: true, color: NAVY, fontFace: "Cambria", margin: 0 });
  s.addText([
    { text: "LLM proposes; Z3 checks; up to 4 retries with feedback.", options: { bullet: true, breakLine: true } },
    { text: "If still invalid, keep the current plan and say which rule blocked it.", options: { bullet: true, breakLine: true, bold: true, color: NAVY } },
    { text: "You never see an overlapping or disconnected layout.", options: { bullet: true } },
  ], { x: 7.2, y: 2.85, w: 5.4, h: 3.3, fontSize: 14, color: DARK, fontFace: "Calibri", margin: 0 });
  foot(s);
}

// ===================================================== S12 Observations / learnings
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Key observations", "What the build taught us");
  s.addText([
    { text: "LLMs are great at intent, weak at constraint-preserving edits. ", options: { bold: true, color: NAVY } },
    { text: "Asking “make the kitchen bigger” often broke another rule. We route simple edits to a deterministic solver and reserve the LLM for genuine spatial descriptions.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Z3 as an always-on judge is the safety net. ", options: { bold: true, color: NAVY } },
    { text: "Because every layout is independently verified, we can swap generators (Gemini ↔ Groq ↔ MILP ↔ templates) freely and still guarantee correctness.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Geometry has hard trade-offs. ", options: { bold: true, color: NAVY } },
    { text: "On a 58-ft-deep plot, perfectly square bedrooms + full tiling + a 15-ft bathroom cap can’t all hold — “square-ish + fully tiled” is the sweet spot.", options: { color: DARK, breakLine: true } },
    { text: " ", options: { breakLine: true } },
    { text: "Human-in-the-loop ≠ free-for-all. ", options: { bold: true, color: NAVY } },
    { text: "The human sets comfort/intent; the solver owns code-compliance. That division is what makes it usable.", options: { color: DARK } },
  ], { x: 0.6, y: 2.0, w: 12.2, h: 4.7, fontSize: 14.5, fontFace: "Calibri", margin: 0 });
  foot(s);
}

// ===================================================== S13 Stack
{
  const s = mk(); s.background = { color: WHITE };
  title(s, "Stack", "Each layout is verified before it’s ever shown");
  const items = [
    ["Verifier (the judge)", "Z3 SMT solver", "exterior 9 rules · interior room/spatial rules"],
    ["Generators", "Templates · MILP (PuLP+CBC) · LLM", "tiled seeds · cutting-plane solve · conversational"],
    ["LLMs", "Gemini 2.5 Flash · Llama 3.3 70B (Groq)", "swappable; Groq default after quota limits"],
    ["Drawing", "ezdxf · matplotlib", "layered .dxf + labeled PNGs, from verified numbers"],
    ["App", "Streamlit (Python 3.14)", "conversational human-in-the-loop studio"],
  ];
  let y = 2.0;
  for (const it of items) {
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 12.2, h: 0.85, fill: { color: "F8FAFC" }, line: { color: ICE, width: 1 } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 0.08, h: 0.85, fill: { color: NAVY }, line: { color: NAVY, width: 0 } });
    s.addText(it[0], { x: 0.85, y: y + 0.1, w: 3.5, h: 0.66, fontSize: 12, color: MUTED, fontFace: "Calibri", valign: "middle", margin: 0 });
    s.addText(it[1], { x: 4.45, y: y + 0.1, w: 4.3, h: 0.66, fontSize: 13.5, bold: true, color: NAVY, fontFace: "Cambria", valign: "middle", margin: 0 });
    s.addText(it[2], { x: 8.8, y: y + 0.1, w: 3.95, h: 0.66, fontSize: 11, italic: true, color: DARK, fontFace: "Calibri", valign: "middle", margin: 0 });
    y += 0.95;
  }
  foot(s);
}

// ===================================================== S14 Takeaways
{
  const s = mk(); s.background = { color: NAVY };
  s.addText("Takeaways", { x: 0.8, y: 0.55, w: 12, h: 1.0, fontSize: 40, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.5, w: 3.0, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  const tk = [
    ["Z3 is the judge — that’s the whole point", "Reproducible, citable verdicts; lets us swap any generator and still guarantee a code-valid plan."],
    ["Generate-and-guarantee + human-in-the-loop", "MILP/templates produce valid plans; the human steers comfort via a conversation, not a config file."],
    ["We found and fixed real problems", "Balance, wasted space, long bedrooms, look-alike vibes, broken edits, and an API quota — all resolved."],
    ["Right tool for each edit", "Deterministic for simple changes, LLM for descriptions — reliable AND expressive."],
  ];
  let y = 2.0;
  for (const t of tk) {
    s.addText(t[0], { x: 0.8, y, w: 11.8, h: 0.5, fontSize: 17, bold: true, color: WHITE, fontFace: "Cambria", margin: 0 });
    s.addText(t[1], { x: 0.8, y: y + 0.5, w: 11.8, h: 0.6, fontSize: 13, color: ICE, fontFace: "Calibri", margin: 0 });
    y += 1.2;
  }
  s.addText("Repo: /Users/ojas/ps1-house-layout/   ·   run:  streamlit run app.py", { x: 0.8, y: SLIDE_H - 0.5, w: 12, h: 0.35, fontSize: 11, color: ICE, italic: true, fontFace: "Calibri", margin: 0 });
}

stamp();
pres.writeFile({ fileName: path.join(PROJ, "LayoutStudio_Presentation.pptx") })
  .then(p => console.log("wrote", p))
  .catch(e => { console.error(e); process.exit(1); });
