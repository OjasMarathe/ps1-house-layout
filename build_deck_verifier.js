// Z3 Verifier component deck — pptxgenjs
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.33 x 7.5
pres.author = "Ojas";
pres.title = "Z3 Verifier";

// ---- palette -------------------------------------------------------------
const INK="14193C", INK2="232A57", WHITE="FFFFFF", ICE="EEF1FB", ICE2="E3E8F8";
const INDIGO="4C5BD4", INDIGO_D="33409C", GREEN="1AA06D", RED="D6455D", AMBER="E0922F";
const TEXT="23284A", MUTED="6B7193", BORDER="D5DBF0";
const HEAD="Georgia", BODY="Calibri", MONO="Consolas";
const W=13.33, H=7.5, MX=0.6;
const sh = () => ({ type:"outer", color:"3A4170", blur:9, offset:3, angle:135, opacity:0.16 });

function footer(s, n){
  s.addText("Z3 Verifier  ·  Ojas  ·  House-design pipeline",
    { x:MX, y:H-0.42, w:8, h:0.3, fontFace:BODY, fontSize:9, color:MUTED, align:"left", margin:0 });
  s.addText(String(n), { x:W-1.0, y:H-0.42, w:0.4, h:0.3, fontFace:BODY, fontSize:9, color:MUTED, align:"right", margin:0 });
}
function titleHead(s, kicker, title){
  s.addText(kicker.toUpperCase(), { x:MX, y:0.42, w:12, h:0.32, fontFace:MONO, fontSize:12, color:INDIGO, charSpacing:2, bold:true, margin:0 });
  s.addText(title, { x:MX, y:0.74, w:12.1, h:0.85, fontFace:HEAD, fontSize:30, color:INK, bold:true, margin:0 });
}
function card(s, x,y,w,h, fill){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x,y,w,h, fill:{color:fill}, line:{color:BORDER,width:1}, rectRadius:0.09, shadow:sh() });
}
function chip(s, x,y,w, txt, col){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x,y,w,h:0.36, fill:{color:"FFFFFF"}, line:{color:col,width:1}, rectRadius:0.06 });
  s.addText(txt, { x:x+0.02,y,w:w-0.04,h:0.36, fontFace:BODY, fontSize:10.5, color:col, bold:true, align:"center", valign:"middle", margin:0 });
}
function arrow(s, x,y,w, col){
  s.addShape(pres.shapes.LINE, { x, y, w, h:0, line:{ color:col, width:2.5, endArrowType:"triangle" } });
}

// ===================================================================== 1 TITLE
let s = pres.addSlide(); s.background={color:INK};
s.addShape(pres.shapes.OVAL, { x:10.4, y:-1.7, w:4.8, h:4.8, fill:{color:INK2} });
s.addShape(pres.shapes.OVAL, { x:11.6, y:4.6, w:3.8, h:3.8, fill:{color:INK2} });
s.addText("THE DETERMINISTIC JUDGE", { x:MX, y:1.55, w:11, h:0.4, fontFace:MONO, fontSize:14, color:"9FB0FF", charSpacing:3, bold:true, margin:0 });
s.addText("The Z3 Verifier", { x:MX, y:2.0, w:11.5, h:1.3, fontFace:HEAD, fontSize:58, color:WHITE, bold:true, margin:0 });
s.addText("Formal, provable constraint checking for the house-design pipeline.",
  { x:MX, y:3.35, w:10.5, h:0.6, fontFace:BODY, fontSize:18, color:"CAD3F5", margin:0 });
// tagline pill
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:MX, y:4.3, w:5.2, h:0.62, fill:{color:INK2}, line:{color:INDIGO,width:1.25}, rectRadius:0.31 });
s.addText("propose  →  prove  →  pass / fail", { x:MX, y:4.3, w:5.2, h:0.62, fontFace:MONO, fontSize:15, color:"DDE3FF", align:"center", valign:"middle", bold:true, margin:0 });
s.addText("Ojas  ·  AI Gurukul  ·  PS-II", { x:MX, y:H-0.7, w:8, h:0.34, fontFace:BODY, fontSize:13, color:"8C97C8", margin:0 });

