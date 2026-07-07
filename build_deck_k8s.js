// Kubernetes/Docker deployment deck — pptxgenjs
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Ojas";
pres.title = "House-Design Pipeline — Containerisation & Kubernetes";

const INK="0F2233", INK2="16314A", WHITE="FFFFFF", ICE="EAF1F6", ICE2="DCE7EE";
const TEAL="1C7293", TEALD="13506A", ORANGE="E8833A", GREEN="1FA971", RED="D6455D";
const TEXT="1F2D3A", MUTED="5E6E7C", BORDER="CFDBE4";
const HEAD="Trebuchet MS", BODY="Calibri", MONO="Consolas";
const W=13.33, H=7.5, MX=0.6;
const sh=()=>({type:"outer",color:"24313B",blur:9,offset:3,angle:135,opacity:0.18});

function footer(s,n){
  s.addText("Docker + Kubernetes  ·  House-Design Pipeline  ·  Ojas",{x:MX,y:H-0.42,w:9,h:0.3,fontFace:BODY,fontSize:9,color:MUTED,margin:0});
  s.addText(String(n),{x:W-1.0,y:H-0.42,w:0.4,h:0.3,fontFace:BODY,fontSize:9,color:MUTED,align:"right",margin:0});
}
function titleHead(s,kicker,title){
  s.addText(kicker.toUpperCase(),{x:MX,y:0.42,w:12,h:0.32,fontFace:MONO,fontSize:12,color:TEAL,charSpacing:2,bold:true,margin:0});
  s.addText(title,{x:MX,y:0.74,w:12.1,h:0.8,fontFace:HEAD,fontSize:28,color:INK,bold:true,margin:0});
}
function card(s,x,y,w,h,fill){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h,fill:{color:fill},line:{color:BORDER,width:1},rectRadius:0.08,shadow:sh()});
}
function box(s,x,y,w,h,fill,label,sub,txtc,bord){
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x,y,w,h,fill:{color:fill},line:{color:bord||BORDER,width:1.25},rectRadius:0.08,shadow:sh()});
  s.addText(label,{x:x+0.05,y:y+(sub?0.12:0),w:w-0.1,h:sub?0.45:h,fontFace:HEAD,fontSize:12.5,color:txtc,bold:true,align:"center",valign:sub?"top":"middle",margin:0});
  if(sub) s.addText(sub,{x:x+0.05,y:y+0.5,w:w-0.1,h:h-0.55,fontFace:BODY,fontSize:9.5,color:(fill===INK||fill===TEAL||fill===INK2||fill===ORANGE)?"CFE0E8":MUTED,align:"center",valign:"top",margin:0});
}
function arrow(s,x,y,w,col){ s.addShape(pres.shapes.LINE,{x,y,w,h:0,line:{color:col,width:2.5,endArrowType:"triangle"}}); }

// ============================================================ 1 TITLE
let s=pres.addSlide(); s.background={color:INK};
s.addShape(pres.shapes.OVAL,{x:10.6,y:-1.6,w:4.6,h:4.6,fill:{color:INK2}});
s.addShape(pres.shapes.OVAL,{x:11.8,y:4.8,w:3.6,h:3.6,fill:{color:INK2}});
s.addText("DEPLOYMENT TASK",{x:MX,y:1.5,w:11,h:0.4,fontFace:MONO,fontSize:14,color:"7FD0D6",charSpacing:3,bold:true,margin:0});
s.addText("Containerising & Scaling\nthe House-Design Pipeline",{x:MX,y:1.95,w:11.5,h:1.7,fontFace:HEAD,fontSize:40,color:WHITE,bold:true,lineSpacingMultiple:1.0,margin:0});
s.addText("Docker image  →  Kubernetes on AWS EC2  →  S3 + autoscaling",{x:MX,y:3.95,w:11,h:0.5,fontFace:BODY,fontSize:18,color:"BFD4DE",margin:0});
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:4.75,w:5.3,h:0.6,fill:{color:INK2},line:{color:TEAL,width:1.25},rectRadius:0.3});
s.addText("build  →  containerise  →  scale out",{x:MX,y:4.75,w:5.3,h:0.6,fontFace:MONO,fontSize:14,color:"CFE6EA",align:"center",valign:"middle",bold:true,margin:0});
s.addText("Ojas  ·  AI Gurukul  ·  PS-II",{x:MX,y:H-0.7,w:8,h:0.34,fontFace:BODY,fontSize:13,color:"7E94A0",margin:0});

