/**
 * Builds Problem2_Documentation_Ours.docx — our two-agent neuro-symbolic CAD
 * system with a MILP / cutting-plane interior generator, mirroring the
 * reference write-up's structure but documenting our approach and real results.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, ImageRun, PageNumber, Header, Footer,
} = require("docx");

const PROJ = "/Users/ojas/ps1-house-layout";
const NAVY = "1E2761";
const TEAL = "0E7490";
const INK = "0F172A";
const GREY = "64748B";
const HDR = "1E2761";   // table header fill
const ZEBRA = "F1F5F9"; // zebra row fill
const CONTENT_W = 9360; // US Letter, 1" margins

// ---------- helpers ----------------------------------------------------------
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text: t, color: NAVY, bold: true })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text: t, color: TEAL, bold: true })] });
const P = (runs) => new Paragraph({
  spacing: { after: 120, line: 276 },
  children: (Array.isArray(runs) ? runs : [new TextRun({ text: runs, color: INK })]) });
const BUL = (t, bold) => new Paragraph({
  numbering: { reference: "bul", level: 0 }, spacing: { after: 40 },
  children: [new TextRun({ text: t, color: INK, bold: !!bold })] });
const NUM = (t) => new Paragraph({
  numbering: { reference: "steps", level: 0 }, spacing: { after: 40 },
  children: [new TextRun({ text: t, color: INK })] });

const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: "CBD5E1" };
const borders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };

function cell(text, w, { head = false, bold = false, fill } = {}) {
  const f = head ? HDR : fill;
  return new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    shading: f ? { fill: f, type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ children: [new TextRun({
      text: text, bold: head || bold, color: head ? "FFFFFF" : INK, size: 19 })] })],
  });
}

function table(headers, rows, widths) {
  const head = new TableRow({ tableHeader: true,
    children: headers.map((h, i) => cell(h, widths[i], { head: true })) });
  const body = rows.map((r, ri) => new TableRow({
    children: r.map((c, i) => cell(String(c), widths[i],
      { fill: ri % 2 ? ZEBRA : undefined })) }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths, rows: [head, ...body] });
}
const SP = () => new Paragraph({ spacing: { after: 80 }, children: [] });

// ---------- document ---------------------------------------------------------
const children = [];

// Title block
children.push(new Paragraph({ spacing: { before: 240, after: 40 },
  children: [new TextRun({ text: "Problem 2", color: NAVY, bold: true, size: 56 })] }));
children.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({
  text: "Two-Agent Neuro-Symbolic CAD Layout Generation with a MILP / Cutting-Plane Interior Solver",
  color: TEAL, bold: true, size: 26 })] }));
children.push(new Paragraph({ spacing: { after: 240 }, children: [new TextRun({
  text: "Ojas Marathe   |   7 June 2026", color: GREY, size: 20 })] }));

// 1. Problem Statement
children.push(H1("1. Problem Statement"));
children.push(P("Building on Problem 1, which verified the outer boundary of a house on an L-shaped plot, this assignment extends the two-agent system to generate and formally verify the complete interior. The system must produce a full residential floor plan — 3 bedrooms, 2 bathrooms, 1 kitchen, 1 living room and a connecting corridor — and prove that the layout satisfies residential-code room-size rules (IRC R304/R305) together with a set of architectural spatial rules (ensuite bathrooms, sanitation separation, circulation)."));
children.push(P("The distinguishing goal of our implementation is the generation strategy. Rather than have the LLM guess a layout and then repair it against the checker (verify-and-fix), the interior is produced by a Mixed-Integer Linear Programming solver using a cutting-plane algorithm (generate-and-guarantee), as suggested in the project guidance. The same Z3 SMT solver remains the independent judge of the result."));

// 2. System Overview
children.push(H1("2. System Overview"));
children.push(P("The system is a fully automated two-phase pipeline. Phase 1 verifies the exterior shell; Phase 2 lays out the interior. Both phases share the same neuro-symbolic principle: a generator proposes geometry, the Z3 SMT solver is the deterministic judge, and an LLM turns any failed constraints into actionable feedback."));
children.push(H2("Pipeline steps"));
[
  "Z3 Optimize computes the theoretical maximum-area legal house for the plot and setbacks (a provable upper bound).",
  "Agent 1 (Gemini 2.5 Flash) generates the outer-boundary geometry; a regex/AST-free magic-comment parser extracts the coordinates without executing the generated code.",
  "The Z3 exterior verifier checks 9 Seattle Building Code constraints (setbacks, tree buffer, door egress, and footprint area >= 90% of the Z3 maximum) and returns SAT or a violation list.",
  "If UNSAT, Agent 2 (Llama 3.3 70B on Groq) writes specific fix instructions and the exterior loop repeats (max 5 iterations).",
  "Once the footprint is SAT, Phase 2 begins. The MILP / cutting-plane solver (PuLP + CBC) generates the 8-room interior directly, guaranteed to satisfy the constraints by construction.",
  "The Z3 interior verifier independently checks the full interior constraint set (25 code/spatial rules plus extras) and confirms SAT with a per-constraint breakdown.",
  "A deterministic emitter writes a layered .dxf (plot, tree, house, rooms, corridor, windows, doors) from the verified numbers; an optional Gemini verify-and-fix loop (INTERIOR_MODE=llm) is available with the MILP layout as the guaranteed fallback.",
].forEach((s) => children.push(NUM(s)));

// 3. Exterior stage
children.push(H1("3. Exterior Stage (Phase 1)"));
children.push(P("The exterior stage turns the brief's vague 'maximize area' into a verifiable number. Z3 Optimize declares the four house corners as symbolic real variables, adds every setback constraint, and maximizes the footprint, yielding a provable maximum of 4,060 sq ft. The verifier then enforces a hard rule that the footprint must reach at least 90% of this maximum (3,654 sq ft), so the generator is forced to push to the legal limit rather than play safe."));
children.push(P([
  new TextRun({ text: "Result: ", bold: true, color: INK }),
  new TextRun({ text: "the loop converges in 2 iterations to a 63 x 58 ft footprint = 3,654 sq ft (90% of the Z3 maximum), with the main door on the south entry wall. This verified footprint is handed to Phase 2.", color: INK }),
]));

// 4. Interior Layout Design Approach
children.push(H1("4. Interior Layout Design Approach"));
children.push(H2("4.1 Generate-and-guarantee instead of verify-and-fix"));
children.push(P("A cutting-plane algorithm is an optimisation technique from Mixed-Integer Linear Programming. The solver starts from the LP relaxation of the layout problem, and whenever the relaxed optimum is geometrically infeasible (e.g. two rooms partially overlapping) it adds a linear cut that removes that solution from the search space, repeating until only valid layouts remain. CBC (the solver bundled with PuLP) performs exactly this branch-and-cut process. The advantage over verify-and-fix is that the solver returns a layout that is mathematically guaranteed to satisfy the encoded constraints on the first solve, with no LLM iteration required."));
children.push(H2("4.2 The three-band structure"));
children.push(P("We model the interior as three horizontal bands that tile the footprint top to bottom. Fixing each band's height keeps every room area linear in the cut positions (so the model stays in the linear fragment CBC can solve), and the band ordering encodes the spatial rules structurally, so the optimum is always code-valid:"));
children.push(table(
  ["Band (south to north)", "Contents", "Purpose"],
  [
    ["Public band", "Living | Kitchen", "Living on the south wall over the door; kitchen flush beside it"],
    ["Corridor band (4 ft)", "full-width hallway", "Separates public from private; connects every room"],
    ["Private band (15 ft)", "Bath1 | Bed1 | Bed3 | Bed2 | Bath2", "Ensuite baths flank only their own bedroom; Bed3 keeps the two baths apart"],
  ], [2600, 3360, 3400]));
children.push(SP());
children.push(P("Because the corridor lies between the public and private bands, no bathroom can ever touch the kitchen (sanitation). Because Bedroom 3 sits between the two ensuite pairs, the two bathrooms are never adjacent. The bathroom height equals the 15 ft maximum-dimension cap, so baths fill the private band without leaving a gap, giving ~100% coverage."));
children.push(H2("4.3 Spatial rules encoded"));
[
  "Living room nearest the south entry, touching the south wall, with the front door opening into it.",
  "Kitchen directly adjacent to the living room (open plan, no corridor between).",
  "Each bathroom is ensuite: it shares a wall (>= 4 ft) with its own bedroom and is smaller in area than that bedroom.",
  "A bathroom must never share a wall with the kitchen (sanitation), and the two bathrooms must never be adjacent to each other.",
  "Bathrooms are capped at 15 ft per side so the solver cannot emit an absurd slab-shaped bath.",
  "Each bedroom is drawn with 2 windows on its exterior wall(s); a 4-ft corridor provides circulation and full connectivity.",
].forEach((s) => children.push(BUL(s)));
children.push(H2("4.4 Layer-based drawing"));
children.push(P("Each room type is emitted on its own .dxf layer (ROOM_LIVING, ROOM_KITCHEN, CORRIDOR, ROOM_BEDROOM, ROOM_BATH, DOOR, LABELS) for clarity and independent inspection. The .dxf is rendered deterministically from the Z3-verified coordinates, never by executing generated code."));

// 5. MILP generator
children.push(H1("5. The MILP / Cutting-Plane Generator"));
children.push(P("The generator (interior_milp.py) builds a PuLP model and solves it with CBC. Everything is linear so CBC's cutting planes apply."));
children.push(H2("5.1 Model"));
children.push(table(
  ["Component", "Formulation"],
  [
    ["Decision variables", "Room widths / band cut positions (continuous); per-pair non-overlap selectors (binary)"],
    ["Containment", "Every room inside the footprint"],
    ["Non-overlap", "Big-M disjunction per pair: at least one of {i left / right / below / above j}"],
    ["Tiling", "Bands span the full width and height -> ~100% coverage, exact areas"],
    ["Door / egress", "Living spans the door, inset >= 2 ft from its side walls, on the south wall"],
    ["Ensuite / sanitation", "Band ordering: Bath_i flanks only Bed_i; corridor isolates baths from kitchen"],
    ["Objective", "Maximise the smallest bedroom width (balanced bedrooms); keep the kitchen generous"],
  ], [2600, 6760]));
children.push(SP());
children.push(P("The big-M non-overlap binaries are what make this a true MILP solved by branch-and-cut: CBC adds Gomory, clique and cover cuts to tighten the relaxation. The band structure then guides the optimum to a complete, code-valid tiling."));

// 6. Z3 verification framework
children.push(H1("6. Z3 Interior Verification Framework"));
children.push(H2("6.1 Constraint sources"));
children.push(BUL("IRC Section R304/R305 governs room area and minimum-dimension requirements."));
children.push(BUL("Architectural meeting rules govern adjacency, ensuite attachment and circulation."));
children.push(H2("6.2 The interior constraint set"));
children.push(P("The verifier (interior_verifier_z3.py) encodes the same 25-rule reference set, grouped below, plus four extra structural rules. Scalar comparisons (areas, side lengths, shared-wall lengths) are evaluated through Z3; pure geometry (overlap, adjacency-graph connectivity) is computed directly."));

children.push(H2("Group 1 — Room area minimums (IRC R304)"));
children.push(table(["Constraint", "Rule", "Source"], [
  ["Living / Kitchen area", ">= 70 sq ft", "IRC R304 habitable minimum"],
  ["Bedroom 1 / 2 / 3 area", ">= 70 sq ft", "IRC R304"],
  ["Bathroom 1 / 2 area", ">= 25 sq ft", "5x5 fixture clearance"],
  ["Corridor area", ">= 16 sq ft", "circulation"],
], [3400, 2960, 3000]));
children.push(SP());
children.push(H2("Group 2 — Minimum dimension (IRC R304)"));
children.push(table(["Constraint", "Rule", "Source"], [
  ["Living / Kitchen / Bedroom side", ">= 7 ft", "IRC R304 (no dimension < 7 ft)"],
  ["Bathroom side", ">= 5 ft", "fixture clearance"],
  ["Corridor width", ">= 4 ft", "IRC R311 hallway"],
], [3400, 2960, 3000]));
children.push(SP());
children.push(H2("Group 3 — Maximum dimension (added after testing)"));
children.push(table(["Constraint", "Rule", "Reason"], [
  ["Bathroom 1 / 2 max side", "<= 15 ft", "Prevents an absurd 33x5 bath that passes the 5 ft minimum"],
], [3400, 2300, 3660]));
children.push(SP());
children.push(H2("Group 4 — Bathroom vs bedroom size"));
children.push(table(["Constraint", "Rule"], [
  ["Bath 1 area < Bed 1 area", "ensuite must be smaller than its bedroom"],
  ["Bath 2 area < Bed 2 area", "ensuite must be smaller than its bedroom"],
], [4000, 5360]));
children.push(SP());
children.push(H2("Group 5 — Bathroom adjacency (sanitation)"));
children.push(table(["Constraint", "Rule"], [
  ["Bath 1 not adjacent to kitchen", "no shared wall (toilet wall must not abut food prep)"],
  ["Bath 2 not adjacent to kitchen", "no shared wall"],
  ["Bath 1 not adjacent to Bath 2", "no shared wall"],
], [4000, 5360]));
children.push(SP());
children.push(H2("Group 6 — Ensuite attachment"));
children.push(table(["Constraint", "Rule"], [
  ["Bath 1 shares a wall with Bed 1", "private access >= 4 ft, without using the corridor"],
  ["Bath 2 shares a wall with Bed 2", "each bath serves a distinct bedroom"],
], [4000, 5360]));
children.push(SP());
children.push(H2("Group 7 — Spatial and coverage"));
children.push(table(["Constraint", "Rule"], [
  ["Living near south wall", "living south edge within 2 ft of the house south wall"],
  ["All rooms inside house", "containment for every room"],
  ["Coverage", "total room area within +/- 5% of the footprint"],
], [4000, 5360]));
children.push(SP());
children.push(H2("Group 8 — Additional structural rules (ours)"));
children.push(table(["Constraint", "Rule"], [
  ["Door opens into living", "front door on the living-room south wall, inset >= 2 ft"],
  ["Kitchen adjacent to living", "shared wall >= 2.5 ft (open plan)"],
  ["Full connectivity", "every room reachable from every other through a >= 2.5 ft doorway"],
  ["Room count", "exactly 1 living + 1 kitchen + 1 corridor + 3 bedrooms + 2 bathrooms"],
], [4000, 5360]));
children.push(SP());
children.push(H2("6.3 How Z3 verifies"));
children.push(P("Each scalar rule is encoded as a Z3 constraint of the form (measured < required) and checked for satisfiability; if SAT, the rule is violated and a precise fix message is produced. An empty violation list means the floor plan is SAT against the full set. Because the MILP already guarantees the constraints, the verifier confirms SAT on the first interior solve."));

// 7. Results
children.push(H1("7. Results"));
children.push(H2("7.1 Exterior (Phase 1)"));
children.push(table(["Metric", "Value"], [
  ["Plot area", "6,420 sq ft (L-shaped)"],
  ["Z3-provable maximum house", "4,060 sq ft (70 x 58 ft)"],
  ["Coverage threshold", ">= 90% of max = 3,654 sq ft"],
  ["Converged footprint", "63 x 58 ft = 3,654 sq ft (90% of max)"],
  ["Iterations to SAT", "2"],
], [4000, 5360]));
children.push(SP());
children.push(H2("7.2 Interior (Phase 2 — MILP / CBC)"));
children.push(P([
  new TextRun({ text: "CBC status: Optimal   |   8 rooms   |   100% coverage   |   Z3: 25/25 rules + 4 extras satisfied, 0 violations.", color: INK, bold: true }),
]));
children.push(table(["Room", "W x H (ft)", "Area (sq ft)"], [
  ["Living", "37 x 39", "1,443"],
  ["Kitchen", "26 x 39", "1,014"],
  ["Corridor", "63 x 4", "252"],
  ["Bath 1 (ensuite Bed 1)", "6 x 15", "90"],
  ["Bedroom 1", "17 x 15", "255"],
  ["Bedroom 3", "17 x 15", "255"],
  ["Bedroom 2", "17 x 15", "255"],
  ["Bath 2 (ensuite Bed 2)", "6 x 15", "90"],
  ["TOTAL", "63 x 58", "3,654 (100%)"],
], [3400, 2960, 3000]));
children.push(SP());
// figure
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
  children: [new ImageRun({ type: "png",
    data: fs.readFileSync(path.join(PROJ, "output/slides/milp_result.png")),
    transformation: { width: 430, height: 454 },
    altText: { title: "MILP interior", name: "milp", description: "MILP-generated interior layout" } })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [new TextRun({ text: "Figure 1 — MILP / cutting-plane interior on the verified footprint: corridor, ensuite bathrooms, bedroom windows; Z3-verified.", italics: true, color: GREY, size: 18 })] }));
children.push(H2("7.3 Verifier self-tests"));
children.push(P("The interior verifier is exercised by 8 smoke cases (a valid MILP layout that must pass, plus mutations that must each trip the right rule: coverage gap, overlap, wrong room count, door-not-in-living, oversized bath, broken ensuite, bath-abuts-kitchen). All 8 pass. The exterior verifier passes its 6 cases."));

// 8. Comparison
children.push(H1("8. Comparison: Generate-and-Guarantee vs Verify-and-Fix"));
children.push(table(["Aspect", "Verify-and-fix (LLM + Z3)", "Generate-and-guarantee (MILP + Z3)"], [
  ["Who places the rooms", "Gemini guesses, Z3 checks", "CBC solves, Z3 confirms"],
  ["Constraint satisfaction", "after 1+ feedback rounds", "guaranteed on first solve"],
  ["Determinism", "LLM output varies", "solver output is reproducible"],
  ["Role of Z3", "judge + feedback source", "independent confirmation"],
], [2400, 3480, 3480]));
children.push(SP());
children.push(P("Our pipeline runs MILP by default and keeps the LLM verify-and-fix loop available (INTERIOR_MODE=llm) with the MILP layout as a guaranteed fallback, so the run always ends Z3-verified."));

// 9. File structure
children.push(H1("9. File Structure"));
children.push(table(["File", "Description"], [
  ["loop_full.py", "Two-phase orchestrator (exterior -> interior), MILP default / LLM optional"],
  ["optimizer_z3.py", "Z3 Optimize for the provable maximum-area footprint"],
  ["verifier_z3.py", "Z3 exterior verifier (9 SBC constraints)"],
  ["interior_milp.py", "MILP / cutting-plane interior generator (PuLP + CBC)"],
  ["interior_verifier_z3.py", "Z3 interior verifier (25 rules + 4 extras)"],
  ["rooms.py", "Room program: counts, IRC minimums, ensuite + adjacency rules"],
  ["agent1_gemini.py / agent1_interior_gemini.py", "Gemini generators (exterior / interior)"],
  ["agent2_groq.py / agent2_interior_groq.py", "Llama (Groq) feedback writers"],
  ["dxf_full.py / make_milp_viz.py", "Layered .dxf emitter / labeled PNG"],
  ["smoketest_verifier.py / smoketest_interior.py", "Deterministic verifier self-tests"],
], [3800, 5560]));
children.push(SP());

// 10. Output files
children.push(H1("10. Output Files"));
children.push(table(["File", "Contents"], [
  ["output/final_full_layout.dxf", "Plot + tree + house + interior, from verified numbers"],
  ["output/slides/milp_result.png", "Labeled MILP interior figure"],
  ["output/ext_iter_NN_*.{py,txt}", "Per-iteration exterior code and feedback"],
], [4200, 5160]));
children.push(SP());

// 11. Limitations
children.push(H1("11. Limitations and Future Work"));
children.push(BUL("Single location (Seattle). The reference's multi-location building codes (Bellevue, Bothell, Redmond) could be added to the exterior verifier."));
children.push(BUL("Windows are drawn (2 per bedroom) but not part of the formal Z3 constraint set."));
children.push(BUL("The MILP uses a fixed band topology for robustness; a free-placement formulation with an assignment of bedrooms to slots would expose more of CBC's combinatorial search."));

// ---------- assemble ---------------------------------------------------------
const doc = new Document({
  creator: "Ojas Marathe",
  title: "Problem 2 — Two-Agent Neuro-Symbolic CAD Layout (MILP)",
  styles: {
    default: { document: { run: { font: "Arial", size: 21, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "CBD5E1", space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: TEAL },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 560, hanging: 280 } } } }] },
    { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 560, hanging: 280 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Problem 2 — Ojas Marathe        Page ", color: GREY, size: 16 }),
                 new TextRun({ children: [PageNumber.CURRENT], color: GREY, size: 16 })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(PROJ, "Problem2_Documentation_Ours.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});