// ===================================================================== 2 WHAT
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "What it is", "The judge that makes the pipeline trustworthy");
s.addText([
  { text:"An LLM proposes a layout. Z3 ", options:{} },
  { text:"proves", options:{bold:true, color:INDIGO} },
  { text:" it legal — or rejects it with exact reasons.\nSame input, same verdict, every time.", options:{} },
], { x:MX, y:1.75, w:12, h:0.95, fontFace:HEAD, fontSize:21, color:TEXT, lineSpacingMultiple:1.05, margin:0 });

const props = [
  ["Deterministic", "Not a probability — an SMT proof. The same layout always gets the same verdict.", INDIGO],
  ["Provable", "Each rule is checked by Z3 with a measured-vs-required number, never a guess.", GREEN],
  ["Portable", "Swap Gemini ↔ Groq ↔ a human — the judge never changes, so the loop stays honest.", AMBER],
];
let cx=MX, cw=(12.13-2*0.35)/3;
props.forEach((p,i)=>{
  const x=cx+i*(cw+0.35);
  card(s, x, 2.95, cw, 2.45, ICE);
  s.addShape(pres.shapes.OVAL, { x:x+0.32, y:3.25, w:0.62, h:0.62, fill:{color:p[2]} });
  s.addText(String(i+1), { x:x+0.32, y:3.25, w:0.62, h:0.62, fontFace:HEAD, fontSize:22, color:WHITE, bold:true, align:"center", valign:"middle", margin:0 });
  s.addText(p[0], { x:x+0.32, y:4.0, w:cw-0.6, h:0.5, fontFace:HEAD, fontSize:19, color:INK, bold:true, margin:0 });
  s.addText(p[1], { x:x+0.32, y:4.5, w:cw-0.62, h:0.8, fontFace:BODY, fontSize:12.5, color:MUTED, margin:0, lineSpacingMultiple:1.0 });
});
// stat strip
s.addText([
  { text:"~0.01 s", options:{ fontFace:HEAD, fontSize:26, bold:true, color:INDIGO } },
  { text:"   per check  ·  budget is 5 s", options:{ fontFace:BODY, fontSize:14, color:MUTED } },
], { x:MX, y:5.7, w:12, h:0.6, align:"left", valign:"middle", margin:0 });
footer(s,2);

// ===================================================================== 3 WHERE IT SITS
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "Where it sits", "Two gates in the pipeline — it drives both retry loops");
const fy=2.6, bh=1.15;
function flowbox(x,w,label,sub,fill,txtc,bord){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y:fy, w, h:bh, fill:{color:fill}, line:{color:bord||BORDER,width:1.25}, rectRadius:0.08, shadow:sh() });
  s.addText(label, { x:x+0.06, y:fy+0.18, w:w-0.12, h:0.45, fontFace:HEAD, fontSize:13.5, color:txtc, bold:true, align:"center", margin:0 });
  s.addText(sub, { x:x+0.06, y:fy+0.62, w:w-0.12, h:0.4, fontFace:BODY, fontSize:10, color:(fill===INK?"AEB8E6":MUTED), align:"center", margin:0 });
}
const gx=MX;
flowbox(gx,      2.5, "Site Plan\nGenerator", "exterior footprint", ICE, INK);
flowbox(gx+2.85, 2.5, "Z3 VERIFIER", "exterior · 13 rules", INK, WHITE, INDIGO);
flowbox(gx+5.7,  2.5, "Floor Plan\nGenerator", "tiles rooms inside", ICE, INK);
flowbox(gx+8.55, 2.6, "Z3 VERIFIER", "interior · ~25 rules", INK, WHITE, INDIGO);
arrow(s, gx+2.52, fy+bh/2, 0.3, INDIGO_D);
arrow(s, gx+5.37, fy+bh/2, 0.3, INDIGO_D);
arrow(s, gx+8.22, fy+bh/2, 0.3, INDIGO_D);
arrow(s, gx+11.17, fy+bh/2, 0.3, INDIGO_D);
s.addText("→ outputs", { x:gx+11.5, y:fy, w:1.6, h:bh, fontFace:BODY, fontSize:12, color:MUTED, italic:true, valign:"middle", margin:0 });
// retry loops under the two verifier gates
[gx+2.85, gx+8.55].forEach(x=>{
  s.addShape(pres.shapes.LINE, { x, y:fy+bh+0.45, w:2.5, h:0, line:{color:RED,width:2, dashType:"dash", beginArrowType:"triangle"} });
  s.addText("↺ retry on fail (capped)", { x:x-0.1, y:fy+bh+0.55, w:2.7, h:0.35, fontFace:BODY, fontSize:11, color:RED, align:"center", bold:true, margin:0 });
});
// key note card
card(s, MX, 5.45, 12.13, 1.25, ICE2);
s.addText([
  { text:"Tool, not an agent.  ", options:{ bold:true, color:INDIGO } },
  { text:"The generators call the verifier ", options:{} },
  { text:"directly, in their own code", options:{ bold:true, color:INK } },
  { text:" — the Agent Manager routes the step transition, not each check. A FAIL returns the reasons the generator retries on; a PASS releases the layout downstream.", options:{} },
], { x:MX+0.35, y:5.62, w:11.5, h:0.95, fontFace:BODY, fontSize:13.5, color:TEXT, valign:"middle", lineSpacingMultiple:1.03, margin:0 });
footer(s,3);