// ============================================================ 2 TASK + MENTAL MODEL
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"The task","Run the pipeline as a scalable cloud service");
// left: decode
card(s,MX,1.9,6.0,4.75,ICE);
s.addText("What sir asked, decoded",{x:MX+0.3,y:2.05,w:5.5,h:0.4,fontFace:HEAD,fontSize:15,color:INK,bold:true,margin:0});
const decode=[
  ["EC2 → node","a virtual machine that, once K8s is installed, joins the cluster as a node"],
  ["one node → cluster","kubeadm init turns an EC2 into a cluster; more EC2s join as workers"],
  ["spin up pod → run image","K8s schedules a Pod → runs your Container → runs the Docker image"],
  ["more containers / no bottleneck","autoscaler adds Pods; the Service load-balances queries across them"],
  ["store image","push to a registry (ECR / Docker Hub) so the cluster can pull it"],
];
decode.forEach((d,i)=>{ const y=2.5+i*0.82;
  s.addShape(pres.shapes.OVAL,{x:MX+0.3,y:y+0.04,w:0.14,h:0.14,fill:{color:TEAL}});
  s.addText(d[0],{x:MX+0.55,y,w:5.3,h:0.3,fontFace:BODY,fontSize:12.5,color:INK,bold:true,margin:0});
  s.addText(d[1],{x:MX+0.55,y:y+0.3,w:5.3,h:0.5,fontFace:BODY,fontSize:10.5,color:MUTED,margin:0});
});
// right: nested stack
s.addText("The layered mental model",{x:7.0,y:1.95,w:5.8,h:0.35,fontFace:HEAD,fontSize:14,color:MUTED,italic:true,margin:0});
const nest=[
  [7.0,2.35,5.8,4.3,INK,"AWS Cloud"],
  [7.45,2.92,4.9,3.65,INK2,"EC2 instance  (virtual machine)"],
  [7.9,3.49,4.0,3.0,TEALD,"Kubernetes Node"],
  [8.35,4.06,3.1,2.35,TEAL,"Pod"],
  [8.8,4.63,2.2,1.7,ORANGE,"Container"],
];
nest.forEach((b,i)=>{
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:b[0],y:b[1],w:b[2],h:b[3],fill:{color:b[4]},line:{color:"FFFFFF",width:1},rectRadius:0.07});
  s.addText(b[5],{x:b[0]+0.15,y:b[1]+0.1,w:b[2]-0.3,h:0.32,fontFace:BODY,fontSize:i>=3?11:11.5,color:"FFFFFF",bold:true,align:i>=4?"center":"left",margin:0});
});
s.addText("our Docker image\nruns here",{x:8.9,y:5.25,w:2.0,h:0.9,fontFace:BODY,fontSize:10,color:"FFF1E6",align:"center",italic:true,margin:0});
footer(s,2);

