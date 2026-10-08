// Shrink any page that does not fit, so one article is always one page.
//
//   node scripts/fit_pages.js <built-file> [origin]
//
// Prints a JSON array with one zoom factor per .page, 1 where nothing is
// needed. Binary search rather than a fixed step, because an article that is
// 4% too tall and one that is 40% too tall should not get the same treatment.
const { chromium } = require('playwright');
const file = process.argv[2];
const origin = process.argv[3] || 'http://localhost:8991';

(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 430, height: 860 } });
  await p.goto(`${origin}/${file}`, { waitUntil: 'networkidle' });
  await p.waitForTimeout(400);
  const out = await p.evaluate(async () => {
    const pages = [...document.querySelectorAll('.page')];
    const res = [];
    for (const sec of pages) {
      const inner = sec.querySelector('.page-inner');
      // The cover has no .page-inner. Emitting a placeholder for it pushed every
      // later value one slot along, so each page was given the previous page's
      // zoom and the longest article got the cover's 1. Only pages with an inner
      // are reported, which is exactly what the injector walks.
      if (!inner) continue;
      // getBoundingClientRect reflects zoom; scrollHeight does NOT -- it reports
      // the unzoomed layout height, so comparing it to clientHeight says a page
      // fits when it is still hanging off the bottom.
      const fits = () => inner.getBoundingClientRect().height <= sec.clientHeight - 24;
      inner.style.zoom = '1';
      if (fits()) { res.push(1); continue; }
      // 0.55 floor. Lower than ideal, but a clipped page is worse than a small one
      let lo = 0.55, hi = 1, best = 0.55;
      for (let i = 0; i < 12; i++) {
        const mid = (lo + hi) / 2;
        inner.style.zoom = String(mid);
        if (fits()) { best = mid; lo = mid; } else { hi = mid; }
      }
      inner.style.zoom = '1';
      res.push(Math.floor(best * 1000) / 1000);
    }
    return res;
  });
  console.log(JSON.stringify(out));
  await b.close();
})();