// ===================================================================== 4 INPUTS / OUTPUTS
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "Inputs & outputs", "What flows in, what flows out — and who's on each end");
const py=1.95, ph=4.7;
// LEFT panel
card(s, MX, py, 4.2, ph, ICE);
s.addText("INPUTS  ·  coming from", { x:MX+0.3, y:py+0.18, w:3.7, h:0.4, fontFace:MONO, fontSize:12, color:INDIGO, bold:true, charSpacing:1, margin:0 });
const ins = [
  ["Constraint Engine", "the ruleset JSON — setbacks, room rules. Single source of truth.", INDIGO],
  ["Site Plan Generator", "footprint to check:  { corners, door }", GREEN],
  ["Floor Plan Generator", "rooms to check (via the Json Extractor)", AMBER],
];
ins.forEach((it,i)=>{
  const y=py+0.75+i*1.27;
  s.addShape(pres.shapes.OVAL, { x:MX+0.3, y:y+0.05, w:0.16, h:0.16, fill:{color:it[2]} });
  s.addText(it[0], { x:MX+0.56, y, w:3.4, h:0.32, fontFace:BODY, fontSize:13.5, color:INK, bold:true, margin:0 });
  s.addText(it[1], { x:MX+0.56, y:y+0.32, w:3.45, h:0.8, fontFace:BODY, fontSize:11, color:MUTED, margin:0, lineSpacingMultiple:1.0 });
});
s.addText("Location Zoning feeds the Constraint Engine — not me directly.",
  { x:MX+0.3, y:py+ph-0.62, w:3.7, h:0.5, fontFace:BODY, fontSize:9.5, italic:true, color:MUTED, margin:0 });
// CENTER node
const nx=5.35, nw=2.6, ny=3.45, nh=1.7;
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:nx, y:ny, w:nw, h:nh, fill:{color:INK}, line:{color:INDIGO,width:1.5}, rectRadius:0.1, shadow:sh() });
s.addText("Z3\nVERIFIER", { x:nx, y:ny+0.28, w:nw, h:0.85, fontFace:HEAD, fontSize:20, color:WHITE, bold:true, align:"center", margin:0 });
s.addText("verify_site · optimize_area · verify_interior", { x:nx+0.1, y:ny+1.12, w:nw-0.2, h:0.5, fontFace:MONO, fontSize:8.5, color:"AEB8E6", align:"center", margin:0 });
arrow(s, MX+4.25, ny+nh/2, 0.95, INDIGO_D);
arrow(s, nx+nw+0.05, ny+nh/2, 0.85, INDIGO_D);
// RIGHT panel
const rx=8.55;
card(s, rx, py, 4.18, ph, ICE);
s.addText("OUTPUTS  ·  going to", { x:rx+0.3, y:py+0.18, w:3.7, h:0.4, fontFace:MONO, fontSize:12, color:INDIGO, bold:true, charSpacing:1, margin:0 });
const outs = [
  ["Site Plan Generator", "max buildable area (target ≥ 90%)", GREEN],
  ["Floor Plan Generator", "verified footprint  —  on PASS", GREEN],
  ["Generators (retry)", "per-constraint reasons  —  on FAIL", RED],
  ["Reviewer + Database", "pass/fail record for sign-off & audit", INDIGO],
];
outs.forEach((it,i)=>{
  const y=py+0.72+i*0.97;
  s.addShape(pres.shapes.OVAL, { x:rx+0.3, y:y+0.05, w:0.16, h:0.16, fill:{color:it[2]} });
  s.addText(it[0], { x:rx+0.56, y, w:3.45, h:0.3, fontFace:BODY, fontSize:13, color:INK, bold:true, margin:0 });
  s.addText(it[1], { x:rx+0.56, y:y+0.3, w:3.4, h:0.5, fontFace:BODY, fontSize:10.5, color:MUTED, margin:0 });
});
footer(s,4);

