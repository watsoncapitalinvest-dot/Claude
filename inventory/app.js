/* ============================================================
   Bar Count — inventory from shelf photos
   Vanilla JS, no dependencies. Data lives in localStorage.

   Design principle, learned the hard way:
   Claude reports what it can SEE. It never guesses what's hidden
   behind the front row. Each location carries a depth factor
   learned from the operator's own corrections, and that factor —
   not the model — is what turns visible bottles into a total.
   ============================================================ */
'use strict';

const MODEL = 'claude-opus-5';
const API_URL = 'https://api.anthropic.com/v1/messages';
const MAX_EDGE = 1568;               // Claude's efficient max image edge

/* ---------- storage (never throws; memory fallback) ---------- */
const store = (() => {
  let ok = false;
  const mem = {};
  try {
    const t = '__bc_test__';
    localStorage.setItem(t, '1');
    localStorage.removeItem(t);
    ok = true;
  } catch (e) { ok = false; }
  return {
    ok,
    get(key, def) {
      try {
        const raw = ok ? localStorage.getItem(key) : mem[key];
        return raw == null ? def : JSON.parse(raw);
      } catch (e) { return def; }
    },
    set(key, val) {
      const raw = JSON.stringify(val);
      mem[key] = raw;
      if (ok) { try { localStorage.setItem(key, raw); } catch (e) {} }
    },
    remove(key) {
      delete mem[key];
      if (ok) { try { localStorage.removeItem(key); } catch (e) {} }
    }
  };
})();

const K = {
  key:       'bc-apikey',
  locations: 'bc-locations',
  cases:     'bc-cases',
  session:   'bc-session',
  catalog:   'bc-catalog',
  history:   'bc-history'
};

/* ---------- default locations (edit in Setup) ---------- */
const DEFAULT_LOCATIONS = [
  'Grey shelf — top',
  'Grey shelf — middle',
  'Grey shelf — bottom',
  'Wire rack — shelf 1',
  'Wire rack — shelf 2',
  'Wire rack — cases',
  'Cooler 1',
  'Cooler 2',
  'Cooler 3',
  'Cooler 4',
  'Floor backstock'
];

/* ---------- state ---------- */
let locations = store.get(K.locations, null);
if (!locations) {
  locations = DEFAULT_LOCATIONS.map((name, i) => ({
    id: 'L' + i,
    name,
    samples: [],           // shelf-wide {est, actual} pairs
    skuSamples: {}         // per-product {est, actual} pairs, keyed by catalogId
  }));
  store.set(K.locations, locations);
}

let caseSizes = store.get(K.cases, {});   // { "product name lowercased": unitsPerCase }
let session   = store.get(K.session, newSession());
let catalog   = store.get(K.catalog, null);  // master SKU list, see catalog.json
let current   = null;                      // { locationId, shots:[dataURL], items:[] }

/* Catalog ships with the app and is cached so the app works offline.
   A newer catalog.json on the server always wins. */
