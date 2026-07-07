// Window Agent + Roof Plan Agent — presentation deck
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                 // 13.33 x 7.5
pres.author = "Ojas";
pres.title = "Window Agent & Roof Plan Agent";

const INK="1A1D29", INK2="262B3D", WHITE="FFFFFF", ICE="F3F4F8", ICE2="E9ECF3";
const AMBER="E39321", AMBERD="B9761A", TEAL="1C7293", TEALD="14566B",
      GREEN="1AA06D", RED="D6455D", TEXT="23283A", MUTED="6A7186", BORDER="DCE1EB";
const HEAD="Georgia", BODY="Calibri", MONO="Consolas";
const W=13.33, H=7.5, MX=0.6;
const sh=()=>({type:"outer",color:"2A2F42",blur:9,offset:3,angle:135,opacity:0.16});

function footer(s,n){
  s.addText("Window Agent + Roof Plan Agent  ·  Ojas  ·  AI Gurukul PS-II",
    {x:MX,y:H-0.42,w:9,h:0.3,fontFace:BODY,fontSize:9,color:MUTED,margin:0});
  s.addText(String(n),{x:W-1.0,y:H-0.42,w:0.4,h:0.3,fontFace:BODY,fontSize:9,color:MUTED,align:"right",margin:0});
}
function titleHead(s,kicker,title){
  s.addText(kicker.toUpperCase(),{x:MX,y:0.42,w:12,h:0.32,fontFace:MONO,fontSize:12,color:AMBERD,charSpacing:2,bold:true,margin:0});
  s.addText(title,{x:MX,y:0.74,w:12.1,h:0.85,fontFace:HEAD,fontSize:27,color:INK,bold:true,margin:0});
}
function card(s,x,y,w,h,fill,bord){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h,fill:{color:fill},line:{color:bord||BORDER,width:1},rectRadius:0.08,shadow:sh()});
}
function chip(s,x,y,w,txt,col){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h:0.34,fill:{color:"FFFFFF"},line:{color:col,width:1},rectRadius:0.06});
  s.addText(txt,{x:x+0.02,y,w:w-0.04,h:0.34,fontFace:BODY,fontSize:10,color:col,bold:true,align:"center",valign:"middle",margin:0});
}
function term(s,x,y,w,h,title,tcol,lines){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h,fill:{color:"12141F"},line:{color:INK2,width:1},rectRadius:0.07,shadow:sh()});
  if(title) s.addText(title,{x:x+0.28,y:y+0.16,w:w-0.5,h:0.34,fontFace:MONO,fontSize:12,color:tcol,bold:true,margin:0});
  s.addText(lines,{x:x+0.28,y:y+(title?0.6:0.22),w:w-0.5,h:h-(title?0.75:0.4),fontFace:MONO,fontSize:11,color:"D6DBEA",lineSpacingMultiple:1.12,valign:"top",margin:0});
}

// ============================================================ 1 TITLE
let s=pres.addSlide(); s.background={color:INK};
s.addShape(pres.shapes.OVAL,{x:10.3,y:-1.5,w:4.6,h:4.6,fill:{color:AMBER}});      // sun
s.addShape(pres.shapes.OVAL,{x:10.75,y:-1.05,w:3.7,h:3.7,fill:{color:INK}});
s.addShape(pres.shapes.OVAL,{x:11.55,y:4.9,w:3.4,h:3.4,fill:{color:INK2}});
s.addText("RESEARCH · BUILD · DEMO",{x:MX,y:1.5,w:11,h:0.4,fontFace:MONO,fontSize:14,color:"F2C67A",charSpacing:3,bold:true,margin:0});
s.addText("Window Agent  &  Roof Plan Agent",{x:MX,y:1.98,w:12,h:1.1,fontFace:HEAD,fontSize:42,color:WHITE,bold:true,margin:0});
s.addText("Deterministic, constraints-first daylight compliance  ·  lighting-aware roofing",
  {x:MX,y:3.5,w:11,h:0.5,fontFace:BODY,fontSize:18,color:"CBD2E0",margin:0});
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:4.35,w:6.0,h:0.6,fill:{color:INK2},line:{color:AMBER,width:1.25},rectRadius:0.3});
s.addText("shift-left  ·  provable  ·  IRC-grounded",{x:MX,y:4.35,w:6.0,h:0.6,fontFace:MONO,fontSize:14,color:"F3D8A8",align:"center",valign:"middle",bold:true,margin:0});
s.addText("Ojas  ·  AI Gurukul  ·  PS-II",{x:MX,y:H-0.7,w:8,h:0.34,fontFace:BODY,fontSize:13,color:"8C93A8",margin:0});