// ===================================================================== 5 CONTRACT
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "The contract", "Stable in/out shapes — build against these, transport can change");
function codeCard(x,y,w,h,title,tcol,lines){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x,y,w,h, fill:{color:INK}, line:{color:INDIGO_D,width:1}, rectRadius:0.07, shadow:sh() });
  s.addText(title, { x:x+0.3, y:y+0.2, w:w-0.6, h:0.4, fontFace:MONO, fontSize:13, color:tcol, bold:true, charSpacing:1, margin:0 });
  s.addText(lines, { x:x+0.3, y:y+0.68, w:w-0.55, h:h-0.9, fontFace:MONO, fontSize:11.5, color:"DCE2FF", margin:0, lineSpacingMultiple:1.12, valign:"top" });
}
codeCard(MX, 1.95, 5.95, 4.7, "EXTERIOR", "8FE3C0", [
  { text:"in  →", options:{ color:"8FB4FF", breakLine:true } },
  { text:"  corners: [[x,y] × 4]", options:{ breakLine:true } },
  { text:"  door:    [x, y]", options:{ breakLine:true } },
  { text:"  + city / ruleset", options:{ breakLine:true } },
  { text:"", options:{ breakLine:true } },
  { text:"out →", options:{ color:"8FB4FF", breakLine:true } },
  { text:"  ok, n_failed", options:{ breakLine:true } },
  { text:"  constraints: [{rule, pass,", options:{ breakLine:true } },
  { text:"     measured, required, message}]", options:{ breakLine:true } },
  { text:"  max_buildable_area_sqft", options:{ breakLine:true } },
  { text:"  tolerance_ft, solve_time_s", options:{} },
]);
codeCard(MX+6.18, 1.95, 5.95, 4.7, "INTERIOR", "F4C77A", [
  { text:"in  →", options:{ color:"8FB4FF", breakLine:true } },
  { text:"  footprint: [x, y, w, h]", options:{ breakLine:true } },
  { text:"  door:      [x, y]", options:{ breakLine:true } },
  { text:"  rooms: [[name, kind,", options:{ breakLine:true } },
  { text:"     x_min, y_min, x_max, y_max]]", options:{ breakLine:true } },
  { text:"  + city", options:{ breakLine:true } },
  { text:"", options:{ breakLine:true } },
  { text:"out →", options:{ color:"8FB4FF", breakLine:true } },
  { text:"  ok, n_failed", options:{ breakLine:true } },
  { text:"  violations: [{rule, measured,", options:{ breakLine:true } },
  { text:"     required, message}]", options:{} },
]);
s.addText("Coordinates in feet · origin = plot SW corner · same frame the generators emit",
  { x:MX, y:6.8, w:12, h:0.35, fontFace:BODY, fontSize:11.5, italic:true, color:MUTED, align:"center", margin:0 });
footer(s,5);