async function loadCatalog() {
  try {
    const res = await fetch('catalog.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error('no catalog');
    const fresh = await res.json();
    if (fresh && Array.isArray(fresh.items)) {
      catalog = fresh;
      store.set(K.catalog, fresh);
    }
  } catch (e) {
    /* offline or missing — keep whatever's cached */
  }
  return catalog;
}

/* Compact catalog rendering for the prompt. Stable byte-for-byte so it caches. */
function catalogBlock() {
  if (!catalog || !catalog.items || !catalog.items.length) return '';
  const onShelf = catalog.items.filter(it => it.shelf !== false);
  const backHouse = catalog.items.filter(it => it.shelf === false);
  const lines = onShelf.map(it => {
    const dims = catalog.shapes && catalog.shapes[it.shape];
    const d = dims && dims.diameter_in ? ` [${dims.diameter_in}in]` : '';
    return `${it.id}|${it.name}|${it.sub}${d}|${it.cues}`;
  });
  return `\n\nTHIS BAR'S CATALOG — ${catalog.items.length} products.\n` +
    `Match what you see against this list and report the catalog name EXACTLY as\n` +
    `written, with its id in catalogId. Matching a known SKU beats reading a blurry\n` +
    `label, so lead with the cues: cap and capsule colour, liquid colour, glass shape.\n\n` +
    `SIZE MATTERS. Many products appear twice at 750ml and 1L. A 1L bottle stands\n` +
    `visibly taller — roughly 13in vs 11.5in — and is usually slightly wider. When\n` +
    `two bottles of the same brand differ in height on the same shelf, that is the\n` +
    `750 and the 1L. If you genuinely cannot tell, pick the 750ml SKU and set\n` +
    `confidence "low" rather than inventing certainty.\n\n` +
    `NEVER count a SKU whose name contains "(generic)". Those are Craftable pour-\n` +
    `tracking placeholders, not bottles that exist on a shelf.\n\n` +
    `=== BOTTLES, CANS AND PACKS (${onShelf.length}) ===\n` +
    `id|name|subcategory[dia]|how to recognise it\n` +
    lines.join('\n') +
    `\n\n=== BACK-OF-HOUSE BULK (${backHouse.length}) ===\n` +
    `Tins, bags, cases, jugs and boxes. These live in dry storage, not on a bar\n` +
    `shelf, and are identified by package text rather than bottle shape. Match one\n` +
    `only if you are actually looking at that package. Names only:\n` +
    backHouse.map(it => `${it.id}|${it.name}`).join('\n') +
    `\n\nIf something is genuinely not on this list, still report it: use your own\n` +
    `descriptive name and leave catalogId empty. Never force a bad match, and never\n` +
    `drop stock just because it is unlisted.`;
}

function newSession() {
  return { id: Date.now(), started: new Date().toISOString(), counts: {} };
  // counts: { locationId: { locationName, at, items:[{name,size,visible,total,edited,category}] } }
}

/* ---------- calibration ----------
   Two levels. A correction on Whispering Angel in Cooler 3 teaches that lane
   first and the shelf second, because depth is a property of how a product is
   stocked, not of the shelf as a whole. A one-deep lane of Dom Perignon on the
   same shelf as a four-deep lane of rose should not get the same multiplier. */
function keyOf(it) { return (it.catalogId || it.name || '').toLowerCase(); }

function ratio(samples) {
  if (!samples || !samples.length) return null;
  let sv = 0, sa = 0;
  for (const s of samples) { sv += s.est; sa += s.actual; }
  return sv > 0 ? sa / sv : null;
}
function skuFactor(loc, key) {
  return ratio((loc.skuSamples || {})[key]);
}
function locFactor(loc) {
  return ratio(loc.samples) || 1;
}
/* The model's own lane reading does the heavy lifting; the learned factor only
   corrects its systematic bias. */
function rawEstimate(it) {
  const front = Math.max(0, it.frontCount | 0);
  const partial = Math.max(0, it.partialCount | 0);
  const deep = Math.min(6, Math.max(1, it.rowsDeep | 0 || 1));
  return Math.max(front + partial, Math.round(front * deep));
}
function estimateFor(loc, it) {
  const raw = rawEstimate(it);
  const f = skuFactor(loc, keyOf(it));
  const factor = (f === null) ? locFactor(loc) : f;
  /* The floor is what was actually SEEN — front row plus partials. `raw` already
     contains the depth guess, so flooring at raw would make the model's own
     over-reads uncorrectable: a lane read 3 deep that is really 2 could never
     come back down. Corrections have to be able to push both ways. */
  const seen = Math.max(0, it.frontCount | 0) + Math.max(0, it.partialCount | 0);
  return Math.max(seen, Math.round(raw * factor));
}
function factorLabel(loc) {
  const n = (loc.samples || []).length;
  const skus = Object.keys(loc.skuSamples || {}).length;
  if (!n) return 'not calibrated';
  return '×' + locFactor(loc).toFixed(2) + ' shelf, ' + skus + ' product' +
         (skus === 1 ? '' : 's') + ' tuned';
}

/* ---------- priors ----------
   Inventory repeats. What this shelf held last time is the strongest single
   clue about what it holds now, and it costs the operator nothing. */
function priorFor(locId, it) {
  const hist = store.get(K.history, {});
  const rec = hist[locId];
  if (!rec || !rec.items) return null;
  const k = keyOf(it);
  const hit = rec.items.find(h => (h.catalogId || h.name || '').toLowerCase() === k);
  return hit ? { total: hit.total, at: rec.at } : null;
}

/* ---------- image handling ---------- */
function fileToScaledDataURL(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      let { width: w, height: h } = img;
      const scale = Math.min(1, MAX_EDGE / Math.max(w, h));
      w = Math.round(w * scale); h = Math.round(h * scale);
      const c = document.createElement('canvas');
      c.width = w; c.height = h;
      c.getContext('2d').drawImage(img, 0, 0, w, h);
      resolve(c.toDataURL('image/jpeg', 0.85));
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Could not read that image')); };
    img.src = url;
  });
}

