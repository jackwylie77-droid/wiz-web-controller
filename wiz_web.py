from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pywizlight import wizlight, PilotBuilder

BULB_IP = "192.168.1.100" # replace with your ligts IP

app = FastAPI()
light = wizlight(BULB_IP)

power_on = True
current_rgb = [120, 180, 255]

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>WiZ Aurora (Safe)</title>

<style>
:root {
    --aurora-r: 120;
    --aurora-g: 180;
    --aurora-b: 255;
}

html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden;
    font-family: Arial, sans-serif;
}

body {
    background: radial-gradient(circle at bottom, #050812, #02040a);
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
}

#aurora {
    position: fixed;
    inset: -30%;
    pointer-events: none;
    filter: blur(80px);
    z-index: -2;
}

.aurora-stroke {
    position: absolute;
    width: 160%;
    left: -30%;
    background: linear-gradient(
        to right,
        rgba(var(--aurora-r),var(--aurora-g),var(--aurora-b),0) 0%,
        rgba(var(--aurora-r),var(--aurora-g),var(--aurora-b),0.35) 40%,
        rgba(var(--aurora-r),var(--aurora-g),var(--aurora-b),0.55) 50%,
        rgba(var(--aurora-r),var(--aurora-g),var(--aurora-b),0.35) 60%,
        rgba(var(--aurora-r),var(--aurora-g),var(--aurora-b),0) 100%
    );
    transform-origin: center;
    will-change: transform, height, opacity;
}

.panel {
    width: 360px;
    padding: 28px;
    border-radius: 20px;
    background: rgba(20,28,60,0.35);
    backdrop-filter: blur(20px) saturate(120%);
    box-shadow:
        0 0 40px rgba(120,180,255,0.15),
        inset 0 0 0 1px rgba(255,255,255,0.08);
    text-align: center;
    z-index: 2;
}

button {
    font-size: 16px;
    padding: 12px 18px;
    margin: 6px;
    border-radius: 10px;
    border: none;
    cursor: pointer;
}

.red { background:#ff3b3b; }
.green { background:#3bff6b; }
.blue { background:#3b6bff; }
.white { background:#f5f5f5; color:black; }
.on { background:#ccc; color:black; }
.off { background:black; color:white; }

/* Accessibility: reduce motion */
@media (prefers-reduced-motion: reduce) {
    #aurora { display: none; }
}
</style>
</head>

<body>

<div id="aurora"></div>

<div class="panel">
    <h2>💡 WiZ Light</h2>

    <button class="on" onclick="on()">ON</button>
    <button class="off" onclick="off()">OFF</button>

    <div>
        <button class="red" onclick="setRGB(255,0,0)">Red</button>
        <button class="green" onclick="setRGB(0,255,0)">Green</button>
        <button class="blue" onclick="setRGB(0,0,255)">Blue</button>
        <button class="white" onclick="setWhite()">White</button>
    </div>
</div>

<script>
const aurora = document.getElementById("aurora");
let strokes = [];

function rand(min,max){ return Math.random()*(max-min)+min; }

function createStroke(){
    const el = document.createElement("div");
    el.className = "aurora-stroke";
    aurora.appendChild(el);

    return {
        el,
        angle: rand(-35,35),
        baseHeight: rand(28,36),
        heightPhase: rand(0,Math.PI*2),
        xPhase: rand(0,Math.PI*2),
        yPhase: rand(0,Math.PI*2),
        opacityPhase: rand(0,Math.PI*2),

        speed: rand(0.000006,0.000012),

        top: rand(35,60)
    };
}

function buildAurora(){
    aurora.innerHTML = "";
    strokes = [];
    const count = Math.floor(rand(2,4));
    for(let i=0;i<count;i++) strokes.push(createStroke());
}

function animateAurora(t){
    strokes.forEach(s=>{
        s.heightPhase += s.speed * t * 0.1;
        s.xPhase += s.speed * t * 0.05;
        s.yPhase += s.speed * t * 0.04;
        s.opacityPhase += s.speed * t * 0.06;

        const height = s.baseHeight + Math.sin(s.heightPhase) * 3;
        const x = Math.sin(s.xPhase) * 3;
        const y = Math.cos(s.yPhase) * 2;
        const opacity = 0.45 + Math.sin(s.opacityPhase) * 0.05;

        s.el.style.top = s.top + "%";
        s.el.style.height = height + "%";
        s.el.style.opacity = opacity;
        s.el.style.transform =
            `translate(${x}%,${y}%) rotate(${s.angle}deg)`;
    });
    requestAnimationFrame(animateAurora);
}

buildAurora();
requestAnimationFrame(animateAurora);
setInterval(buildAurora, 600000); // regenerate every 10 min

let current = {r:120,g:180,b:255};
let target  = {r:120,g:180,b:255};

function lerp(a,b,t){ return a+(b-a)*t; }

function animateColor(){
    current.r = lerp(current.r,target.r,0.02);
    current.g = lerp(current.g,target.g,0.02);
    current.b = lerp(current.b,target.b,0.02);

    document.documentElement.style.setProperty("--aurora-r", Math.round(current.r));
    document.documentElement.style.setProperty("--aurora-g", Math.round(current.g));
    document.documentElement.style.setProperty("--aurora-b", Math.round(current.b));

    requestAnimationFrame(animateColor);
}
animateColor();

async function syncColor(){
    const r = await fetch("/status");
    const j = await r.json();
    if(!j.power) return;
    [target.r,target.g,target.b] = j.rgb;
}
setInterval(syncColor,4000);

function setRGB(r,g,b){ fetch(`/set?r=${r}&g=${g}&b=${b}`); }
function setWhite(){ fetch("/white"); }
function off(){ fetch("/off"); }
function on(){ fetch("/on"); }
</script>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML

@app.get("/set")
async def set_color(r:int,g:int,b:int):
    global current_rgb
    if not power_on: return {"ignored":True}
    current_rgb=[r,g,b]
    await light.turn_on(PilotBuilder(rgb=(r,g,b)))
    return {"ok":True}

@app.get("/white")
async def white():
    global current_rgb
    current_rgb=[200,220,255]
    await light.turn_on(PilotBuilder(colortemp=4000))
    return {"ok":True}

@app.get("/off")
async def off():
    global power_on
    power_on=False
    await light.turn_off()
    return {"ok":True}

@app.get("/on")
async def on():
    global power_on
    power_on=True
    await light.turn_on()
    return {"ok":True}

@app.get("/status")
async def status():
    return {"power":power_on,"rgb":current_rgb}