// ============================================================ 2 OVERVIEW
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Overview","Two agents — researched, built, and demoed");
const ov=[
  ["Window Agent",AMBER,["Turned Aadi's daylight *scorer* into a","shift-left, deterministic *constraint* layer.","Hard code rules (egress, light, glazing) are","given to the generator + proved by Z3;","the soft daylight score stays non-blocking."]],
  ["Roof Plan Agent",TEAL,["Deterministic roof geometry (gable/hip/shed/","flat), multi-floor stepped roofs, pitch +","drainage — Z3-self-verified. Now places","sunroofs using the Window Agent's daylight","scores (lighting-aware roofing)."]],
];
ov.forEach((o,i)=>{ const x=MX+i*6.15;
  card(s,x,1.95,5.95,4.4,ICE);
  s.addShape(pres.shapes.RECTANGLE,{x:x,y:1.95,w:0.12,h:4.4,fill:{color:o[1]}});
  s.addText(o[0],{x:x+0.35,y:2.15,w:5.4,h:0.5,fontFace:HEAD,fontSize:20,color:INK,bold:true,margin:0});
  s.addText(o[2].map((t,k)=>({text:t,options:{breakLine:k<o[2].length-1}})),
    {x:x+0.35,y:2.75,w:5.4,h:3.2,fontFace:BODY,fontSize:14,color:TEXT,lineSpacingMultiple:1.12,valign:"top",margin:0});
});
s.addText("Both are pure, reproducible, no-LLM tools that plug into the Z3 Verifier + DXF/PDF exports.",
  {x:MX,y:6.55,w:12,h:0.35,fontFace:BODY,fontSize:12.5,italic:true,color:MUTED,align:"center",margin:0});
footer(s,2);

// ============================================================ 3 WINDOW: START + FEEDBACK
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Window Agent","The starting point, and the mentor's feedback");
card(s,MX,1.95,5.95,4.55,ICE);
s.addText("What existed (Aadi)",{x:MX+0.3,y:2.12,w:5.4,h:0.4,fontFace:HEAD,fontSize:16,color:INK,bold:true,margin:0});
s.addText([
  {text:"A deterministic daylight SCORER + suggester:",options:{breakLine:true}},
  {text:"ranks exterior walls by sun exposure + tree",options:{breakLine:true}},
  {text:"shade, suggests windows to hit a window-to-",options:{breakLine:true}},
  {text:"floor ratio, scores daylight 0–100.",options:{breakLine:true}},
  {text:"No LLM · reproducible · a soft signal.",options:{color:TEALD,bold:true}},
],{x:MX+0.3,y:2.65,w:5.45,h:2.0,fontFace:BODY,fontSize:13.5,color:TEXT,lineSpacingMultiple:1.1,valign:"top",margin:0});
s.addText("The gap: it verifies AFTER the fact and enforces no hard code rules (egress, glazing, sill).",
  {x:MX+0.3,y:5.55,w:5.45,h:0.8,fontFace:BODY,fontSize:12.5,italic:true,color:AMBERD,valign:"top",margin:0});
card(s,MX+6.15,1.95,5.95,4.55,"FDF4E6",AMBER);
s.addText("Mentor's feedback (the ask)",{x:MX+6.45,y:2.12,w:5.4,h:0.4,fontFace:HEAD,fontSize:16,color:AMBERD,bold:true,margin:0});
s.addText([
  {text:"Follow the LAC guideline",options:{bullet:true,breakLine:true,bold:true}},
  {text:"Lighting-only verification adds latency (retry loops)",options:{bullet:true,breakLine:true}},
  {text:"Shift-left: give lighting as constraints, not post-checks",options:{bullet:true,breakLine:true}},
  {text:"Explore deterministic vs non-deterministic verification",options:{bullet:true,breakLine:true}},
  {text:"Formalise the hard window rules (egress, tempered glass,",options:{bullet:true,breakLine:true}},
  {text:"    sill/header, per-room placement) with Constraint Engine",options:{breakLine:true}},
  {text:"    + Floor Plan",options:{}},
],{x:MX+6.48,y:2.65,w:5.4,h:3.6,fontFace:BODY,fontSize:13,color:TEXT,lineSpacingMultiple:1.05,paraSpaceAfter:4,valign:"top",margin:0});
footer(s,3);

// ============================================================ 4 LAC
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"The LAC guideline","Latency · Accuracy · Concurrency → three decisions");
s.addText("\"LAC\" is a systems trilemma. It isn't a separate task — it is the rationale for every decision below.",
  {x:MX,y:1.75,w:12,h:0.4,fontFace:BODY,fontSize:14,color:TEXT,margin:0});