// ===================================================================== 6 WHAT IT CHECKS
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "What it checks", "13 site rules + ~25 interior rules — one Z3 core");
card(s, MX, 1.95, 5.95, 3.5, ICE);
s.addText("EXTERIOR  ·  site / zoning", { x:MX+0.3, y:2.12, w:5.4, h:0.4, fontFace:MONO, fontSize:12.5, color:INDIGO, bold:true, margin:0 });
const extChips=["Front / rear / side setbacks","Tree-buffer keep-out","Min width & depth","Door egress & placement","Corner-in-plot containment","Min utilization ≥ 90%","Max lot coverage ≤ 35%"];
extChips.forEach((c,i)=>{ const col=i%2, row=Math.floor(i/2);
  chip(s, MX+0.3+col*2.85, 2.62+row*0.52, 2.75, c, (c.includes("35%")?GREEN:INDIGO_D)); });
card(s, MX+6.18, 1.95, 5.95, 3.5, ICE);
s.addText("INTERIOR  ·  IRC room rules", { x:MX+6.48, y:2.12, w:5.4, h:0.4, fontFace:MONO, fontSize:12.5, color:INDIGO, bold:true, margin:0 });
const intChips=["Room min areas & sides","Full program / no drop","No overlap · no gaps","Ensuite bath ↔ bedroom","Bath ⊥ kitchen & each other","Living near entry","Living > each bedroom","Corridor ≤ 15% usable","Every room connected"];
intChips.forEach((c,i)=>{ const col=i%2, row=Math.floor(i/2);
  const isNew=c.includes("> each")||c.includes("15%");
  chip(s, MX+6.48+col*2.85, 2.62+row*0.46, 2.75, c, (isNew?GREEN:INDIGO_D)); });
// new-rules callout
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:MX, y:5.7, w:12.13, h:1.0, fill:{color:"E9F7F0"}, line:{color:GREEN,width:1.25}, rectRadius:0.08 });
s.addText([
  { text:"Just added  ", options:{ bold:true, color:GREEN, fontFace:HEAD, fontSize:15 } },
  { text:"max lot coverage 35%   ·   living > each bedroom   ·   corridor ≤ 15%", options:{ color:INK, fontFace:BODY, fontSize:14, bold:true } },
], { x:MX+0.35, y:5.7, w:11.4, h:1.0, valign:"middle", margin:0 });
footer(s,6);

// ===================================================================== 7 MODES + CITY
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "Two modes · city-agnostic", "Same Z3 code, different code-book per city");
card(s, MX, 1.95, 3.4, 2.25, ICE);
s.addText("OPTIMIZE", { x:MX+0.3, y:2.12, w:2.9, h:0.4, fontFace:HEAD, fontSize:18, color:INDIGO, bold:true, margin:0 });
s.addText("“What's the most I can legally build here?”\n→ provable max buildable area.",
  { x:MX+0.3, y:2.6, w:2.85, h:1.45, fontFace:BODY, fontSize:12.5, color:TEXT, margin:0, lineSpacingMultiple:1.04, valign:"top" });
card(s, MX+3.65, 1.95, 3.4, 2.25, ICE);
s.addText("VERIFY", { x:MX+3.95, y:2.12, w:2.9, h:0.4, fontFace:HEAD, fontSize:18, color:INDIGO, bold:true, margin:0 });
s.addText("“Is this exact layout legal?”\n→ per-constraint PASS / FAIL with reasons.",
  { x:MX+3.95, y:2.6, w:2.85, h:1.45, fontFace:BODY, fontSize:12.5, color:TEXT, margin:0, lineSpacingMultiple:1.04, valign:"top" });