/* ---------- the prompt ---------- */
const SYSTEM_PROMPT = `You read bar and restaurant shelf photos and report stock.

You are looking at ONE photo of a shelf where bottles stand several rows deep.
Most of the stock is behind the front row. Do not pretend otherwise, and do not
pretend you can see it. Instead, describe the LANE.

For each product, report three separate things:

1. frontCount — closures you can fully see: capsules, foils, screwcaps, corks,
   crown caps, can tops. Count only what you can actually resolve.

2. partialCount — ADDITIONAL bottles you can see PART of but not the whole
   closure: a sliver of neck between two front bottles, the edge of a capsule,
   a shoulder showing through a gap, a reflection that is clearly another
   bottle. This is real evidence and most readers throw it away. Do not.
   If you see nothing partial, report 0.

3. rowsDeep — how many rows deep this product's lane appears to run.
   Judge it from the photo:
     - You can see the shelf back, the wall, or empty space behind the row -> 1
     - You can see a second tier of closures behind the front -> 2
     - The lane recedes past what you can resolve, no back visible -> 3 or 4
   Use the shelf itself as the ruler: a 750ml bottle is about 3 inches across,
   so a shelf that reads about five bottle-widths deep holds up to five rows.
   If you genuinely cannot judge depth, report 1 and set confidence "low".
   Never inflate rowsDeep to be helpful — a wrong depth corrupts the
   calibration that corrects your work.

Identification:
- Match against the catalog below and report the name exactly as written.
- Group by product. Two products sharing a closure colour but differing by
  label are separate entries.
- If you can read a size, report it.

Unidentified stock still counts. If you see closures you cannot name, report
them with a descriptive name like "Unidentified — copper screwcap, clear glass"
and confidence "low". Never drop stock.

For countedBy, say what you actually saw — "5 gold capsules front, 2 more
partly showing between them, lane runs about 3 deep". This is how the operator
checks your work in one glance.

Category must be exactly one of: wine, liquor, na, beer.
Wine includes all sparkling and champagne. Liquor includes liqueurs and cordials.
NA covers soda, water, juice, mixers, coffee, tea and non-alcoholic aperitifs.`;

const SCHEMA = {
  type: 'object',
  properties: {
    items: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name:         { type: 'string' },
          catalogId:    { type: 'string' },
          size:         { type: 'string' },
          frontCount:   { type: 'integer' },
          partialCount: { type: 'integer' },
          rowsDeep:     { type: 'integer' },
          countedBy:    { type: 'string' },
          confidence:   { type: 'string', enum: ['high', 'medium', 'low'] },
          category:     { type: 'string', enum: ['wine', 'liquor', 'na', 'beer'] }
        },
        required: ['name', 'catalogId', 'size', 'frontCount', 'partialCount', 'rowsDeep', 'countedBy', 'confidence', 'category'],
        additionalProperties: false
      }
    },
    shelfNotes: { type: 'string' }
  },
  required: ['items', 'shelfNotes'],
  additionalProperties: false
};