const lac=[
  ["Latency",AMBER,"Don't stall in retry loops","Decision 2 — SHIFT-LEFT the hard rules into constraints, so illegal windows aren't generated → far fewer generate→verify→fail rounds."],
  ["Accuracy",TEAL,"Verdicts correct & reproducible","Decision 1 — DETERMINISTIC verification: a provable, same-input→same-verdict gate (a stochastic sim can't guarantee this)."],
  ["Concurrency",GREEN,"Agents run in parallel","Decision 2 (soft tier) — the daylight SCORE is NON-BLOCKING; Livability runs concurrently, only a real violation gates."],
];
const cw=(12.13-2*0.3)/3;
lac.forEach((l,i)=>{ const x=MX+i*(cw+0.3);
  card(s,x,2.35,cw,3.9,ICE);
  s.addShape(pres.shapes.OVAL,{x:x+cw/2-0.4,y:2.6,w:0.8,h:0.8,fill:{color:l[1]}});
  s.addText(l[0][0],{x:x+cw/2-0.4,y:2.6,w:0.8,h:0.8,fontFace:HEAD,fontSize:30,color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
  s.addText(l[0],{x:x+0.2,y:3.55,w:cw-0.4,h:0.4,fontFace:HEAD,fontSize:18,color:INK,bold:true,align:"center",margin:0});
  s.addText(l[2],{x:x+0.2,y:3.98,w:cw-0.4,h:0.4,fontFace:BODY,fontSize:11.5,italic:true,color:MUTED,align:"center",margin:0});
  s.addText(l[3],{x:x+0.28,y:4.45,w:cw-0.56,h:1.7,fontFace:BODY,fontSize:12,color:TEXT,align:"center",lineSpacingMultiple:1.05,valign:"top",margin:0});
});
footer(s,4);

// ============================================================ 5 DECISION 1
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Decision 1 — Accuracy","Lighting/compliance verification is DETERMINISTIC");
const rows=[
  ["A","Deterministic analytic (WWR, sun-weight, code predicates)","Yes","Yes","~ms",GREEN],
  ["B","Physically-based daylight sim (Radiance, Monte-Carlo)","No*","No","sec–min",RED],
  ["C","LLM / ML judge of \"is the lighting ok\"","No","No","slow + $",RED],
];
s.addText([{text:"cols:  Approach",options:{}}], {x:0,y:0,w:0.1,h:0.1,fontSize:1,color:"FFFFFF"}); // spacer noop
// header
const tx=MX, tw=12.13, hy=2.0;
s.addShape(pres.shapes.RECTANGLE,{x:tx,y:hy,w:tw,h:0.42,fill:{color:INK}});
[["Approach",0.55,5.6],["Reproducible",6.35,1.9],["Provable",8.35,1.6],["Latency",10.15,1.9]].forEach(c=>
  s.addText(c[0],{x:tx+c[1],y:hy,w:c[2],h:0.42,fontFace:BODY,fontSize:12,color:"FFFFFF",bold:true,valign:"middle",margin:0}));
rows.forEach((r,i)=>{ const y=hy+0.42+i*0.72;
  s.addShape(pres.shapes.RECTANGLE,{x:tx,y,w:tw,h:0.72,fill:{color:i%2?ICE:"FFFFFF"},line:{color:BORDER,width:0.5}});
  s.addShape(pres.shapes.OVAL,{x:tx+0.18,y:y+0.2,w:0.32,h:0.32,fill:{color:r[5]}});
  s.addText(r[0],{x:tx+0.18,y:y+0.2,w:0.32,h:0.32,fontFace:HEAD,fontSize:13,color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
  s.addText(r[1],{x:tx+0.6,y,w:5.6,h:0.72,fontFace:BODY,fontSize:12,color:TEXT,valign:"middle",margin:0});
  s.addText(r[2],{x:tx+6.35,y,w:1.9,h:0.72,fontFace:BODY,fontSize:12,color:(r[2][0]==='Y'?GREEN:RED),bold:true,valign:"middle",margin:0});
  s.addText(r[3],{x:tx+8.35,y,w:1.6,h:0.72,fontFace:BODY,fontSize:12,color:(r[3][0]==='Y'?GREEN:RED),bold:true,valign:"middle",margin:0});
  s.addText(r[4],{x:tx+10.15,y,w:1.9,h:0.72,fontFace:BODY,fontSize:12,color:MUTED,valign:"middle",margin:0});
});
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:4.95,w:12.13,h:1.55,fill:{color:INK},line:{color:AMBERD,width:1},rectRadius:0.08,shadow:sh()});
s.addText([
  {text:"The linchpin:  ",options:{fontFace:HEAD,bold:true,color:"F2C67A"}},
  {text:"shift-left ",options:{color:AMBER,bold:true}},
  {text:"requires ",options:{color:WHITE,italic:true}},
  {text:"determinism — you can only hand a rule to the generator as a CONSTRAINT if it is a decidable predicate. A Monte-Carlo daylight score can never be a constraint, only a post-hoc score.",options:{color:"CFD5E4"}},
],{x:MX+0.4,y:4.95,w:11.4,h:1.55,fontFace:BODY,fontSize:14.5,valign:"middle",lineSpacingMultiple:1.05,margin:0});
s.addText("* Monte-Carlo daylight metrics vary run-to-run — unacceptable for a legal gate.",{x:MX,y:H-0.62,w:10,h:0.3,fontFace:BODY,fontSize:10,italic:true,color:MUTED,margin:0});
footer(s,5);

// ============================================================ 6 DECISION 2
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Decision 2 — Latency","Shift-left: split HARD constraints from the SOFT score");
// the expensive loop
card(s,MX,1.95,12.13,1.55,"FBECEE",RED);
s.addText("Before — verify after the fact",{x:MX+0.3,y:2.08,w:6,h:0.35,fontFace:HEAD,fontSize:14,color:RED,bold:true,margin:0});
["generate","verify","FAIL","regenerate"].forEach((t,i)=>{ const x=MX+0.35+i*2.35;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y:2.5,w:1.9,h:0.62,fill:{color:i==2?RED:"FFFFFF"},line:{color:RED,width:1},rectRadius:0.3});
  s.addText(t,{x,y:2.5,w:1.9,h:0.62,fontFace:BODY,fontSize:12.5,color:i==2?"FFFFFF":TEXT,bold:true,align:"center",valign:"middle",margin:0});
  if(i<3) s.addShape(pres.shapes.LINE,{x:x+1.92,y:2.81,w:0.4,h:0,line:{color:RED,width:2,endArrowType:"triangle"}});
});
s.addText("↺ every failed round is a full (LLM) regeneration = latency",{x:MX+9.7,y:2.5,w:2.6,h:0.62,fontFace:BODY,fontSize:10.5,color:RED,italic:true,valign:"middle",margin:0});
// the shift-left way
card(s,MX,3.7,12.13,1.4,"E9F7F0",GREEN);
s.addText("After — constraints first (correct-by-construction)",{x:MX+0.3,y:3.83,w:8,h:0.35,fontFace:HEAD,fontSize:14,color:GREEN,bold:true,margin:0});
["constraints given up front","generator satisfies them","verify (usually passes)"].forEach((t,i)=>{ const x=MX+0.35+i*3.2;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y:4.25,w:2.85,h:0.62,fill:{color:"FFFFFF"},line:{color:GREEN,width:1},rectRadius:0.3});
  s.addText(t,{x,y:4.25,w:2.85,h:0.62,fontFace:BODY,fontSize:11.5,color:TEXT,bold:true,align:"center",valign:"middle",margin:0});
  if(i<2) s.addShape(pres.shapes.LINE,{x:x+2.87,y:4.56,w:0.28,h:0,line:{color:GREEN,width:2,endArrowType:"triangle"}});
});
// hard vs soft
card(s,MX,5.3,5.95,1.2,ICE);
s.addText([{text:"HARD (gate): ",options:{bold:true,color:INK}},{text:"egress · light ≥8% · vent ≥4% · safety glazing · sill — proved by Z3, given to the generator.",options:{color:TEXT}}],
  {x:MX+0.3,y:5.3,w:5.4,h:1.2,fontFace:BODY,fontSize:12,valign:"middle",lineSpacingMultiple:1.03,margin:0});