// ============================================================ 3 ARCHITECTURE
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Architecture","Where every piece sits at run time");
box(s,MX,3.05,1.7,1.05,ICE2,"Client",null,INK);
arrow(s,MX+1.72,3.57,0.5,TEALD);
box(s,2.85,2.95,2.4,1.25,TEAL,"Service","NodePort :30080\nload-balancer","FFFFFF",TEALD);
// fan to 3 pods
[2.05,3.15,4.25].forEach((py,i)=>{
  s.addShape(pres.shapes.LINE,{x:5.27,y:3.57,w:0.83,h:(py+0.45)-3.57,line:{color:TEALD,width:2,endArrowType:"triangle"}});
});
[2.05,3.15,4.25].forEach((py,i)=>{ box(s,6.1,py,2.6,0.95,INK,`Pod ${i+1}`,"container · 1 Z3","FFFFFF",ORANGE); });
s.addText("HPA scales pods 2 → 8",{x:6.1,y:5.35,w:2.6,h:0.3,fontFace:BODY,fontSize:10.5,color:ORANGE,bold:true,align:"center",margin:0});
// S3 + ECR on right
box(s,9.55,2.05,3.2,1.15,ICE2,"S3 bucket","city-code rule files\n(model artifacts)",INK);
box(s,9.55,4.05,3.2,1.15,ICE2,"ECR registry","stores the Docker image",INK);
// one representative arrow each (cleaner than one per pod)
s.addShape(pres.shapes.LINE,{x:8.72,y:3.45,w:0.83,h:-0.75,line:{color:GREEN,width:1.75,endArrowType:"triangle"}});
s.addText("pull codes",{x:8.78,y:2.95,w:1.4,h:0.3,fontFace:BODY,fontSize:9,color:GREEN,bold:true,margin:0});
s.addShape(pres.shapes.LINE,{x:9.55,y:4.55,w:-0.83,h:-0.6,line:{color:MUTED,width:1.75,dashType:"dash",endArrowType:"triangle"}});
s.addText("image",{x:8.78,y:4.5,w:0.9,h:0.3,fontFace:BODY,fontSize:9,color:MUTED,bold:true,margin:0});
card(s,MX,5.9,12.13,0.75,ICE);
s.addText([
  {text:"Read it as: ",options:{bold:true,color:TEAL}},
  {text:"a query hits the Service, which load-balances it to one of N identical Pods; each Pod runs the container that pulled its city-code rules from S3 at startup.",options:{color:TEXT}},
],{x:MX+0.3,y:5.9,w:11.6,h:0.75,fontFace:BODY,fontSize:12.5,valign:"middle",margin:0});
footer(s,3);

// ============================================================ 4 WHAT I BUILT (PROOF)
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Done locally","Built, containerised, and verified — today");
// terminal card
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:1.95,w:7.2,h:3.5,fill:{color:"0B1822"},line:{color:TEALD,width:1},rectRadius:0.07,shadow:sh()});
s.addText([
  {text:"$ docker build -t house-pipeline:v1 .",options:{color:"7FD0D6",breakLine:true}},
  {text:"$ docker run -d -p 8000:8000 house-pipeline:v1",options:{color:"7FD0D6",breakLine:true}},
  {text:"",options:{breakLine:true}},
  {text:"$ curl .../optimize?city=bellevue",options:{color:"E6EEF2",breakLine:true}},
  {text:'  { "max_buildable_area_sqft": 2568.0 }',options:{color:"9FE6C4",breakLine:true}},
  {text:"",options:{breakLine:true}},
  {text:"$ curl -X POST .../generate -d '{\"city\":\"seattle\"}'",options:{color:"E6EEF2",breakLine:true}},
  {text:'  { "interior": { "rooms": 8, "verified": true },',options:{color:"9FE6C4",breakLine:true}},
  {text:'    "took_ms": 39.6 }',options:{color:"9FE6C4"}},
],{x:MX+0.3,y:2.2,w:6.7,h:3.0,fontFace:MONO,fontSize:11.5,lineSpacingMultiple:1.12,valign:"top",margin:0});
// stat cards
const stats=[["image","builds clean on python:3.11-slim",GREEN],["8 rooms","interior Z3-verified, 0 violations",TEAL],["~40 ms","per full /generate request",ORANGE]];
stats.forEach((st,i)=>{ const y=1.95+i*1.18;
  card(s,8.1,y,4.6,1.0,ICE);
  s.addText(st[0],{x:8.35,y:y+0.12,w:2.0,h:0.7,fontFace:HEAD,fontSize:22,color:st[2],bold:true,valign:"middle",margin:0});
  s.addText(st[1],{x:10.0,y:y,w:2.55,h:1.0,fontFace:BODY,fontSize:12,color:TEXT,valign:"middle",margin:0});
});
card(s,MX,5.65,12.13,1.0,ICE2);
s.addText([
  {text:"Endpoints live:  ",options:{bold:true,color:INK}},
  {text:"/health   /cities   /optimize   /verify   /generate",options:{fontFace:MONO,color:TEALD,bold:true}},
  {text:"   — the same image will run unchanged inside a Kubernetes pod.",options:{color:MUTED}},
],{x:MX+0.3,y:5.65,w:11.6,h:1.0,fontFace:BODY,fontSize:13,valign:"middle",margin:0});
footer(s,4);