async function readShelf(shots, locName) {
  const key = store.get(K.key, '');
  if (!key) throw new Error('No API key saved. Add one in Setup.');

  const content = shots.map(d => ({
    type: 'image',
    source: { type: 'base64', media_type: 'image/jpeg', data: d.split(',')[1] }
  }));
  content.push({
    type: 'text',
    text: `Location: ${locName}\n\n` +
          (shots.length > 1
            ? `${shots.length} photos of the SAME shelf from different angles. Merge them into one count — do not add the same bottle twice across photos.\n\n`
            : '') +
          `List every visible bottle, can and pack. Visible only.`
  });

  const res = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true'
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 16000,
      thinking: { type: 'adaptive' },
      /* Catalog is stable across every shelf, so cache it — the whole list is
         re-sent on each read and would otherwise be paid for every time. */
      system: [
        { type: 'text', text: SYSTEM_PROMPT + catalogBlock(),
          cache_control: { type: 'ephemeral' } }
      ],
      output_config: { format: { type: 'json_schema', schema: SCHEMA } },
      messages: [{ role: 'user', content }]
    })
  });

  if (!res.ok) {
    let detail = '';
    try { const j = await res.json(); detail = j.error?.message || ''; } catch (e) {}
    if (res.status === 401) throw new Error('API key rejected. Check it in Setup.');
    if (res.status === 429) throw new Error('Rate limited. Wait a moment and retry.');
    throw new Error(`API error ${res.status}${detail ? ': ' + detail : ''}`);
  }

  const data = await res.json();
  if (data.stop_reason === 'refusal') throw new Error('Request was declined. Try a different photo.');

  const textBlock = (data.content || []).find(b => b.type === 'text');
  if (!textBlock) throw new Error('Empty response from the model.');
  let parsed;
  try { parsed = JSON.parse(textBlock.text); }
  catch (e) { throw new Error('Could not parse the response.'); }
  return parsed;
}

/* ---------- view routing ---------- */
const views = {
  count:   document.getElementById('view-count'),
  capture: document.getElementById('view-capture'),
  totals:  document.getElementById('view-totals'),
  setup:   document.getElementById('view-setup')
};
function show(name) {
  Object.entries(views).forEach(([k, el]) => el.classList.toggle('is-on', k === name));
  document.querySelectorAll('.tab').forEach(t =>
    t.classList.toggle('is-on', t.dataset.view === name));
  window.scrollTo(0, 0);
  if (name === 'count')  renderLocations();
  if (name === 'totals') renderTotals();
  if (name === 'setup')  renderSetup();
}
document.getElementById('tabs').addEventListener('click', e => {
  const t = e.target.closest('.tab');
  if (t) show(t.dataset.view);
});

function toast(msg, ms) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.hidden = true; }, ms || 2400);
}

/* ---------- COUNT view ---------- */
function renderLocations() {
  const done  = Object.keys(session.counts).length;
  const total = locations.length;
  let units = 0;
  Object.values(session.counts).forEach(c => c.items.forEach(i => { units += i.total; }));

  document.getElementById('session-bar').innerHTML =
    `<div><div class="lab">Units so far</div><div class="big">${units}</div></div>` +
    `<div style="text-align:right"><div class="lab">Locations</div>` +
    `<div class="big">${done}<span style="color:var(--ink-faint)">/${total}</span></div></div>`;

  const list = document.getElementById('loc-list');
  list.innerHTML = '';
  locations.forEach(loc => {
    const rec = session.counts[loc.id];
    const b = document.createElement('button');
    b.className = 'loc';
    const meta = rec
      ? `${rec.items.length} product${rec.items.length === 1 ? '' : 's'} · ${rec.items.reduce((s, i) => s + i.total, 0)} units`
      : factorLabel(loc);
    b.innerHTML =
      `<div class="loc-main"><div class="loc-name">${esc(loc.name)}</div>` +
      `<div class="loc-meta">${esc(meta)}</div></div>` +
      `<span class="pill ${rec ? 'pill-done' : 'pill-todo'}">${rec ? 'counted' : 'to do'}</span>`;
    b.onclick = () => openCapture(loc.id);
    list.appendChild(b);
  });
}