card(s,MX+6.18,5.3,5.95,1.2,ICE);
s.addText([{text:"SOFT (score): ",options:{bold:true,color:AMBERD}},{text:"daylight quality, orientation, tree-shade, aesthetics — Aadi's agent, non-blocking, in the report.",options:{color:TEXT}}],
  {x:MX+6.48,y:5.3,w:5.4,h:1.2,fontFace:BODY,fontSize:12,valign:"middle",lineSpacingMultiple:1.03,margin:0});
footer(s,6);

// ============================================================ 7 IRC RULE SET
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Decision 3 — the rule set","Every hard rule grounded in the IRC (auditable, city-tunable)");
const irc=[
  ["egress_window","Each sleeping room: 1 operable window, net clear ≥ 5.7 sq ft, ≥ 24 in H, ≥ 20 in W, sill ≤ 44 in","IRC R310",AMBER],
  ["natural_light","Habitable room glazing ≥ 8% of floor area","IRC R303.1",TEAL],
  ["natural_ventilation","Openable area ≥ 4% of floor area","IRC R303.1",TEAL],
  ["safety_glazing","Sill < 18 in, wet rooms, or next to a door → must be tempered","IRC R308.4",AMBER],
  ["operable-for-egress","Egress windows must be an operable type (fixed/picture rejected)","IRC R310",GREEN],
];
irc.forEach((r,i)=>{ const y=2.0+i*0.86;
  card(s,MX,y,12.13,0.74,i%2?ICE2:ICE);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+0.2,y:y+0.14,w:2.9,h:0.46,fill:{color:r[3]},line:{color:r[3],width:1},rectRadius:0.06});
  s.addText(r[0],{x:MX+0.2,y:y+0.14,w:2.9,h:0.46,fontFace:MONO,fontSize:11.5,color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
  s.addText(r[1],{x:MX+3.35,y,w:7.4,h:0.74,fontFace:BODY,fontSize:12.5,color:TEXT,valign:"middle",margin:0});
  s.addText(r[2],{x:MX+10.9,y,w:1.1,h:0.74,fontFace:MONO,fontSize:11,color:AMBERD,bold:true,valign:"middle",margin:0});
});
s.addText("(city) values — the tempered-sill and egress-sill thresholds — are overridable per jurisdiction by the Constraint Engine ruleset.",
  {x:MX,y:6.45,w:12,h:0.35,fontFace:BODY,fontSize:11,italic:true,color:MUTED,align:"center",margin:0});
