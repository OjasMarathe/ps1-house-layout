/**
 * PS-II Seminar 1 — 5-minute deck (8 slides). Output: AIGurukul_Ojas_Seminar1.pptx
 */
const path = require("path");
const PG = require("pptxgenjs");
const NAVY="1E2761",ICE="CADCFC",WHITE="FFFFFF",GREEN="2C5F2D",ORANGE="C0392B",TEAL="0E7490",MUTED="64748B",DARK="0F172A";
const W=13.333,H=7.5,PROJ="/Users/ojas/ps1-house-layout",IMG=n=>path.join(PROJ,"output/slides",n);
const pres=new PG(); pres.layout="LAYOUT_WIDE"; pres.author="Ojas Marathe";
let pg=0; const fs=[];
const mk=()=>{const s=pres.addSlide();pg++;s.__p=pg;return s;};
const foot=s=>fs.push(s);
function stamp(){for(const s of fs){s.addText(`${s.__p} / ${pg}`,{x:W-1.2,y:H-.42,w:.9,h:.3,fontSize:10,color:MUTED,fontFace:"Calibri",align:"right"});s.addText("PS-II Seminar 1 · Ojas",{x:.5,y:H-.42,w:6,h:.3,fontSize:10,color:MUTED,fontFace:"Calibri"});}}
function title(s,t,sub){s.addText(t,{x:.6,y:.36,w:12.1,h:.8,fontSize:30,bold:true,color:NAVY,fontFace:"Cambria",margin:0});if(sub)s.addText(sub,{x:.6,y:1.14,w:12.1,h:.5,fontSize:15,color:MUTED,italic:true,fontFace:"Calibri",margin:0});}
function stat(s,x,y,w,h,v,l,a=NAVY){s.addShape(pres.shapes.RECTANGLE,{x,y,w,h,fill:{color:WHITE},line:{color:ICE,width:1.5}});s.addShape(pres.shapes.RECTANGLE,{x,y,w:.08,h,fill:{color:a},line:{color:a,width:0}});s.addText(v,{x:x+.22,y:y+.12,w:w-.36,h:h*.56,fontSize:26,bold:true,color:a,fontFace:"Cambria",valign:"middle",margin:0});s.addText(l,{x:x+.22,y:y+h*.56,w:w-.36,h:h*.4,fontSize:10.5,color:MUTED,fontFace:"Calibri",margin:0});}

// S1 Title
{const s=mk();s.background={color:NAVY};
s.addShape(pres.shapes.RECTANGLE,{x:0,y:0,w:.35,h:H,fill:{color:TEAL},line:{color:TEAL,width:0}});
s.addText("PS-II · SEMINAR 1",{x:1,y:1.4,w:11,h:.5,fontSize:20,color:ICE,fontFace:"Cambria",charSpacing:10,margin:0});
s.addText("Neuro-Symbolic Floor Plans",{x:1,y:2.05,w:11.6,h:1.2,fontSize:48,bold:true,color:WHITE,fontFace:"Cambria",margin:0});
s.addText("An LLM draws the house; the Z3 solver proves every building rule",{x:1,y:3.45,w:11.6,h:.8,fontSize:19,italic:true,color:ICE,fontFace:"Calibri",margin:0});
s.addShape(pres.shapes.RECTANGLE,{x:1,y:5.5,w:4,h:.04,fill:{color:TEAL},line:{color:TEAL,width:0}});
s.addText("Ojas Marathe   ·   AI Gurukul   ·   June 2026",{x:1,y:5.6,w:11,h:.5,fontSize:14,color:ICE,fontFace:"Calibri",margin:0});
s.addText("Z3 SMT · MILP (PuLP+CBC) · Gemini / Llama (Groq) · ezdxf · Streamlit",{x:1,y:6.05,w:11.8,h:.5,fontSize:13,color:WHITE,fontFace:"Consolas",margin:0});}

// S2 Problem + idea
{const s=mk();s.background={color:WHITE};
title(s,"The problem & the idea","Generate a code-compliant house drawing — and prove it's correct");
s.addText([
 {text:"Two problems on one constrained L-shaped plot:",options:{color:DARK,breakLine:true}},
 {text:"  • Exterior: house outline + door (Seattle Building Code)",options:{color:DARK,breakLine:true}},
 {text:"  • Interior: 3 bed + 2 bath + kitchen + living (IRC)",options:{color:DARK,breakLine:true}},
 {text:" ",options:{breakLine:true}},
 {text:"The idea (neuro-symbolic): ",options:{bold:true,color:TEAL}},
 {text:"LLMs generate well but hallucinate geometry. So the LLM proposes, and ",options:{color:DARK}},
 {text:"the Z3 SMT solver is the deterministic judge",options:{bold:true,color:NAVY}},
 {text:" — generated code is never executed.",options:{color:DARK}},
],{x:.6,y:2.0,w:7.0,h:4.4,fontSize:15,fontFace:"Calibri",margin:0});
s.addImage({path:IMG("plot_only.png"),x:7.9,y:1.9,w:5.0,h:5.0,sizing:{type:"contain",w:5.0,h:5.0}});
foot(s);}