document.getElementById('btn-new-session').onclick = () => {
  if (Object.keys(session.counts).length &&
      !confirm('Start a new count? The current one is replaced.')) return;
  session = newSession();
  store.set(K.session, session);
  renderLocations();
  toast('New count started');
};

/* ---------- CAPTURE view ---------- */
function openCapture(locId) {
  const loc = locations.find(l => l.id === locId);
  current = { locationId: locId, shots: [], items: [] };
  document.getElementById('cap-title').textContent = loc.name;
  document.getElementById('cap-sub').textContent =
    'Shoot straight on at shelf height. ' + factorLabel(loc);
  document.getElementById('results').innerHTML = '';
  document.getElementById('confirm-actions').hidden = true;
  document.getElementById('analyze-status').hidden = true;
  renderShots();
  show('capture');
}
document.getElementById('btn-back').onclick = () => show('count');

document.getElementById('file-input').addEventListener('change', async e => {
  const files = Array.from(e.target.files || []);
  e.target.value = '';
  for (const f of files) {
    try { current.shots.push(await fileToScaledDataURL(f)); }
    catch (err) { toast(err.message); }
  }
  renderShots();
});

function renderShots() {
  const box = document.getElementById('shots');
  box.innerHTML = '';
  current.shots.forEach((d, i) => {
    const el = document.createElement('div');
    el.className = 'shot';
    el.innerHTML = `<img src="${d}" alt="shelf photo ${i + 1}"><button aria-label="Remove photo">&times;</button>`;
    el.querySelector('button').onclick = () => { current.shots.splice(i, 1); renderShots(); };
    box.appendChild(el);
  });
  document.getElementById('btn-analyze').disabled = current.shots.length === 0;
}