footer(s,7);

// ============================================================ 8 FEEDBACK - PRINCIPLES
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Feedback → response (1/3)","The four principles");
const fb1=[
  ["Follow the LAC guideline","Identified LAC = Latency·Accuracy·Concurrency; the three design decisions each target one leg."],
  ["Lighting-only verification adds latency","Confirmed — the generate→verify→fail loop is the cost; addressed by shift-left."],
  ["Shift-left lighting as constraints","Built verify_windows: hard rules are now constraints given to the generator + proved, not post-hoc checks."],
  ["Deterministic vs non-deterministic?","Decided DETERMINISTIC, with the linchpin justification (shift-left needs decidable predicates)."],
];
fb1.forEach((f,i)=>{ const y=2.0+i*1.12;
  card(s,MX,y,12.13,1.0,ICE);
  s.addShape(pres.shapes.OVAL,{x:MX+0.28,y:y+0.28,w:0.44,h:0.44,fill:{color:AMBER}});
  s.addText("Q"+(i+1),{x:MX+0.28,y:y+0.28,w:0.44,h:0.44,fontFace:BODY,fontSize:11,color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
  s.addText(f[0],{x:MX+0.95,y:y+0.14,w:11,h:0.34,fontFace:HEAD,fontSize:14.5,color:INK,bold:true,margin:0});
  s.addText([{text:"→ ",options:{color:GREEN,bold:true}},{text:f[1],options:{color:TEXT}}],
    {x:MX+0.95,y:y+0.5,w:11,h:0.44,fontFace:BODY,fontSize:12.5,valign:"top",margin:0});
});
footer(s,8);

// ============================================================ 9 FEEDBACK - HARD RULES
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Feedback → response (2/3)","The window rules we made HARD + provable");
const fb2=[
  ["Bedrooms need fire-escape windows","egress_window — IRC R310 (≥5.7 sqft, 24×20 in, sill ≤44 in, operable)",GREEN],
  ["Tempered glass below height X","safety_glazing — IRC R308.4, city-tunable sill threshold",GREEN],
  ["Sill / header height","sill_height_ft field; enforced by egress + tempered rules",GREEN],
  ["Enough light & air per room","natural_light ≥8%, natural_ventilation ≥4% — IRC R303.1",GREEN],
  ["Fire-egress ⇒ operable (sliding/openable)","egress requires an operable window type",GREEN],
];
fb2.forEach((f,i)=>{ const y=2.0+i*0.9;
  card(s,MX,y,12.13,0.78,i%2?ICE2:ICE);
  s.addText("✓",{x:MX+0.25,y,w:0.5,h:0.78,fontFace:BODY,fontSize:20,color:GREEN,bold:true,align:"center",valign:"middle",margin:0});
  s.addText(f[0],{x:MX+0.85,y,w:4.9,h:0.78,fontFace:BODY,fontSize:13,color:INK,bold:true,valign:"middle",margin:0});
  s.addText(f[1],{x:MX+5.85,y,w:6.15,h:0.78,fontFace:MONO,fontSize:10.5,color:TEXT,valign:"middle",margin:0});
});
s.addText("All deterministic, city-parameterisable, and callable as verify_windows(windows, rooms, constraints=ruleset).",
  {x:MX,y:6.55,w:12,h:0.35,fontFace:BODY,fontSize:11.5,italic:true,color:MUTED,align:"center",margin:0});
footer(s,9);

// ============================================================ 10 FEEDBACK - SOFT
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Feedback → response (3/3)","Placement & aesthetics — soft, or needs coordination");
const fb3=[
  ["Bathroom window near shower / 3×2 max","SOFT — needs fixture (shower) position from Floor Plan"],
  ["Master bath windows around the tub","SOFT — needs tub position from Floor Plan"],
  ["Walk-in closet: small, high window","SOFT — placement heuristic"],
  ["Kitchen window above the sink","SOFT — needs sink position from Floor Plan"],
  ["Bedroom window not behind the bed","SOFT — needs bed position from Floor Plan"],
  ["Aesthetic glazing scales with budget","SOFT — a Livability score dimension, not code"],
  ["Garage window; patio ⇒ sliding door","Optional / handled by Floor Plan (doors)"],
];
fb3.forEach((f,i)=>{ const col=i%2,row=Math.floor(i/2);
  const x=MX+col*6.15, y=2.0+row*0.98;
  card(s,x,y,5.95,0.85,ICE);
  s.addShape(pres.shapes.OVAL,{x:x+0.22,y:y+0.29,w:0.28,h:0.28,fill:{color:AMBER}});
  s.addText(f[0],{x:x+0.62,y:y+0.1,w:5.2,h:0.36,fontFace:BODY,fontSize:12,color:INK,bold:true,margin:0});
  s.addText(f[1],{x:x+0.62,y:y+0.44,w:5.2,h:0.36,fontFace:BODY,fontSize:10.5,color:MUTED,margin:0});
});
s.addText([{text:"Decision: ",options:{bold:true,color:AMBERD}},{text:"promote these to HARD checks the moment the Floor Plan agent emits fixture coordinates (sink, bed, tub). Coordination item with Prasad.",options:{color:TEXT}}],
  {x:MX,y:6.05,w:12.13,h:0.6,fontFace:BODY,fontSize:12.5,align:"center",valign:"middle",margin:0});
footer(s,10);

// ============================================================ 11 WINDOW DEMO
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Window Agent — demo","Deterministic, ~6 ms, exact measured-vs-required");
term(s,MX,2.0,5.95,4.4,"$ verify_windows(compliant)","7BE0B0",[
  {text:"3 rooms: bedroom, living, bathroom",options:{breakLine:true,color:"9AA3B8"}},
  {text:"",options:{breakLine:true}},
  {text:"ok            : True",options:{color:"9FE6C4",breakLine:true}},
  {text:"n_failed      : 0",options:{color:"9FE6C4",breakLine:true}},
  {text:"solve_time_s  : 0.006",options:{color:"9FE6C4",breakLine:true}},
  {text:"",options:{breakLine:true}},
  {text:"# egress, light, vent, safety",options:{color:"9AA3B8",breakLine:true}},
  {text:"# glazing all satisfied",options:{color:"9AA3B8"}},
]);
term(s,MX+6.18,2.0,5.95,4.4,"$ verify_windows(non_compliant)","F0A0AC",[
  {text:"ok  : False    n_failed : 6",options:{color:"FBB6C0",breakLine:true}},
  {text:"",options:{breakLine:true}},
  {text:"✗ egress_window        bed  (R310)",options:{color:"F0A0AC",breakLine:true}},
  {text:"✗ natural_light   4<12 bed  (R303)",options:{color:"F0A0AC",breakLine:true}},
  {text:"✗ natural_ventilation 0<6 bed",options:{color:"F0A0AC",breakLine:true}},
  {text:"✗ natural_light  4<24 living(R303)",options:{color:"F0A0AC",breakLine:true}},
  {text:"✗ natural_ventilation 4<12 living",options:{color:"F0A0AC",breakLine:true}},
  {text:"✗ safety_glazing sill 12in<18in",options:{color:"F0A0AC"}},
]);
s.addText("Every violation carries the measured value, the required value, and the IRC section — ready to feed a generator retry or a reviewer.",
  {x:MX,y:6.55,w:12,h:0.35,fontFace:BODY,fontSize:12,italic:true,color:MUTED,align:"center",margin:0});
footer(s,11);

// ============================================================ 12 RESEARCH
s=pres.addSlide(); s.background={color:INK};
s.addText("RESEARCH CONTRIBUTION",{x:MX,y:0.55,w:11,h:0.4,fontFace:MONO,fontSize:13,color:"F2C67A",charSpacing:3,bold:true,margin:0});
s.addText("Constraints-first residential daylight compliance",{x:MX,y:0.95,w:12,h:0.7,fontFace:HEAD,fontSize:26,color:WHITE,bold:true,margin:0});
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:2.0,w:5.95,h:2.5,fill:{color:INK2},line:{color:RED,width:1},rectRadius:0.08});
s.addText("Prevailing: generate-then-simulate",{x:MX+0.3,y:2.18,w:5.4,h:0.4,fontFace:HEAD,fontSize:15,color:"F0A0AC",bold:true,margin:0});
s.addText("An LLM / diffusion model proposes; a physically-based simulator scores the daylight afterwards. Stochastic, slow, can't constrain generation.",
  {x:MX+0.3,y:2.7,w:5.45,h:1.7,fontFace:BODY,fontSize:13,color:"CFD5E4",lineSpacingMultiple:1.1,valign:"top",margin:0});
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+6.18,y:2.0,w:5.95,h:2.5,fill:{color:INK2},line:{color:GREEN,width:1},rectRadius:0.08});
s.addText("Ours: a dual-use predicate",{x:MX+6.48,y:2.18,w:5.4,h:0.4,fontFace:HEAD,fontSize:15,color:"7BE0B0",bold:true,margin:0});
s.addText("The SAME deterministic, IRC-grounded predicate both constrains generation (correct-by-construction) AND proves compliance. Only possible because it's deterministic.",
  {x:MX+6.48,y:2.7,w:5.45,h:1.7,fontFace:BODY,fontSize:13,color:"CFD5E4",lineSpacingMultiple:1.1,valign:"top",margin:0});
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:4.75,w:12.13,h:1.05,fill:{color:"12141F"},line:{color:AMBERD,width:1},rectRadius:0.08});
s.addText([{text:"The claim: ",options:{color:"F2C67A",bold:true,fontFace:HEAD}},{text:"separate \"is it legal\" (provable) from \"is it nice\" (scored) — and reuse the legal predicate as a generator constraint. A clean paper angle in generative building design.",options:{color:"E6EAF3"}}],
  {x:MX+0.4,y:4.75,w:11.4,h:1.05,fontFace:BODY,fontSize:13.5,valign:"middle",margin:0});