// S3 Pipeline
{const s=mk();s.background={color:WHITE};
title(s,"The pipeline — two phases, one principle","Generator proposes · Z3 proves · human/LLM explains");
const bY=2.1,bH=3.2;
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:.6,y:bY,w:5.7,h:bH,fill:{color:"F8FAFC"},line:{color:NAVY,width:1.5},rectRadius:.12});
s.addText("PHASE 1 — EXTERIOR",{x:.85,y:bY+.15,w:5.2,h:.4,fontSize:13,bold:true,color:NAVY,charSpacing:3,fontFace:"Calibri",margin:0});
s.addText([{text:"Z3 Optimize → provable max-area footprint",options:{bullet:true,breakLine:true}},{text:"Gemini draws outline; parser extracts coords",options:{bullet:true,breakLine:true}},{text:"Z3 verifies 9 SBC rules",options:{bullet:true,breakLine:true,bold:true,color:NAVY}},{text:"Llama (Groq) feedback → loop",options:{bullet:true}}],{x:.95,y:bY+.6,w:5.1,h:2,fontSize:13,color:DARK,fontFace:"Calibri",margin:0});
s.addShape(pres.shapes.LINE,{x:6.35,y:bY+bH/2,w:.6,h:0,line:{color:NAVY,width:2.5,endArrowType:"triangle"}});
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:7.05,y:bY,w:5.7,h:bH,fill:{color:"F0FDFA"},line:{color:TEAL,width:1.5},rectRadius:.12});
s.addText("PHASE 2 — INTERIOR",{x:7.3,y:bY+.15,w:5.2,h:.4,fontSize:13,bold:true,color:TEAL,charSpacing:3,fontFace:"Calibri",margin:0});
s.addText([{text:"Seed: tiled template OR MILP/CBC solve",options:{bullet:true,breakLine:true}},{text:"Conversational edits: chips + free-text (LLM)",options:{bullet:true,breakLine:true}},{text:"Z3 verifies the interior rule set",options:{bullet:true,breakLine:true,bold:true,color:NAVY}},{text:"Only VALID layouts are shown",options:{bullet:true}}],{x:7.4,y:bY+.6,w:5.1,h:2,fontSize:13,color:DARK,fontFace:"Calibri",margin:0});
s.addText("Never executes LLM code — geometry is parsed; the .dxf is rendered from Z3-verified numbers.",{x:.6,y:5.7,w:12.2,h:.6,fontSize:13.5,italic:true,color:MUTED,fontFace:"Calibri",margin:0});
foot(s);}

// S4 Exterior result
{const s=mk();s.background={color:WHITE};
title(s,"Exterior — Z3 makes “maximise area” a hard rule","Converged to 90% of the provable maximum in 2 iterations");
stat(s,.6,2.0,3.9,1.5,"6,420","PLOT (sq ft)",NAVY);
stat(s,4.7,2.0,3.9,1.5,"4,060","Z3 MAX HOUSE",NAVY);
stat(s,.6,3.7,3.9,1.5,"3,654","BUILT — 90% of max",GREEN);
stat(s,4.7,3.7,3.9,1.5,"2","ITERATIONS",GREEN);
s.addText("Z3 Optimize proves the largest legal house; the verifier then enforces ≥90% of it — so the LLM must push to the legal limit, and Z3 caught & corrected a 57% first attempt.",
 {x:.6,y:5.5,w:8.0,h:1.2,fontSize:13,color:DARK,fontFace:"Calibri",margin:0});
s.addImage({path:IMG("labeled_result.png"),x:8.7,y:1.9,w:4.2,h:5.0,sizing:{type:"contain",w:4.2,h:5.0}});
foot(s);}

// S5 Interior + 3 generators
{const s=mk();s.background={color:WHITE};
title(s,"Interior — three generators, one verifier","Templates (instant) · MILP/cutting-plane · LLM (conversational)");
s.addImage({path:IMG("milp_result.png"),x:.5,y:1.9,w:5.0,h:4.9,sizing:{type:"contain",w:5.0,h:4.9}});
s.addText([
 {text:"Templates",options:{bold:true,color:TEAL,breakLine:true}},
 {text:"Hand-designed tiled layouts; instant, always valid.",options:{color:DARK,breakLine:true}},
 {text:" ",options:{breakLine:true}},
 {text:"MILP / CBC (cutting-plane)",options:{bold:true,color:NAVY,breakLine:true}},
 {text:"Big-M non-overlap, solved by branch-and-cut — generate-and-guarantee.",options:{color:DARK,breakLine:true}},
 {text:" ",options:{breakLine:true}},
 {text:"LLM (conversational)",options:{bold:true,color:GREEN,breakLine:true}},
 {text:"Places rooms from a description; Z3 confirms; loop on failure.",options:{color:DARK,breakLine:true}},
 {text:" ",options:{breakLine:true}},
 {text:"All verified vs IRC sizes, non-overlap, door-in-living, connectivity — 100% tiled.",options:{italic:true,color:TEAL}},
],{x:6.0,y:1.95,w:6.8,h:4.9,fontSize:14,fontFace:"Calibri",margin:0});
foot(s);}

