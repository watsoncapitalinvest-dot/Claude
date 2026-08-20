// Measurement-driven pagination for the flip pages. Renders the built page at
// phone size, greedily packs content blocks until one more would overflow, and
// records the break points so no page ever scrolls. Pairs with build_story_page.py.
//
//   node scripts/measure_pages.js <slug> <built-file> [origin]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const slug = process.argv[2] || 'the-wookie-curse';
const file = process.argv[3] || 'scfl-wookie-curse.html';
const origin = process.argv[4] || 'http://localhost:8991';
const here = __dirname;

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 430, height: 860 } });
  await p.goto(`${origin}/${file}`, { waitUntil: 'networkidle' });
  const blocks = JSON.parse(fs.readFileSync(path.join(here, '.pack-blocks.json'), 'utf8'));
  const kinds = JSON.parse(fs.readFileSync(path.join(here, '.pack-kinds.json'), 'utf8'));
  const RUN = await p.evaluate(() => {
    const r = document.querySelector('.runhead');
    return r ? r.outerHTML : '';
  });
  const res = await p.evaluate(({ blocks, kinds, RUN }) => {
    const pages = document.querySelector('.book .pages');
    const sec = document.createElement('section');
    sec.className = 'page'; sec.style.visibility = 'hidden';
    const inner = document.createElement('div');
    inner.className = 'page-inner'; sec.appendChild(inner); pages.appendChild(sec);
    const breaks = []; let start = 0;
    while (start < blocks.length) {
      let end = start;
      while (end < blocks.length) {
        inner.innerHTML = RUN + blocks.slice(start, end + 1).join('');
        if (sec.scrollHeight > sec.clientHeight) break;
        end++;
      }
      if (end === start) end = start + 1;               // a block taller than the page
      while (end - 1 > start && kinds[end - 1] === 'sect') end--;   // never end on a heading
      start = end;
      if (start < blocks.length) breaks.push(start);
    }
    sec.remove();
    return breaks;
  }, { blocks, kinds, RUN });
  fs.writeFileSync(path.join(here, `.pack-breaks-${slug}.json`), JSON.stringify(res));
  console.log('breaks:', JSON.stringify(res));
  await b.close();
})();