s.addText("Grounding: IRC R310 (egress) · R303.1 (light/vent) · R308.4 (safety glazing)  ·  full memo: WINDOW_AGENT_RESEARCH.md",
  {x:MX,y:6.15,w:12,h:0.4,fontFace:MONO,fontSize:10.5,color:"8C93A8",margin:0});

// ============================================================ 13 ROOF: WHAT
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Roof Plan Agent","Deterministic geometry · Z3-self-verified · Cluster 4");
card(s,MX,1.95,5.95,2.15,ICE);
s.addText("Input  ← Elevation / Multi-floor (+ Window daylight)",{x:MX+0.3,y:2.1,w:5.4,h:0.35,fontFace:BODY,fontSize:12.5,color:TEALD,bold:true,margin:0});
s.addText("Output → roof polygons \"view_type\":\"roof\" → DXF Generator + PDF",{x:MX+0.3,y:2.5,w:5.5,h:0.35,fontFace:BODY,fontSize:12.5,color:TEALD,bold:true,margin:0});
s.addText([{text:"Generates: ",options:{bold:true,color:INK}},{text:"roof outline (matches footprint exactly), ridge, hips, per-plane pitch + drainage, heights.",options:{color:TEXT}}],
  {x:MX+0.3,y:2.95,w:5.45,h:1.0,fontFace:BODY,fontSize:12.5,valign:"top",lineSpacingMultiple:1.05,margin:0});