// S6 Conversational studio
{const s=mk();s.background={color:WHITE};
title(s,"A conversational design studio (Streamlit)","“Describe it in words, the solver proves it” — human-in-the-loop");
s.addImage({path:IMG("studio_layout.png"),x:.5,y:1.9,w:5.1,h:4.9,sizing:{type:"contain",w:5.1,h:4.9}});
s.addText([
 {text:"Pick a vibe → instant tiled plan.",options:{bullet:true,breakLine:true}},
 {text:"Quick-changes (bigger bedrooms/kitchen…) = deterministic, always valid.",options:{bullet:true,breakLine:true}},
 {text:"Free-text (“bedrooms in the three corners, kitchen between the top two”) → the LLM lays it out; Z3 checks it.",options:{bullet:true,breakLine:true}},
 {text:"A plan is shown only if Z3 fully accepts it.",options:{bullet:true,breakLine:true,bold:true,color:NAVY}},
 {text:"Live Z3 badge + one-click .dxf download.",options:{bullet:true}},
],{x:6.0,y:2.0,w:6.8,h:4.6,fontSize:14.5,fontFace:"Calibri",margin:0});
foot(s);}

// S7 Findings
{const s=mk();s.background={color:WHITE};
title(s,"Findings — problems hit & fixed, and the models","Most surfaced from live testing");
const d=[[{text:"Problem",options:{bold:true,color:WHITE,fill:{color:ORANGE}}},{text:"Fix",options:{bold:true,color:WHITE,fill:{color:GREEN}}}],
 ["~35% wasted as one “corridor” block","tiling templates (100%) + ≥4-ft halls"],
 ["Bedrooms long / vibes looked identical","square-ish, 4 distinct tiled templates"],
 ["Chat left invalid plans","commit only if Z3-valid (else revert)"],
 ["Gemini quota (20/day) exhausted","swap generator to Llama 3.3 (Groq)"]];
s.addTable(d,{x:.6,y:2.0,w:12.2,h:2.4,fontSize:13,fontFace:"Calibri",color:DARK,border:{pt:.5,color:ICE},rowH:.55,colW:[6.1,6.1],valign:"middle"});
s.addText([
 {text:"Models: ",options:{bold:true,color:NAVY}},
 {text:"Gemini 2.5 Flash — best spatial reasoning, but 20 req/day cap.  Llama 3.3 (Groq) — fast, huge quota, weaker layouts.  Kimi K2 — 404, never ran.",options:{color:DARK,breakLine:true}},
 {text:" ",options:{breakLine:true}},
 {text:"Key observation: ",options:{bold:true,color:TEAL}},
 {text:"LLMs are good at intent, weak at constraint-preserving edits — so deterministic for simple edits, LLM for descriptions, Z3 as the always-on judge (which let us swap models freely).",options:{color:DARK}},
],{x:.6,y:4.7,w:12.2,h:2.0,fontSize:13.5,fontFace:"Calibri",margin:0});
foot(s);}

// S8 Conclusions
{const s=mk();s.background={color:NAVY};
s.addText("Conclusions & what's next",{x:.8,y:.6,w:12,h:1,fontSize:36,bold:true,color:WHITE,fontFace:"Cambria",margin:0});
s.addShape(pres.shapes.RECTANGLE,{x:.8,y:1.5,w:3,h:.04,fill:{color:TEAL},line:{color:TEAL,width:0}});
const tk=[
 ["Z3 is the judge — that's the whole point","Reproducible, citable verdicts; lets us swap any generator (LLM / MILP / templates) and still guarantee a code-valid plan."],
 ["Generate-and-guarantee + human-in-the-loop","The solver owns compliance; the human steers comfort through a conversation."],
 ["What's next","Multi-floor · roof-plan (straight skeleton) · 3D & elevations · persistence/DB · MCP services · multi-jurisdiction codes."],
];
let y=2.0;
for(const t of tk){s.addText(t[0],{x:.8,y,w:11.8,h:.5,fontSize:18,bold:true,color:WHITE,fontFace:"Cambria",margin:0});s.addText(t[1],{x:.8,y:y+.5,w:11.8,h:.7,fontSize:13.5,color:ICE,fontFace:"Calibri",margin:0});y+=1.45;}
s.addText("Thank you — questions?",{x:.8,y:H-.7,w:12,h:.4,fontSize:14,italic:true,color:ICE,fontFace:"Calibri",margin:0});}

stamp();
pres.writeFile({fileName:path.join(PROJ,"AIGurukul_Ojas_Seminar1.pptx")}).then(p=>console.log("wrote",p)).catch(e=>{console.error(e);process.exit(1);});