// chart: city comparison (right column, clear of the cards and the dark strip)
s.addText("Max buildable area — same lot, different city JSON", { x:7.75, y:1.95, w:5, h:0.35, fontFace:BODY, fontSize:11.5, color:MUTED, italic:true, margin:0 });
s.addChart(pres.charts.BAR, [{ name:"sq ft", labels:["Seattle (35% cap)","Bellevue (40% cap)"], values:[2247,2568] }], {
  x:7.75, y:2.35, w:4.95, h:1.8, barDir:"col", chartColors:[INDIGO, GREEN],
  showValue:true, dataLabelPosition:"outEnd", dataLabelColor:INK, dataLabelFontSize:12, dataLabelFontBold:true,
  catAxisLabelColor:MUTED, catAxisLabelFontSize:10, valAxisHidden:true, valGridLine:{style:"none"},
  showLegend:false, showTitle:false, chartArea:{fill:{color:"FFFFFF"}}, barGapWidthPct:55,
});
// config note strip (below everything — no overlap)
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:MX, y:4.5, w:12.13, h:2.0, fill:{color:INK}, line:{color:INDIGO_D,width:1}, rectRadius:0.08, shadow:sh() });
s.addText("Constraints are config, not code.", { x:MX+0.4, y:4.7, w:11, h:0.5, fontFace:HEAD, fontSize:18, color:WHITE, bold:true, margin:0 });
s.addText([
  { text:"A new jurisdiction is a new ", options:{} },
  { text:"citycodes/<city>.json", options:{ fontFace:MONO, color:"9FB0FF" } },
  { text:" file — zero verifier changes. The Z3 engine is identical for Seattle and Bellevue; only the numbers differ. This is the prototype of what the Constraint Engine now owns.", options:{} },
], { x:MX+0.4, y:5.25, w:11.5, h:1.1, fontFace:BODY, fontSize:13.5, color:"D7DDF5", margin:0, lineSpacingMultiple:1.06, valign:"top" });
footer(s,7);

// ===================================================================== 8 TRUSTWORTHY
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "Why it's trustworthy", "The four properties that make it a judge, not a guesser");
const why=[
  ["Provable","Every rule decided by Z3 — a measured-vs-required proof, not a probability.",INDIGO],
  ["Tolerant","A configurable float tolerance: rounding noise never causes a false failure.",GREEN],
  ["Fast","~0.01 s per check against a 5 s budget — fits inside a tight retry loop.",AMBER],
  ["Direct","A pure tool call: no Agent-Manager hop, no side effects, fully reproducible.",RED],
];
const w2=(12.13-0.35)/2, h2=2.15;
why.forEach((p,i)=>{ const col=i%2,row=Math.floor(i/2);
  const x=MX+col*(w2+0.35), y=2.0+row*(h2+0.35);
  card(s, x, y, w2, h2, ICE);
  s.addShape(pres.shapes.OVAL, { x:x+0.32, y:y+0.32, w:0.55, h:0.55, fill:{color:p[2]} });
  s.addText("✓", { x:x+0.32, y:y+0.32, w:0.55, h:0.55, fontFace:BODY, fontSize:20, color:WHITE, bold:true, align:"center", valign:"middle", margin:0 });
  s.addText(p[0], { x:x+1.05, y:y+0.34, w:w2-1.3, h:0.5, fontFace:HEAD, fontSize:20, color:INK, bold:true, margin:0 });
  s.addText(p[1], { x:x+1.05, y:y+0.86, w:w2-1.35, h:1.0, fontFace:BODY, fontSize:13.5, color:MUTED, margin:0, lineSpacingMultiple:1.05 });
});
footer(s,8);