// ============================================================ 5 BUG & FIX
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"A real bug I hit & fixed","Z3 is not thread-safe — found it under load");
// before
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:2.0,w:5.95,h:2.7,fill:{color:"FBECEE"},line:{color:RED,width:1.25},rectRadius:0.08});
s.addText("BEFORE",{x:MX+0.3,y:2.18,w:4,h:0.35,fontFace:MONO,fontSize:12,color:RED,bold:true,charSpacing:2,margin:0});
s.addText([
  {text:"10 concurrent /generate requests",options:{bold:true,breakLine:true}},
  {text:"→ multiple threads call Z3 at once",options:{breakLine:true}},
  {text:"→ ASSERTION VIOLATION  (ast.cpp)",options:{color:RED,fontFace:MONO,breakLine:true}},
  {text:"→ pod segfaults, exit 139  💥",options:{color:RED,bold:true}},
],{x:MX+0.3,y:2.6,w:5.4,h:2.0,fontFace:BODY,fontSize:13.5,color:TEXT,lineSpacingMultiple:1.15,valign:"top",margin:0});
// after
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+6.18,y:2.0,w:5.95,h:2.7,fill:{color:"E9F7F0"},line:{color:GREEN,width:1.25},rectRadius:0.08});
s.addText("AFTER",{x:MX+6.48,y:2.18,w:4,h:0.35,fontFace:MONO,fontSize:12,color:GREEN,bold:true,charSpacing:2,margin:0});
s.addText([
  {text:"threading.Lock() serialises Z3 calls",options:{fontFace:MONO,color:TEALD,breakLine:true}},
  {text:"→ 60 requests, 12 concurrent",options:{bold:true,breakLine:true}},
  {text:"→ all 200, pod stays healthy ✓",options:{color:GREEN,bold:true,breakLine:true}},
  {text:"→ correctness over raw speed",options:{color:MUTED}},
],{x:MX+6.48,y:2.6,w:5.4,h:2.0,fontFace:BODY,fontSize:13.5,color:TEXT,lineSpacingMultiple:1.15,valign:"top",margin:0});
// insight
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:5.0,w:12.13,h:1.55,fill:{color:INK},line:{color:TEALD,width:1},rectRadius:0.08,shadow:sh()});
s.addText([
  {text:"The insight:  ",options:{fontFace:HEAD,bold:true,color:"7FD0D6"}},
  {text:"one pod can only run Z3 single-threaded — so you ",options:{color:WHITE}},
  {text:"scale with more pods, not more threads.",options:{color:ORANGE,bold:true}},
  {text:"  That's exactly what Kubernetes (HPA + Service) is for.",options:{color:"CFE0E8"}},
],{x:MX+0.4,y:5.0,w:11.4,h:1.55,fontFace:BODY,fontSize:15,valign:"middle",lineSpacingMultiple:1.05,margin:0});
footer(s,5);

// ============================================================ 6 SCALING
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"How it scales","“So querying doesn't bottleneck” — answered");
// Service banner (full width) -> down arrow -> pod strip
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:1.9,w:12.13,h:0.62,fill:{color:TEAL},line:{color:TEALD,width:1},rectRadius:0.08,shadow:sh()});
s.addText("Service  ·  NodePort :30080  ·  load-balances every query across ALL pods",{x:MX,y:1.9,w:12.13,h:0.62,fontFace:HEAD,fontSize:14,color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
s.addShape(pres.shapes.LINE,{x:W/2,y:2.56,w:0,h:0.16,line:{color:TEALD,width:2.5,endArrowType:"triangle"}});
const sx=[MX,3.0,5.4,7.8];
sx.forEach((px,i)=>{ box(s,px,2.8,2.1,0.95,INK,`Pod ${i+1}`,"1 Z3","FFFFFF",ORANGE); });
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:10.2,y:2.8,w:2.1,h:0.95,fill:{color:"FFFFFF"},line:{color:ORANGE,width:1.5,dashType:"dash"},rectRadius:0.08});
s.addText("… up to 8",{x:10.2,y:2.8,w:2.1,h:0.95,fontFace:HEAD,fontSize:13,color:ORANGE,bold:true,align:"center",valign:"middle",margin:0});
s.addText("HPA adds / removes pods automatically as CPU rises & falls   (min 2 → max 8)",{x:MX,y:3.88,w:12.13,h:0.35,fontFace:BODY,fontSize:12.5,color:ORANGE,bold:true,align:"center",margin:0});
const pts=[
  ["1 pod","handles ≈ 1 query at a time (~40 ms) and never crashes — Z3 is serialised"],
  ["N pods","handle ≈ N queries in parallel — throughput scales linearly with pod count"],
  ["Service","spreads incoming queries so no single pod is ever the bottleneck"],
  ["HPA","watches CPU and changes the pod count automatically — no human in the loop"],
];
pts.forEach((p,i)=>{ const y=4.42+i*0.56;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y,w:1.9,h:0.46,fill:{color:ICE},line:{color:TEAL,width:1},rectRadius:0.06});
  s.addText(p[0],{x:MX,y,w:1.9,h:0.46,fontFace:MONO,fontSize:12,color:TEALD,bold:true,align:"center",valign:"middle",margin:0});
  s.addText(p[1],{x:MX+2.1,y,w:10.0,h:0.46,fontFace:BODY,fontSize:12.5,color:TEXT,valign:"middle",margin:0});
});
footer(s,6);