s.addText("Roof types",{x:MX+6.18,y:1.95,w:5,h:0.35,fontFace:HEAD,fontSize:15,color:INK,bold:true,margin:0});
["gable","hip","shed (mono-pitch)","flat (drained)"].forEach((t,i)=>{ const col=i%2,row=Math.floor(i/2);
  chip(s,MX+6.18+col*3.0,2.4+row*0.5,2.8,t,TEAL); });
s.addText("+ multi-floor STEPPED roofs (a lower shed over the garage), per-level roof types.",
  {x:MX+6.18,y:3.5,w:5.9,h:0.6,fontFace:BODY,fontSize:12,italic:true,color:MUTED,valign:"top",margin:0});
// self-verify note
card(s,MX,4.3,12.13,2.0,"FDF4E6",AMBER);
s.addText("Self-verifies before handoff (same propose→prove pattern as the generators)",{x:MX+0.35,y:4.45,w:11,h:0.4,fontFace:HEAD,fontSize:15,color:AMBERD,bold:true,margin:0});
["roof_matches_footprint","stepped_roof_downward","roof_eave_setback","pitch_specified","drainage_specified","skylight_within_roof"].forEach((r,i)=>{ const col=i%3,row=Math.floor(i/3);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+0.35+col*3.9,y:4.95+row*0.6,w:3.7,h:0.46,fill:{color:"FFFFFF"},line:{color:AMBERD,width:1},rectRadius:0.06});
  s.addText(r,{x:MX+0.35+col*3.9,y:4.95+row*0.6,w:3.7,h:0.46,fontFace:MONO,fontSize:10.5,color:AMBERD,bold:true,align:"center",valign:"middle",margin:0}); });
footer(s,13);

