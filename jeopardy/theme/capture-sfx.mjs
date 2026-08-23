import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const b = await chromium.launch();
const p = await b.newPage();
p.on('pageerror',e=>console.log('ERR',String(e).slice(0,160)));
await p.goto('http://127.0.0.1:8912/jeopardy/index.html',{waitUntil:'networkidle'});
await p.waitForTimeout(600);

const names = ['reveal','right','wrong','final','done'];
const out = {};
for (const nm of names){
  const data = await p.evaluate(async (nm) => {
    muted = false;                                  // effects bail out when muted
    const SR = 44100, LEN = SR * 2;                 // two seconds is plenty
    const off = new OfflineAudioContext(1, LEN, SR);
    AC = off;                                       // point the game's synth at it
    SFX[nm]();
    const buf = await off.startRendering();
    AC = null;
    return Array.from(buf.getChannelData(0));
  }, nm);
  out[nm] = data;
  const peak = Math.max(...data.map(Math.abs));
  console.log(`${nm.padEnd(8)} peak ${peak.toFixed(3)}  nonzero ${data.filter(x=>Math.abs(x)>1e-4).length}`);
}
fs.writeFileSync('sfx.json', JSON.stringify(out));
await b.close();