document.getElementById('btn-analyze').onclick = async () => {
  const loc = locations.find(l => l.id === current.locationId);
  const status = document.getElementById('analyze-status');
  const btn = document.getElementById('btn-analyze');
  status.hidden = false; status.className = 'status';
  status.textContent = 'Reading the shelf…';
  btn.disabled = true;

  try {
    const out = await readShelf(current.shots, loc.name);
    current.items = (out.items || []).map(it => {
      const row = {
        name: it.name,
        catalogId: it.catalogId || '',
        size: it.size || '',
        category: it.category || 'wine',
        front: Math.max(0, it.frontCount | 0),
        partial: Math.max(0, it.partialCount | 0),
        deep: Math.min(6, Math.max(1, it.rowsDeep | 0 || 1)),
        countedBy: it.countedBy || '',
        confidence: it.confidence || 'medium',
        edited: false
      };
      row.raw = rawEstimate({ frontCount: row.front, partialCount: row.partial, rowsDeep: row.deep });
      row.total = estimateFor(loc, { frontCount: row.front, partialCount: row.partial,
                                     rowsDeep: row.deep, catalogId: row.catalogId, name: row.name });
      row.prior = priorFor(loc.id, row);
      return row;
    });
    status.textContent = out.shelfNotes
      ? out.shelfNotes
      : `${current.items.length} products read. Check the numbers.`;
    renderResults();
    document.getElementById('confirm-actions').hidden = current.items.length === 0;
  } catch (err) {
    status.className = 'status err';
    status.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
};

function renderResults() {
  const loc = locations.find(l => l.id === current.locationId);
  const box = document.getElementById('results');
  box.innerHTML = '';

  current.items.forEach(it => {
    const el = document.createElement('div');
    el.className = 'res' + (it.edited ? ' edited' : '');

    const lane = `${it.front} front` +
      (it.partial ? ` + ${it.partial} partly showing` : '') +
      (it.deep > 1 ? ` · lane ~${it.deep} deep` : ' · one deep');

    const priorBit = it.prior
      ? `<span class="prior">last count ${it.prior.total}</span>`
      : '';

    el.innerHTML =
      `<div class="res-top"><div class="res-name">${esc(it.name)}` +
        (it.size ? ` <span class="res-size">${esc(it.size)}</span>` : '') +
        (it.catalogId ? '' : ` <span class="unlisted">not in catalog</span>`) +
      `</div></div>` +
      `<div class="res-evidence">${esc(lane)}${priorBit ? ' · ' : ''}${priorBit}</div>` +
      (it.countedBy ? `<div class="res-evidence dim">${esc(it.countedBy)}</div>` : '') +
      `<div class="res-nums">` +
        `<div class="stepper">` +
          `<button data-a="-" aria-label="Decrease">−</button>` +
          `<input type="number" inputmode="numeric" value="${it.total}" min="0">` +
          `<button data-a="+" aria-label="Increase">+</button>` +
        `</div>` +
      `</div>`;

    const input = el.querySelector('input');
    const setVal = v => {
      const n = Math.max(0, parseInt(v, 10) || 0);
      it.total = n;
      it.edited = (n !== estimateFor(loc, {
        frontCount: it.front, partialCount: it.partial, rowsDeep: it.deep,
        catalogId: it.catalogId, name: it.name
      }));
      input.value = n;
      el.classList.toggle('edited', it.edited);
    };
    el.querySelectorAll('.stepper button').forEach(b => {
      b.onclick = () => setVal(it.total + (b.dataset.a === '+' ? 1 : -1));
    });
    input.onchange = () => setVal(input.value);
    box.appendChild(el);
  });
}

document.getElementById('btn-confirm').onclick = () => {
  const loc = locations.find(l => l.id === current.locationId);
  if (!loc.skuSamples) loc.skuSamples = {};

  /* A correction teaches the product first and the shelf second. */
  let learned = 0;
  current.items.forEach(it => {
    if (it.edited && it.raw > 0 && it.total > 0) {
      const k = keyOf(it);
      (loc.skuSamples[k] = loc.skuSamples[k] || []).push({ est: it.raw, actual: it.total });
      if (loc.skuSamples[k].length > 12) loc.skuSamples[k] = loc.skuSamples[k].slice(-12);
      loc.samples.push({ est: it.raw, actual: it.total });
      learned++;
    }
  });
  if (loc.samples.length > 60) loc.samples = loc.samples.slice(-60);
  store.set(K.locations, locations);

  const items = current.items.map(i => ({
    name: i.name, catalogId: i.catalogId, size: i.size, category: i.category,
    front: i.front, partial: i.partial, deep: i.deep, total: i.total, edited: i.edited
  }));

  session.counts[loc.id] = { locationName: loc.name, at: new Date().toISOString(), items };
  store.set(K.session, session);

  /* History is what makes the next count easier than this one. */
  const hist = store.get(K.history, {});
  hist[loc.id] = { at: new Date().toISOString(), items };
  store.set(K.history, hist);

  toast(learned
    ? `Saved. ${learned} correction${learned === 1 ? '' : 's'} learned for ${loc.name}.`
    : 'Saved.', 3000);
  show('count');
};

/* ---------- TOTALS view ---------- */
const CAT_LABEL = { wine: 'Wine', liquor: 'Liquor', na: 'NA Bevs', beer: 'Beer' };

function aggregate() {
  const byCat = { wine: {}, liquor: {}, na: {}, beer: {} };
  Object.values(session.counts).forEach(rec => {
    rec.items.forEach(i => {
      const cat = byCat[i.category] ? i.category : 'wine';
      const key = (i.name + (i.size ? ' |' + i.size : '')).trim();
      if (!byCat[cat][key]) byCat[cat][key] = { name: i.name, size: i.size, total: 0 };
      byCat[cat][key].total += i.total;
    });
  });
  return byCat;
}

function renderTotals() {
  const done = Object.keys(session.counts).length;
  const missing = locations.filter(l => !session.counts[l.id]);
  const cov = document.getElementById('coverage');

  if (!done) {
    cov.className = 'coverage';
    cov.textContent = 'Nothing counted yet.';
    document.getElementById('totals-body').innerHTML = '<div class="empty">No counts on file.</div>';
    return;
  }
  if (missing.length) {
    cov.className = 'coverage';
    cov.innerHTML = `<strong>${missing.length} location${missing.length === 1 ? '' : 's'} not counted.</strong> ` +
      `This total is partial — it covers only what you walked: ` +
      esc(missing.map(m => m.name).join(', ')) + ' still to do.';
  } else {
    cov.className = 'coverage ok';
    cov.innerHTML = `<strong>All ${locations.length} locations counted.</strong> Nothing skipped.`;
  }

  const byCat = aggregate();
  let html = '', grand = 0;
  Object.keys(CAT_LABEL).forEach(cat => {
    const rows = Object.values(byCat[cat]).sort((a, b) => a.name.localeCompare(b.name));
    if (!rows.length) return;
    const sub = rows.reduce((s, r) => s + r.total, 0);
    grand += sub;
    html += `<div class="cat"><h2><span>${CAT_LABEL[cat]}</span><span>${sub}</span></h2>`;
    rows.forEach(r => {
      html += `<div class="line"><span class="nm">${esc(r.name)}` +
              (r.size ? ` <span class="res-size">${esc(r.size)}</span>` : '') +
              `</span><span class="dots"></span><span class="qt">${r.total}</span></div>`;
    });
    html += `</div>`;
  });
  html += `<div class="session-bar"><div><div class="lab">Total units</div>` +
          `<div class="big">${grand}</div></div></div>`;
  document.getElementById('totals-body').innerHTML = html;
}

function toCSV() {
  const rows = [['Item', 'Size', 'Category', 'Units', 'Locations']];
  const seen = {};
  Object.values(session.counts).forEach(rec => {
    rec.items.forEach(i => {
      const key = (i.name + '|' + i.size + '|' + i.category).toLowerCase();
      if (!seen[key]) seen[key] = { name: i.name, size: i.size, cat: i.category, total: 0, locs: [] };
      seen[key].total += i.total;
      if (!seen[key].locs.includes(rec.locationName)) seen[key].locs.push(rec.locationName);
    });
  });
  Object.values(seen)
    .sort((a, b) => a.name.localeCompare(b.name))
    .forEach(v => rows.push([v.name, v.size, CAT_LABEL[v.cat] || v.cat, v.total, v.locs.join('; ')]));
  return rows.map(r => r.map(c => {
    const s = String(c);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }).join(',')).join('\n');
}

document.getElementById('btn-export').onclick = () => {
  const blob = new Blob([toCSV()], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bar-count-' + new Date().toISOString().slice(0, 10) + '.csv';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
};
document.getElementById('btn-copy').onclick = async () => {
  try { await navigator.clipboard.writeText(toCSV()); toast('Copied'); }
  catch (e) { toast('Could not copy — use Export instead'); }
};

/* ---------- SETUP view ---------- */
function renderSetup() {
  document.getElementById('key-status').textContent =
    store.get(K.key, '') ? 'Key saved in this browser.' : 'No key saved.';

  const cs = document.getElementById('cat-summary');
  if (!catalog || !catalog.items) {
    cs.innerHTML = '<div class="hint">No catalog loaded.</div>';
  } else {
    const n = catalog.items.length;
    const solid = catalog.items.filter(i => i.confidence === 'high').length;
    const need = catalog.items.filter(i => i.needs_photo).length;
    cs.innerHTML =
      `<div class="cat-stat">` +
      `<div><span class="n">${n}</span><span class="l">products</span></div>` +
      `<div><span class="n">${solid}</span><span class="l">strong cues</span></div>` +
      `<div><span class="n">${need}</span><span class="l">need a photo</span></div>` +
      `</div>` +
      (need ? `<div class="hint">Needs a reference shot: ` +
        esc(catalog.items.filter(i => i.needs_photo).map(i => i.name).join(', ')) + `</div>` : '') +
      `<div class="hint">v${esc(catalog.version || '?')} · ` +
      `${catalog.items.filter(i => i.cat === 'wine').length} wine · ` +
      `${catalog.items.filter(i => i.cat === 'liquor').length} liquor · ` +
      `${catalog.items.filter(i => i.cat === 'na').length} NA Bev. ` +
      `No Beer section transcribed yet.</div>`;
  }

  const lb = document.getElementById('setup-locs');
  lb.innerHTML = '';
  locations.forEach(loc => {
    const r = document.createElement('div');
    r.className = 'srow';
    r.innerHTML = `<span class="nm">${esc(loc.name)}</span>` +
                  `<span class="fac">${esc(factorLabel(loc))}</span>` +
                  `<button class="x" aria-label="Remove">&times;</button>`;
    r.querySelector('.x').onclick = () => {
      if (!confirm('Remove ' + loc.name + '? Its calibration is lost.')) return;
      locations = locations.filter(l => l.id !== loc.id);
      delete session.counts[loc.id];
      store.set(K.locations, locations); store.set(K.session, session);
      renderSetup();
    };
    lb.appendChild(r);
  });

  const cb = document.getElementById('setup-cases');
  const keys = Object.keys(caseSizes).sort();
  cb.innerHTML = keys.length ? '' : '<div class="hint">None set.</div>';
  keys.forEach(k => {
    const r = document.createElement('div');
    r.className = 'srow';
    r.innerHTML = `<span class="nm">${esc(k)}</span><span class="fac">${caseSizes[k]}/case</span>` +
                  `<button class="x" aria-label="Remove">&times;</button>`;
    r.querySelector('.x').onclick = () => {
      delete caseSizes[k]; store.set(K.cases, caseSizes); renderSetup();
    };
    cb.appendChild(r);
  });
}

document.getElementById('btn-save-key').onclick = () => {
  const v = document.getElementById('api-key').value.trim();
  if (!v) { toast('Paste a key first'); return; }
  store.set(K.key, v);
  document.getElementById('api-key').value = '';
  renderSetup();
  toast('Key saved');
};
document.getElementById('btn-add-loc').onclick = () => {
  const el = document.getElementById('new-loc');
  const name = el.value.trim();
  if (!name) return;
  locations.push({ id: 'L' + Date.now(), name, samples: [] });
  store.set(K.locations, locations);
  el.value = '';
  renderSetup();
};
document.getElementById('btn-add-case').onclick = () => {
  const n = document.getElementById('new-case-sku');
  const q = document.getElementById('new-case-qty');
  const name = n.value.trim(), qty = parseInt(q.value, 10);
  if (!name || !qty || qty < 1) { toast('Need a product and a number'); return; }
  caseSizes[name] = qty;
  store.set(K.cases, caseSizes);
  n.value = ''; q.value = '';
  renderSetup();
};
document.getElementById('btn-export-all').onclick = () => {
  const dump = JSON.stringify({ locations, caseSizes, session }, null, 2);
  const blob = new Blob([dump], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bar-count-data.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
};
document.getElementById('btn-wipe').onclick = () => {
  if (!confirm('Erase all locations, calibration and counts? This cannot be undone.')) return;
  [K.locations, K.cases, K.session].forEach(k => store.remove(k));
  location.reload();
};

/* ---------- util ---------- */
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* ---------- boot ---------- */
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
show('count');
loadCatalog().then(() => { if (views.setup.classList.contains('is-on')) renderSetup(); });