// ============================================================ 7 K8S OBJECTS
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"The Kubernetes objects","Five small YAML files describe the whole deployment");
const objs=[
  ["Namespace","an isolated space (house-pipeline) for all our objects",TEAL],
  ["ConfigMap","env config: S3 bucket, region, city-code prefix",TEAL],
  ["Deployment","runs N replica pods of the image, with /health probes + CPU/RAM limits",ORANGE],
  ["Service","NodePort :30080 — one stable address, load-balances across pods",TEAL],
  ["HorizontalPodAutoscaler","2 → 8 pods automatically at 70% CPU",ORANGE],
];
objs.forEach((o,i)=>{ const y=1.95+i*0.82;
  card(s,MX,y,12.13,0.72,i%2?ICE2:ICE);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+0.2,y:y+0.13,w:3.3,h:0.46,fill:{color:o[2]},line:{color:o[2],width:1},rectRadius:0.06});
  s.addText(o[0],{x:MX+0.2,y:y+0.13,w:3.3,h:0.46,fontFace:MONO,fontSize:12.5,color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
  s.addText(o[1],{x:MX+3.75,y,w:8.2,h:0.72,fontFace:BODY,fontSize:13,color:TEXT,valign:"middle",margin:0});
});
s.addText("Deploy them all with one command:   kubectl apply -f k8s/",{x:MX,y:6.15,w:12,h:0.4,fontFace:MONO,fontSize:13,color:TEALD,bold:true,align:"center",margin:0});
footer(s,7);

// ============================================================ 8 AWS PATH
s=pres.addSlide(); s.background={color:WHITE};
titleHead(s,"Path to AWS","Six steps from local image to live cluster");
const steps=[
  ["Push image","tag & push house-pipeline:v1 to ECR"],
  ["Build cluster","EC2 ×2 + kubeadm init/join + Calico CNI"],
  ["S3 + IAM","upload city codes; let worker nodes read the bucket"],
  ["metrics-server","install it so the HPA can read CPU"],
  ["kubectl apply","namespace → configmap → deployment → service → hpa"],
  ["Load-test","hey/k6 the endpoint, watch kubectl get hpa scale up"],
];
const cw=(12.13-2*0.3)/3;
steps.forEach((st,i)=>{ const col=i%3,row=Math.floor(i/3);
  const x=MX+col*(cw+0.3), y=2.1+row*2.05;
  card(s,x,y,cw,1.8,ICE);
  s.addShape(pres.shapes.OVAL,{x:x+0.3,y:y+0.28,w:0.6,h:0.6,fill:{color:i<4?TEAL:ORANGE}});
  s.addText(String(i+1),{x:x+0.3,y:y+0.28,w:0.6,h:0.6,fontFace:HEAD,fontSize:22,color:"FFFFFF",bold:true,align:"center",valign:"middle",margin:0});
  s.addText(st[0],{x:x+1.05,y:y+0.34,w:cw-1.3,h:0.5,fontFace:HEAD,fontSize:16,color:INK,bold:true,margin:0});
  s.addText(st[1],{x:x+0.32,y:y+1.0,w:cw-0.6,h:0.7,fontFace:BODY,fontSize:12,color:MUTED,margin:0,lineSpacingMultiple:1.0});
});
footer(s,8);