// ============================================================ 14 ROOF: DEMO + SKYLIGHT
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Roof demo + lighting integration","Sunroof placed from the Window Agent's daylight scores");
s.addImage({path:"output/roof_plan.png", x:MX, y:1.95, w:6.6, h:4.6, sizing:{type:"contain", w:6.6, h:4.6}});
card(s,7.5,1.95,5.23,2.35,ICE);
s.addText("The skylight rule",{x:7.75,y:2.1,w:4.8,h:0.35,fontFace:HEAD,fontSize:15,color:INK,bold:true,margin:0});
s.addText([
  {text:"Reads per-room daylight scores from the",options:{breakLine:true}},
  {text:"Window Agent → drops a sunroof over each",options:{breakLine:true}},
  {text:"UNDER-LIT top-floor room (score < 45), on",options:{breakLine:true}},
  {text:"its sunniest roof plane (prefers S/E/W).",options:{}},
],{x:7.75,y:2.55,w:4.8,h:1.7,fontFace:BODY,fontSize:12,color:TEXT,lineSpacingMultiple:1.08,valign:"top",margin:0});
term(s,7.5,4.45,5.23,2.05,null,null,[
  {text:"ROOF PLAN — VERIFIED ✓",options:{color:"9FE6C4",breakLine:true}},
  {text:"main   gable 5:12  ridge 28.8ft",options:{breakLine:true}},
  {text:"garage shed  5:12  (stepped, lower)",options:{breakLine:true}},
  {text:"sunroof → family_room (score 34)",options:{color:"F3D8A8",breakLine:true}},
  {text:"          on the E (sun) plane",options:{color:"F3D8A8"}},
]);
footer(s,14);

// ============================================================ 15 CONNECT + STATUS
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"How it connects · status","Two agents, one daylight-aware pipeline");
// mini flow
const fx=[["Window Agent","daylight scores +\nhard constraints",AMBER],["Roof Plan Agent","sunroof placement +\nroof geometry",TEAL],["Z3 Verifier","provable\ncompliance",GREEN],["DXF / PDF","permit\nartifacts",INK2]];
fx.forEach((b,i)=>{ const x=MX+i*3.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y:2.0,w:2.7,h:1.15,fill:{color:i==3?INK:ICE},line:{color:b[2],width:1.25},rectRadius:0.08,shadow:sh()});
  s.addText(b[0],{x,y:2.14,w:2.7,h:0.4,fontFace:HEAD,fontSize:13,color:i==3?"FFFFFF":INK,bold:true,align:"center",margin:0});
  s.addText(b[1],{x,y:2.55,w:2.7,h:0.55,fontFace:BODY,fontSize:10,color:i==3?"CFD5E4":MUTED,align:"center",margin:0});
  if(i<3) s.addShape(pres.shapes.LINE,{x:x+2.72,y:2.57,w:0.36,h:0,line:{color:MUTED,width:2,endArrowType:"triangle"}});
});
card(s,MX,3.6,5.95,2.85,"E9F7F0",GREEN);
s.addText("DONE",{x:MX+0.3,y:3.75,w:4,h:0.35,fontFace:MONO,fontSize:13,color:GREEN,bold:true,charSpacing:2,margin:0});
s.addText([
  {text:"Window constraint layer (egress/light/vent/glazing), deterministic + IRC-cited",options:{bullet:true,breakLine:true}},
  {text:"Roof agent: geometry, stepped roofs, pitch/drainage, DXF+SVG",options:{bullet:true,breakLine:true}},
  {text:"Skylight placement from daylight scores",options:{bullet:true,breakLine:true}},
  {text:"All Z3-self-verified; demos + docs written",options:{bullet:true}},
],{x:MX+0.32,y:4.2,w:5.4,h:2.1,fontFace:BODY,fontSize:12,color:TEXT,lineSpacingMultiple:1.03,paraSpaceAfter:5,valign:"top",margin:0});
card(s,MX+6.18,3.6,5.95,2.85,ICE);
s.addText("NEXT (coordination)",{x:MX+6.48,y:3.75,w:5,h:0.35,fontFace:MONO,fontSize:13,color:TEALD,bold:true,charSpacing:1,margin:0});
s.addText([
  {text:"Constraint Engine (Harshit): add a windows block + per-city thresholds",options:{bullet:true,breakLine:true}},
  {text:"Floor Plan (Prasad): emit fixture positions → promotes SOFT placement to HARD",options:{bullet:true,breakLine:true}},
  {text:"Confirm Aadi's exact daylight-score field name",options:{bullet:true,breakLine:true}},
  {text:"Optional: physically-based sim as an offline quality enrichment",options:{bullet:true}},
],{x:MX+6.5,y:4.2,w:5.4,h:2.1,fontFace:BODY,fontSize:12,color:TEXT,lineSpacingMultiple:1.03,paraSpaceAfter:5,valign:"top",margin:0});
footer(s,15);

pres.writeFile({fileName:"WindowRoof_Agents_Presentation.pptx"}).then(f=>console.log("WROTE",f));