// ===================================================================== 9 DEMO
s = pres.addSlide(); s.background={color:INK};
s.addText("RUN THE DEMO", { x:MX, y:0.55, w:11, h:0.4, fontFace:MONO, fontSize:13, color:"9FB0FF", charSpacing:3, bold:true, margin:0 });
s.addText("One command — runs in ~2 seconds", { x:MX, y:0.92, w:11.5, h:0.8, fontFace:HEAD, fontSize:30, color:WHITE, bold:true, margin:0 });
// command pill
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:MX, y:2.0, w:8.6, h:0.95, fill:{color:"0C1030"}, line:{color:INDIGO,width:1.5}, rectRadius:0.1 });
s.addText([
  { text:"$ ", options:{ color:GREEN } },
  { text:"cd ~/ps1-house-layout && bash demo.sh", options:{ color:"EDEFFF" } },
], { x:MX+0.35, y:2.0, w:8.2, h:0.95, fontFace:MONO, fontSize:18, bold:true, valign:"middle", margin:0 });
s.addText("(from the project folder · uses the bundled .venv)", { x:MX+9.0, y:2.0, w:3.6, h:0.95, fontFace:BODY, fontSize:11.5, italic:true, color:"8C97C8", valign:"middle", margin:0 });
// the 6 beats
const beats=[
  ["cities","constraints are config, not code"],
  ["optimize","provable max area — Seattle 2247 vs Bellevue 2568"],
  ["verify (legal)","all 13 rules proven PASS in ~9 ms"],
  ["verify (illegal)","rejected, with measured-vs-required reasons"],
  ["tolerance","5e-7 ft ignored · 0.01 ft caught"],
  ["interior","same engine, IRC room rules"],
];
const by=3.35, colw=5.9;
beats.forEach((b,i)=>{ const col=i%2,row=Math.floor(i/2);
  const x=MX+col*(colw+0.33), y=by+row*0.95;
  s.addShape(pres.shapes.OVAL, { x, y:y+0.04, w:0.5, h:0.5, fill:{color:INDIGO} });
  s.addText(String(i+1), { x, y:y+0.04, w:0.5, h:0.5, fontFace:HEAD, fontSize:16, color:WHITE, bold:true, align:"center", valign:"middle", margin:0 });
  s.addText(b[0], { x:x+0.65, y:y, w:colw-0.7, h:0.32, fontFace:MONO, fontSize:13.5, color:"BFE8D6", bold:true, margin:0 });
  s.addText(b[1], { x:x+0.65, y:y+0.32, w:colw-0.7, h:0.4, fontFace:BODY, fontSize:11.5, color:"C5CCEC", margin:0 });
});
s.addText("Single commands also work:  python verifier_tool.py verify --city seattle --layout house.json",
  { x:MX, y:H-0.62, w:12, h:0.35, fontFace:MONO, fontSize:10.5, color:"7E89BC", margin:0 });

// ===================================================================== 10 STATUS / NEXT
s = pres.addSlide(); s.background={color:WHITE};
titleHead(s, "Status & next", "Built, green, and ready to integrate");
card(s, MX, 2.0, 5.95, 3.0, "E9F7F0");
s.addText("DONE", { x:MX+0.32, y:2.2, w:4, h:0.4, fontFace:MONO, fontSize:13, color:GREEN, bold:true, charSpacing:2, margin:0 });
s.addText([
  { text:"Both verifiers + optimizer, 38 rules", options:{ bullet:true, breakLine:true } },
  { text:"3 new rules: coverage 35%, living>bed, corridor 15%", options:{ bullet:true, breakLine:true } },
  { text:"City-config JSON · float tolerance · CLI", options:{ bullet:true, breakLine:true } },
  { text:"Tests green: verifier 6/6, interior ALL PASS", options:{ bullet:true } },
], { x:MX+0.35, y:2.65, w:5.4, h:2.2, fontFace:BODY, fontSize:13, color:TEXT, margin:0, paraSpaceAfter:6 });
card(s, MX+6.18, 2.0, 5.95, 3.0, ICE);
s.addText("NEXT", { x:MX+6.5, y:2.2, w:4, h:0.4, fontFace:MONO, fontSize:13, color:INDIGO, bold:true, charSpacing:2, margin:0 });
s.addText([
  { text:"Consume Constraint Engine JSON (per schema)", options:{ bullet:true, breakLine:true } },
  { text:"Confirm footprint / room shapes with generators", options:{ bullet:true, breakLine:true } },
  { text:"Switch tree keep-out to a polygon", options:{ bullet:true, breakLine:true } },
  { text:"Optional: wrap as an MCP server (same 3 fns)", options:{ bullet:true } },
], { x:MX+6.53, y:2.65, w:5.4, h:2.2, fontFace:BODY, fontSize:13, color:TEXT, margin:0, paraSpaceAfter:6 });
// closing line
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x:MX, y:5.35, w:12.13, h:1.15, fill:{color:INK}, line:{color:INDIGO_D,width:1}, rectRadius:0.09, shadow:sh() });
s.addText([
  { text:"Propose → prove → pass/fail.  ", options:{ fontFace:HEAD, bold:true, color:WHITE } },
  { text:"The deterministic core the whole pipeline can trust.", options:{ color:"CAD3F5" } },
], { x:MX+0.4, y:5.35, w:11.5, h:1.15, fontFace:BODY, fontSize:16, valign:"middle", margin:0 });
footer(s,10);

pres.writeFile({ fileName:"Z3_Verifier_Presentation.pptx" }).then(f=>console.log("WROTE",f));