// ============================================================ 9 STATUS + DEMO
s=pres.addSlide(); s.background={color:INK};
s.addText("STATUS & DEMO",{x:MX,y:0.55,w:11,h:0.4,fontFace:MONO,fontSize:13,color:"7FD0D6",charSpacing:3,bold:true,margin:0});
s.addText("Done today, and how to show it",{x:MX,y:0.92,w:11.5,h:0.7,fontFace:HEAD,fontSize:28,color:WHITE,bold:true,margin:0});
// done
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:1.95,w:5.95,h:2.95,fill:{color:"12303A"},line:{color:GREEN,width:1},rectRadius:0.08});
s.addText("DONE  ✓",{x:MX+0.3,y:2.12,w:4,h:0.35,fontFace:MONO,fontSize:13,color:"7BE0B0",bold:true,charSpacing:2,margin:0});
s.addText([
  {text:"FastAPI service over PS1+PS2 pipeline",options:{bullet:true,breakLine:true}},
  {text:"Docker image built & run, all endpoints OK",options:{bullet:true,breakLine:true}},
  {text:"Thread-safety bug found & fixed (load-tested)",options:{bullet:true,breakLine:true}},
  {text:"All 5 K8s manifests + S3 artifact loader",options:{bullet:true,breakLine:true}},
  {text:"DEPLOY.md runbook (decodes the brief)",options:{bullet:true}},
],{x:MX+0.35,y:2.6,w:5.4,h:2.2,fontFace:BODY,fontSize:12.5,color:"E6EEF2",lineSpacingMultiple:1.05,paraSpaceAfter:5,valign:"top",margin:0});
// next
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX+6.18,y:1.95,w:5.95,h:2.95,fill:{color:"12303A"},line:{color:TEAL,width:1},rectRadius:0.08});
s.addText("NEXT  (needs AWS)",{x:MX+6.48,y:2.12,w:5,h:0.35,fontFace:MONO,fontSize:13,color:"7FD0D6",bold:true,charSpacing:1,margin:0});
s.addText([
  {text:"Push image to ECR",options:{bullet:true,breakLine:true}},
  {text:"Stand up EC2 + kubeadm cluster",options:{bullet:true,breakLine:true}},
  {text:"S3 bucket + worker-node IAM role",options:{bullet:true,breakLine:true}},
  {text:"kubectl apply -f k8s/  + metrics-server",options:{bullet:true,breakLine:true}},
  {text:"Load-test & watch the HPA scale",options:{bullet:true}},
],{x:MX+6.53,y:2.6,w:5.4,h:2.2,fontFace:BODY,fontSize:12.5,color:"E6EEF2",lineSpacingMultiple:1.05,paraSpaceAfter:5,valign:"top",margin:0});
// demo command
s.addShape(pres.shapes.ROUNDED_RECTANGLE,{x:MX,y:5.15,w:12.13,h:1.4,fill:{color:"0B1822"},line:{color:ORANGE,width:1.5},rectRadius:0.1});
s.addText("LIVE DEMO",{x:MX+0.4,y:5.3,w:3,h:0.3,fontFace:MONO,fontSize:11,color:ORANGE,bold:true,charSpacing:2,margin:0});
s.addText([
  {text:"$ ",options:{color:GREEN}},
  {text:"docker run -d -p 8000:8000 house-pipeline:v1",options:{color:"EDF3F5"}},
  {text:"   then   ",options:{color:MUTED}},
  {text:"curl -X POST localhost:8000/generate -d '{\"city\":\"seattle\"}'",options:{color:"EDF3F5"}},
],{x:MX+0.4,y:5.65,w:11.4,h:0.7,fontFace:MONO,fontSize:13.5,bold:true,valign:"middle",margin:0});

pres.writeFile({fileName:"HousePipeline_K8s_Deployment.pptx"}).then(f=>console.log("WROTE",f));
