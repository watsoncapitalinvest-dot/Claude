/* ============================================================
   SPS Pools & Spas — Back Office
   Vanilla JS, no dependencies. Data lives in localStorage.
   ============================================================ */
'use strict';

/* ---------- storage (never throws; memory fallback) ---------- */
const store = (() => {
  let ok = false;
  const mem = {};
  try {
    const t = '__sps_test__';
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
  company: 'sps-company',
  techs: 'sps-techs',
  customers: 'sps-customers',
  visits: 'sps-visits',
  invoices: 'sps-invoices',
  iosHint: 'sps-ios-hint-dismissed'
};

const DB = {
  company: store.get(K.company, null),
  techs: store.get(K.techs, []),
  customers: store.get(K.customers, []),
  visits: store.get(K.visits, []),
  invoices: store.get(K.invoices, [])
};
function save(which) {
  if (which === 'company') store.set(K.company, DB.company);
  if (which === 'techs') store.set(K.techs, DB.techs);
  if (which === 'customers') store.set(K.customers, DB.customers);
  if (which === 'visits') store.set(K.visits, DB.visits);
  if (which === 'invoices') store.set(K.invoices, DB.invoices);
}

/* ---------- utils ---------- */
const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, m =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
const uid = (p) => p + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
const money = (n) => '$' + (Number(n) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const DAYS = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];
const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const TECH_PALETTE = ['#16C0C8', '#7C5CFC', '#E0901A', '#1AA463', '#E0466B', '#2F86D6', '#8A6D3B', '#5C7480'];

function toISO(d) { // local date -> YYYY-MM-DD (never UTC, avoids off-by-one)
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
function fromISO(iso) {
  const p = String(iso || '').split('-').map(Number);
  return new Date(p[0], (p[1] || 1) - 1, p[2] || 1);
}
const todayISO = () => toISO(new Date());
function addDays(iso, n) { const d = fromISO(iso); d.setDate(d.getDate() + n); return toISO(d); }
function fmtDate(iso) {
  if (!iso) return '—';
  const d = fromISO(iso);
  return MONTHS[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
}
function fmtDateShort(iso) { const d = fromISO(iso); return MONTHS[d.getMonth()] + ' ' + d.getDate(); }
function sameMonth(iso, ref) { return !!iso && iso.slice(0, 7) === ref.slice(0, 7); }
function initials(name) {
  return String(name || '?').trim().split(/\s+/).slice(0, 2).map(w => w[0] || '').join('').toUpperCase() || '?';
}

function toast(msg) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  $('#toast-root').appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; }, 1900);
  setTimeout(() => el.remove(), 2300);
}

/* ---------- lookups ---------- */
const getCustomer = (id) => DB.customers.find(c => c.id === id);
const getTech = (id) => DB.techs.find(t => t.id === id);
const techColor = (id) => (getTech(id) || {}).color || '#5C7480';
const techName = (id) => (getTech(id) || {}).name || 'Unassigned';
const customerVisits = (id) => DB.visits.filter(v => v.customerId === id).sort((a, b) => b.date.localeCompare(a.date));
const customerInvoices = (id) => DB.invoices.filter(i => i.customerId === id).sort((a, b) => b.date.localeCompare(a.date));

/* ---------- scheduling ---------- */
function isDue(c, iso) {
  if (c.status !== 'active' || !c.plan || c.plan.freq === 'none' || !c.plan.day) return false;
  const d = fromISO(iso);
  if (DAYS[d.getDay()] !== c.plan.day) return false;
  if (c.plan.freq === 'weekly') return true;
  if (c.plan.freq === 'biweekly') {
    const created = fromISO(c.createdAt || iso);
    const weeks = Math.floor((d - created) / (7 * 86400000));
    return weeks % 2 === 0;
  }
  if (c.plan.freq === 'monthly') return d.getDate() <= 7; // first such weekday of the month
  return false;
}
const dueOn = (iso) => DB.customers.filter(c => isDue(c, iso));
const visitFor = (customerId, iso) => DB.visits.find(v => v.customerId === customerId && v.date === iso);

/* ---------- chemistry ranges & dosing ---------- */
const RANGES = {
  fc:   { label: 'Free Chlorine', unit: 'ppm', min: 1, max: 3, note: '' },
  ph:   { label: 'pH', unit: '', min: 7.4, max: 7.6, note: 'acceptable 7.2–7.8' },
  ta:   { label: 'Total Alkalinity', unit: 'ppm', min: 80, max: 120, note: '' },
  cya:  { label: 'Stabilizer / CYA', unit: 'ppm', min: 30, max: 50, note: 'salt pools 60–80' },
  ch:   { label: 'Calcium Hardness', unit: 'ppm', min: 200, max: 400, note: '' },
  salt: { label: 'Salt', unit: 'ppm', min: 2700, max: 3400, note: 'check the cell' }
};
function readingState(key, val) {
  if (val === '' || val == null) return null;
  const n = Number(val);
  if (isNaN(n)) return null;
  const r = RANGES[key];
  if (n < r.min) return 'low';
  if (n > r.max) return 'high';
  return 'ok';
}
function visitBalancePill(v) {
  let off = 0, any = false;
  for (const k of Object.keys(RANGES)) {
    const s = readingState(k, (v.readings || {})[k]);
    if (s) { any = true; if (s !== 'ok') off++; }
  }
  if (!any) return '<span class="pill gray">No readings</span>';
  return off === 0 ? '<span class="pill green">Balanced</span>' : `<span class="pill red">${off} off</span>`;
}

/* unit formatting: fl oz -> gal/qt/cups; weight oz -> lb */
function r1(n) { return Math.round(n * 10) / 10; }
function fmtFlOz(oz) {
  if (oz >= 128) return r1(oz / 128) + ' gal';
  if (oz >= 32) return r1(oz / 32) + ' qt';
  if (oz >= 8) return r1(oz / 8) + ' cups';
  return r1(oz) + ' fl oz';
}
function fmtWtOz(oz) {
  if (oz >= 16) return r1(oz / 16) + ' lb';
  return r1(oz) + ' oz';
}

/* Dosing tables — amounts per 10,000 gallons */
const DOSING = {
  fc: {
    label: 'Free Chlorine (ppm)',
    raise: [
      { id: 'lc125', name: 'Liquid chlorine 12.5%', perUnit: 10.2, per: 1, kind: 'floz' },
      { id: 'lc10', name: 'Liquid chlorine 10%', perUnit: 12.8, per: 1, kind: 'floz' },
      { id: 'calhypo', name: 'Cal-hypo 73%', perUnit: 1.83, per: 1, kind: 'wt' }
    ],
    lower: 'dilute-or-wait'
  },
  ph: {
    label: 'pH',
    raise: [{ id: 'sodaash', name: 'Soda ash', perUnit: 30, per: 1, kind: 'wt' }],
    lowerProducts: [
      { id: 'mur', name: 'Muriatic acid 31%', perUnit: 80, per: 1, kind: 'floz' },
      { id: 'dry', name: 'Dry acid (sodium bisulfate)', perUnit: 60, per: 1, kind: 'wt' }
    ]
  },
  ta: {
    label: 'Total Alkalinity (ppm)',
    raise: [{ id: 'soda', name: 'Baking soda', perUnit: 24, per: 10, kind: 'wt' }],
    lowerProducts: [{ id: 'mur', name: 'Muriatic acid 31%', perUnit: 26, per: 10, kind: 'floz', note: 'also lowers pH — retest pH after' }]
  },
  ch: {
    label: 'Calcium Hardness (ppm)',
    raise: [{ id: 'cacl', name: 'Calcium chloride', perUnit: 20, per: 10, kind: 'wt' }],
    lower: 'dilute'
  },
  cya: {
    label: 'Stabilizer / CYA (ppm)',
    raise: [{ id: 'cya', name: 'Cyanuric acid', perUnit: 13, per: 10, kind: 'wt' }],
    lower: 'dilute'
  },
  salt: {
    label: 'Salt (ppm)',
    raise: [{ id: 'salt', name: 'Pool salt', formula: 'salt' }],
    lower: 'dilute'
  }
};

function calcDose(param, gallons, current, target, productId) {
  const cfg = DOSING[param];
  const delta = target - current;
  const scale = gallons / 10000;
  if (!gallons || gallons <= 0) return { err: 'Enter the pool volume in gallons.' };
  if (isNaN(current) || isNaN(target)) return { err: 'Enter both current and target values.' };
  if (delta === 0) return { err: 'Current and target are the same — nothing to add.' };

  if (delta > 0) {
    const prods = cfg.raise;
    const p = prods.find(x => x.id === productId) || prods[0];
    if (p.formula === 'salt') {
      const lbs = 0.00000834 * gallons * delta;
      return { amount: r1(lbs) + ' lb', product: p.name, note: 'Broadcast into the pool with the pump running; brush to dissolve.' };
    }
    const units = p.perUnit * (delta / p.per) * scale;
    return {
      amount: p.kind === 'floz' ? fmtFlOz(units) : fmtWtOz(units),
      product: p.name,
      note: p.note || ''
    };
  }

  // lowering
  if (cfg.lowerProducts) {
    const p = cfg.lowerProducts.find(x => x.id === productId) || cfg.lowerProducts[0];
    const units = p.perUnit * (Math.abs(delta) / p.per) * scale;
    return {
      amount: p.kind === 'floz' ? fmtFlOz(units) : fmtWtOz(units),
      product: p.name,
      note: p.note || 'Add slowly near a return with the pump running.'
    };
  }
  // no chemical lowers this — dilution
  if (current <= 0) return { err: 'Current value must be above zero to compute dilution.' };
  const drain = gallons * (1 - target / current);
  const pct = Math.round((1 - target / current) * 100);
  return {
    amount: Math.round(drain).toLocaleString() + ' gal',
    product: 'Partial drain & refill (dilution)',
    note: `Drain about ${pct}% of the pool and refill with fresh water, then retest.` +
      (param === 'fc' && cfg.lower === 'dilute-or-wait' ? ' For chlorine you can also simply wait — sunlight burns FC off naturally.' : '')
  };
}

/* ============================================================
   Views
   ============================================================ */
const state = {
  view: 'dashboard',
  scheduleDate: todayISO(),
  clientSearch: '',
  clientId: null,      // open customer detail
  invoiceFilter: 'all'
};

const ICONS = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
  schedule: '<rect x="3" y="4" width="18" height="17" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
  clients: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  invoices: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
  reports: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
  team: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  tools: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  settings: '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>',
  more: '<circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/><circle cx="5" cy="12" r="1.6"/>'
};
const svg = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg>`;

const NAV = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'schedule', label: 'Schedule' },
  { id: 'clients', label: 'Clients' },
  { id: 'invoices', label: 'Invoices' },
  { id: 'reports', label: 'Reports' },
  { id: 'team', label: 'Team' },
  { id: 'tools', label: 'Tools' },
  { id: 'settings', label: 'Settings' }
];
const TABS = ['dashboard', 'schedule', 'clients', 'invoices'];
const TITLES = { dashboard: 'Dashboard', schedule: 'Schedule', clients: 'Clients', invoices: 'Invoices', reports: 'Reports', team: 'Team', tools: 'Tools', settings: 'Settings' };

/* ---------- global actions namespace (used from inline handlers) ---------- */
const A = {};

A.go = (view) => {
  state.view = view;
  if (view !== 'clients') state.clientId = null;
  render();
  window.scrollTo(0, 0);
};
A.openClient = (id) => { state.view = 'clients'; state.clientId = id; render(); window.scrollTo(0, 0); };
A.closeClient = () => { state.clientId = null; render(); };

function buildNav() {
  $('#sidenav').innerHTML = NAV.map(n =>
    `<button data-nav="${n.id}" onclick="A.go('${n.id}')">${svg(n.id)}<span>${n.label}</span></button>`).join('');
  $('#tabbar').innerHTML = TABS.map(t =>
    `<button data-nav="${t}" onclick="A.go('${t}')">${svg(t)}<span>${TITLES[t]}</span></button>`).join('') +
    `<button data-nav="more" onclick="A.moreSheet()">${svg('more')}<span>More</span></button>`;
}

A.moreSheet = () => {
  openModal('More', `
    <div class="grid" style="grid-template-columns:1fr 1fr;gap:10px">
      ${['reports', 'team', 'tools', 'settings'].map(v => `
        <button class="btn ghost" style="flex-direction:column;padding:18px 10px;gap:8px" onclick="closeModal();A.go('${v}')">
          ${svg(v)}<span>${TITLES[v]}</span>
        </button>`).join('')}
    </div>`, '');
};

function render() {
  buildNavState();
  const v = state.view;
  $('#page-title').textContent = TITLES[v] || '';
  const el = $('#view');
  if (v === 'dashboard') el.innerHTML = viewDashboard();
  else if (v === 'schedule') el.innerHTML = viewSchedule();
  else if (v === 'clients') el.innerHTML = state.clientId ? viewClientDetail(state.clientId) : viewClients();
  else if (v === 'invoices') el.innerHTML = viewInvoices();
  else if (v === 'reports') el.innerHTML = viewReports();
  else if (v === 'team') el.innerHTML = viewTeam();
  else if (v === 'tools') el.innerHTML = viewTools();
  else if (v === 'settings') el.innerHTML = viewSettings();
  $('#side-foot').innerHTML = DB.company
    ? `<b>${esc(DB.company.name)}</b>${esc(DB.company.phone || '')}` : '';
}
function buildNavState() {
  document.querySelectorAll('[data-nav]').forEach(b => {
    b.classList.toggle('active', b.dataset.nav === state.view);
  });
}

/* ---------- dashboard ---------- */
function viewDashboard() {
  const today = todayISO();
  const stops = dueOn(today);
  const done = stops.filter(c => visitFor(c.id, today)).length;
  const revMTD = DB.invoices.filter(i => i.status === 'paid' && sameMonth(i.paidDate, today))
    .reduce((s, i) => s + (Number(i.total) || 0), 0);
  const outstanding = DB.invoices.filter(i => i.status === 'unpaid')
    .reduce((s, i) => s + (Number(i.total) || 0), 0);
  const active = DB.customers.filter(c => c.status === 'active').length;
  const overdue = DB.invoices.filter(i => i.status === 'unpaid' && i.dueDate && i.dueDate < today);

  return `
    ${overdue.length ? `<div class="banner red" onclick="state.invoiceFilter='unpaid';A.go('invoices')">
      ⚠️ <span>${overdue.length} overdue invoice${overdue.length > 1 ? 's' : ''} totaling
      ${money(overdue.reduce((s, i) => s + Number(i.total || 0), 0))} — tap to review</span></div>` : ''}
    <div class="grid tiles">
      <div class="tile"><div class="t-label">Today's stops</div><div class="t-num">${done}/${stops.length}</div>
        <div class="t-sub">${stops.length ? (stops.length - done) + ' remaining' : 'No stops today'}</div></div>
      <div class="tile accent"><div class="t-label">Revenue (MTD)</div><div class="t-num">${money(revMTD)}</div>
        <div class="t-sub">paid this month</div></div>
      <div class="tile"><div class="t-label">Outstanding</div><div class="t-num">${money(outstanding)}</div>
        <div class="t-sub">${DB.invoices.filter(i => i.status === 'unpaid').length} unpaid invoice(s)</div></div>
      <div class="tile"><div class="t-label">Active accounts</div><div class="t-num">${active}</div>
        <div class="t-sub">${DB.customers.length - active ? (DB.customers.length - active) + ' paused' : 'all active'}</div></div>
    </div>

    <div class="section-head"><h2>Today's route — ${fmtDate(today)}</h2>
      <button class="btn ghost sm" onclick="state.scheduleDate='${today}';A.go('schedule')">Open schedule</button></div>
    <div class="card">${routeList(today) || '<div class="empty"><span class="big">🏖️</span>No stops scheduled today.</div>'}</div>

    <div class="section-head"><h2>Quick actions</h2></div>
    <div class="quick-grid">
      <button class="btn primary" onclick="A.customerForm()">＋<small>New customer</small></button>
      <button class="btn dark" onclick="A.invoiceForm()">＋<small>New invoice</small></button>
      <button class="btn ghost" onclick="A.go('tools')">🧪<small>Dosage calculator</small></button>
      <button class="btn ghost" onclick="A.go('reports')">📊<small>Reports</small></button>
    </div>`;
}

/* ---------- schedule ---------- */
function routeList(iso) {
  const stops = dueOn(iso);
  if (!stops.length) return '';
  // group by tech
  const groups = {};
  for (const c of stops) (groups[c.tech || ''] = groups[c.tech || ''] || []).push(c);
  return Object.keys(groups).map(tid => {
    const t = getTech(tid);
    return `<div class="tech-group">
      <div class="tg-head"><span class="tg-dot" style="background:${techColor(tid)}"></span>${esc(t ? t.name : 'Unassigned')}
        <span class="pill gray">${groups[tid].length}</span></div>
      ${groups[tid].map(c => {
        const v = visitFor(c.id, iso);
        return `<div class="row" onclick="A.openClient('${c.id}')">
          <span class="avatar" style="background:${techColor(c.tech)}">${esc(initials(c.name))}</span>
          <div class="r-main"><div class="r-title">${esc(c.name)}</div><div class="r-sub">${esc(c.address || '')}</div></div>
          <div class="r-side">${v
            ? `<span class="pill green">✓ Done</span>`
            : `<button class="btn primary sm" onclick="event.stopPropagation();A.visitForm('${c.id}','${iso}')">Log visit</button>`}
          </div></div>`;
      }).join('')}
    </div>`;
  }).join('');
}

A.schedDay = (iso) => { state.scheduleDate = iso; render(); };

function viewSchedule() {
  const sel = state.scheduleDate;
  const d = fromISO(sel);
  // week strip Sun..Sat containing selected date
  const weekStart = addDays(sel, -d.getDay());
  let strip = '';
  for (let i = 0; i < 7; i++) {
    const iso = addDays(weekStart, i);
    const n = dueOn(iso).length;
    const dd = fromISO(iso);
    strip += `<div class="day-cell ${iso === sel ? 'sel' : ''} ${iso === todayISO() ? 'today' : ''}" onclick="A.schedDay('${iso}')">
      <div class="d-dow">${DAYS[dd.getDay()]}</div><div class="d-num">${dd.getDate()}</div>
      <div class="d-count">${n ? n + ' stop' + (n > 1 ? 's' : '') : '&nbsp;'}</div></div>`;
  }
  const stops = dueOn(sel);
  const done = stops.filter(c => visitFor(c.id, sel)).length;
  return `
    <div class="date-nav">
      <button class="btn ghost sm" onclick="A.schedDay('${addDays(sel, -1)}')">‹ Prev</button>
      <h2>${DAY_NAMES[d.getDay()]}, ${fmtDate(sel)}</h2>
      <button class="btn ghost sm" onclick="A.schedDay('${addDays(sel, 1)}')">Next ›</button>
    </div>
    <div class="day-strip">${strip}</div>
    ${sel !== todayISO() ? `<div style="text-align:center;margin-bottom:10px">
      <button class="btn ghost sm" onclick="A.schedDay('${todayISO()}')">Jump to today</button></div>` : ''}
    <div class="card">
      <h3>Route <span class="spacer"></span><span class="pill ${done === stops.length && stops.length ? 'green' : 'aqua'}">${done}/${stops.length} done</span></h3>
      ${routeList(sel) || '<div class="empty"><span class="big">🏖️</span>No customers due on this day.</div>'}
    </div>`;
}

/* ---------- clients ---------- */
A.clientSearch = (q) => {
  state.clientSearch = q;
  const list = $('#client-list');
  if (list) list.innerHTML = clientRows();
};

function planPill(c) {
  if (!c.plan || c.plan.freq === 'none') return '<span class="pill gray">No plan</span>';
  const f = { weekly: 'Weekly', biweekly: 'Bi-weekly', monthly: 'Monthly' }[c.plan.freq] || c.plan.freq;
  return `<span class="pill aqua">${f}${c.plan.day ? ' · ' + c.plan.day : ''}</span>`;
}

function clientRows() {
  const q = state.clientSearch.trim().toLowerCase();
  let list = DB.customers.slice().sort((a, b) => a.name.localeCompare(b.name));
  if (q) list = list.filter(c =>
    (c.name || '').toLowerCase().includes(q) ||
    (c.address || '').toLowerCase().includes(q) ||
    (c.phone || '').toLowerCase().includes(q));
  if (!list.length) return `<div class="empty"><span class="big">🔍</span>${q ? 'No matches.' : 'No customers yet — add your first one.'}</div>`;
  return list.map(c => `
    <div class="row" onclick="A.openClient('${c.id}')">
      <span class="avatar" style="background:${techColor(c.tech)}">${esc(initials(c.name))}</span>
      <div class="r-main">
        <div class="r-title">${esc(c.name)} ${c.status === 'paused' ? '<span class="pill amber">Paused</span>' : ''}</div>
        <div class="r-sub">${esc(c.address || 'No address')}</div>
      </div>
      <div class="r-side">${planPill(c)}<span class="r-sub">${customerVisits(c.id).length} visits</span></div>
    </div>`).join('');
}

function viewClients() {
  return `
    <div class="search-wrap"><input type="search" placeholder="Search name, address, or phone…"
      value="${esc(state.clientSearch)}" oninput="A.clientSearch(this.value)"></div>
    <div class="section-head"><h2>${DB.customers.length} customer${DB.customers.length === 1 ? '' : 's'}</h2>
      <button class="btn primary sm" onclick="A.customerForm()">＋ New customer</button></div>
    <div class="card" id="client-list">${clientRows()}</div>`;
}

function viewClientDetail(id) {
  const c = getCustomer(id);
  if (!c) { state.clientId = null; return viewClients(); }
  const visits = customerVisits(id);
  const invoices = customerInvoices(id);
  const pool = c.pool || {}, access = c.access || {};
  return `
    <button class="back-link" onclick="A.closeClient()">‹ All clients</button>
    <div class="detail-head">
      <span class="avatar" style="background:${techColor(c.tech)}">${esc(initials(c.name))}</span>
      <div class="dh-main">
        <h2>${esc(c.name)}</h2>
        <div class="dh-sub">${esc(c.address || 'No address')}</div>
      </div>
      <div class="btn-row">
        ${c.phone ? `<a class="btn ghost sm" href="tel:${esc(c.phone)}" style="text-decoration:none">📞 Call</a>` : ''}
        <button class="btn ghost sm" onclick="A.customerForm('${c.id}')">Edit</button>
        <button class="btn primary sm" onclick="A.visitForm('${c.id}')">＋ Log visit</button>
      </div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
      ${planPill(c)}
      <span class="pill ${c.status === 'active' ? 'green' : 'amber'}">${c.status === 'active' ? 'Active' : 'Paused'}</span>
      ${c.plan && c.plan.price ? `<span class="pill gray">${money(c.plan.price)}/visit</span>` : ''}
      <span class="pill gray">Tech: ${esc(techName(c.tech))}</span>
    </div>

    <div class="grid two">
      <div class="card"><h3>Contact</h3>
        <dl class="kv">
          <dt>Phone</dt><dd>${esc(c.phone || '—')}</dd>
          <dt>Email</dt><dd>${esc(c.email || '—')}</dd>
          <dt>Since</dt><dd>${fmtDate(c.createdAt)}</dd>
        </dl></div>
      <div class="card"><h3>Pool</h3>
        <dl class="kv">
          <dt>Volume</dt><dd>${pool.gallons ? Number(pool.gallons).toLocaleString() + ' gal' : '—'}</dd>
          <dt>Type</dt><dd>${esc(pool.type || '—')}</dd>
          <dt>Surface</dt><dd>${esc(pool.surface || '—')}</dd>
          <dt>Equipment</dt><dd>${esc(pool.equipment || '—')}</dd>
        </dl></div>
      <div class="card"><h3>Access</h3>
        <dl class="kv">
          <dt>Gate</dt><dd>${esc(access.gate || '—')}</dd>
          <dt>Pets</dt><dd>${esc(access.pet || '—')}</dd>
          <dt>Notes</dt><dd>${esc(access.notes || '—')}</dd>
        </dl></div>
    </div>

    <div class="section-head"><h2>Service history</h2><span class="pill gray">${visits.length}</span></div>
    <div class="card">${visits.length ? visits.map(v => `
      <div class="row" onclick="A.visitDetail('${v.id}')">
        <span class="avatar" style="background:${techColor(v.techId)};width:34px;height:34px;font-size:12px">${esc(initials(techName(v.techId)))}</span>
        <div class="r-main"><div class="r-title">${fmtDate(v.date)}</div>
          <div class="r-sub">${esc((v.tasks || []).slice(0, 3).join(', ') || 'No tasks logged')}${(v.tasks || []).length > 3 ? '…' : ''}</div></div>
        <div class="r-side">${visitBalancePill(v)}</div>
      </div>`).join('') : '<div class="empty">No visits logged yet.</div>'}
    </div>

    <div class="section-head"><h2>Invoices</h2>
      <button class="btn ghost sm" onclick="A.invoiceForm(null,'${c.id}')">＋ New invoice</button></div>
    <div class="card">${invoices.length ? invoices.map(i => invoiceRow(i)).join('') : '<div class="empty">No invoices yet.</div>'}</div>

    <div style="margin-top:18px;text-align:right">
      <button class="btn danger sm" onclick="A.deleteCustomer('${c.id}')">Delete customer</button>
    </div>`;
}

/* ---------- customer form ---------- */
A.customerForm = (id) => {
  const c = id ? getCustomer(id) : null;
  const p = (c && c.plan) || { freq: 'weekly', day: DAYS[new Date().getDay()], price: '' };
  const pool = (c && c.pool) || {}, access = (c && c.access) || {};
  openModal(c ? 'Edit customer' : 'New customer', `
    <div class="field"><label>Name *</label><input id="f-name" value="${esc(c ? c.name : '')}" placeholder="Jane Smith"></div>
    <div class="field"><label>Service address</label><input id="f-address" value="${esc(c ? c.address : '')}" placeholder="123 Palm Ave"></div>
    <div class="field-grid">
      <div class="field"><label>Phone</label><input id="f-phone" type="tel" value="${esc(c ? c.phone : '')}"></div>
      <div class="field"><label>Email</label><input id="f-email" type="email" value="${esc(c ? c.email : '')}"></div>
    </div>
    <h3 style="margin:8px 0 10px;font-size:14px">Service plan</h3>
    <div class="field-grid three">
      <div class="field"><label>Frequency</label>
        <select id="f-freq">
          ${['weekly', 'biweekly', 'monthly', 'none'].map(f => `<option value="${f}" ${p.freq === f ? 'selected' : ''}>${{ weekly: 'Weekly', biweekly: 'Bi-weekly', monthly: 'Monthly', none: 'None' }[f]}</option>`).join('')}
        </select></div>
      <div class="field"><label>Day</label>
        <select id="f-day">${DAYS.map((d, i) => `<option value="${d}" ${p.day === d ? 'selected' : ''}>${DAY_NAMES[i]}</option>`).join('')}</select></div>
      <div class="field"><label>$/visit</label><input id="f-price" type="number" min="0" step="1" value="${esc(p.price)}"></div>
    </div>
    <div class="field-grid">
      <div class="field"><label>Assigned tech</label>
        <select id="f-tech"><option value="">Unassigned</option>
          ${DB.techs.map(t => `<option value="${t.id}" ${c && c.tech === t.id ? 'selected' : ''}>${esc(t.name)}</option>`).join('')}
        </select></div>
      <div class="field"><label>Status</label>
        <select id="f-status">
          <option value="active" ${!c || c.status === 'active' ? 'selected' : ''}>Active</option>
          <option value="paused" ${c && c.status === 'paused' ? 'selected' : ''}>Paused</option>
        </select></div>
    </div>
    <h3 style="margin:8px 0 10px;font-size:14px">Pool</h3>
    <div class="field-grid three">
      <div class="field"><label>Gallons</label><input id="f-gallons" type="number" min="0" value="${esc(pool.gallons)}"></div>
      <div class="field"><label>Type</label>
        <select id="f-ptype">${['Chlorine', 'Saltwater', 'Spa'].map(t => `<option ${pool.type === t ? 'selected' : ''}>${t}</option>`).join('')}</select></div>
      <div class="field"><label>Surface</label><input id="f-surface" value="${esc(pool.surface)}" placeholder="Plaster"></div>
    </div>
    <div class="field"><label>Equipment</label><input id="f-equipment" value="${esc(pool.equipment)}" placeholder="Pentair pump, cartridge filter"></div>
    <h3 style="margin:8px 0 10px;font-size:14px">Access</h3>
    <div class="field-grid">
      <div class="field"><label>Gate code</label><input id="f-gate" value="${esc(access.gate)}"></div>
      <div class="field"><label>Pets</label><input id="f-pet" value="${esc(access.pet)}" placeholder="Dog — friendly"></div>
    </div>
    <div class="field"><label>Access notes</label><textarea id="f-anotes">${esc(access.notes)}</textarea></div>
  `, `
    <button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn primary" onclick="A.saveCustomer('${id || ''}')">${c ? 'Save changes' : 'Add customer'}</button>`);
};

A.saveCustomer = (id) => {
  const name = $('#f-name').value.trim();
  if (!name) { toast('Name is required'); return; }
  const data = {
    name,
    address: $('#f-address').value.trim(),
    phone: $('#f-phone').value.trim(),
    email: $('#f-email').value.trim(),
    plan: {
      freq: $('#f-freq').value,
      day: $('#f-day').value,
      price: Number($('#f-price').value) || 0
    },
    tech: $('#f-tech').value,
    pool: {
      gallons: Number($('#f-gallons').value) || 0,
      type: $('#f-ptype').value,
      surface: $('#f-surface').value.trim(),
      equipment: $('#f-equipment').value.trim()
    },
    access: {
      gate: $('#f-gate').value.trim(),
      pet: $('#f-pet').value.trim(),
      notes: $('#f-anotes').value.trim()
    },
    status: $('#f-status').value
  };
  if (id) {
    const c = getCustomer(id);
    Object.assign(c, data);
  } else {
    DB.customers.push(Object.assign({ id: uid('c'), createdAt: todayISO() }, data));
  }
  save('customers');
  closeModal();
  toast(id ? 'Customer updated' : 'Customer added');
  render();
};

A.deleteCustomer = (id) => {
  const c = getCustomer(id);
  confirmModal(`Delete ${esc(c.name)}?`,
    'This removes the customer and keeps their visits and invoices orphaned. This cannot be undone.', () => {
      DB.customers = DB.customers.filter(x => x.id !== id);
      save('customers');
      state.clientId = null;
      toast('Customer deleted');
      render();
    });
};

/* ---------- visit logging ---------- */
const TASKS = ['Skim & net', 'Brush walls', 'Vacuum', 'Empty baskets', 'Clean filter', 'Test water', 'Add chemicals', 'Equipment check'];
const CHEM_NAMES = ['Liquid chlorine', 'Chlorine tabs', 'Cal-hypo shock', 'Muriatic acid', 'Soda ash', 'Baking soda', 'Calcium chloride', 'Cyanuric acid', 'Pool salt', 'Algaecide', 'Clarifier', 'DE powder', 'Other'];
const CHEM_UNITS = ['fl oz', 'oz', 'lb', 'gal', 'qt', 'cups', 'tabs'];

A.readingInput = (el, key) => {
  const s = readingState(key, el.value);
  el.classList.remove('reading-low', 'reading-high', 'reading-ok');
  if (s === 'low') el.classList.add('reading-low');
  if (s === 'high') el.classList.add('reading-high');
  if (s === 'ok') el.classList.add('reading-ok');
};
A.toggleChip = (el) => el.classList.toggle('on');
A.addChemRow = (name, qty, unit) => {
  const wrap = $('#chem-rows');
  const row = document.createElement('div');
  row.className = 'field-grid three chem-row';
  row.style.alignItems = 'end';
  row.innerHTML = `
    <div class="field"><label>Chemical</label>
      <select class="ch-name">${CHEM_NAMES.map(n => `<option ${n === name ? 'selected' : ''}>${n}</option>`).join('')}</select></div>
    <div class="field"><label>Qty</label><input class="ch-qty" type="number" min="0" step="0.1" value="${esc(qty || '')}"></div>
    <div class="field" style="display:flex;gap:6px;align-items:end">
      <div style="flex:1"><label>Unit</label>
        <select class="ch-unit">${CHEM_UNITS.map(u => `<option ${u === unit ? 'selected' : ''}>${u}</option>`).join('')}</select></div>
      <button class="btn danger sm" style="margin-bottom:13px" onclick="this.closest('.chem-row').remove()">✕</button>
    </div>`;
  wrap.appendChild(row);
};

A.visitForm = (customerId, dateISO, visitId) => {
  const c = getCustomer(customerId);
  if (!c) return;
  const existing = visitId ? DB.visits.find(v => v.id === visitId) : null;
  const date = (existing && existing.date) || dateISO || todayISO();
  const r = (existing && existing.readings) || {};
  openModal(`Log visit — ${esc(c.name)}`, `
    <div class="field-grid">
      <div class="field"><label>Date</label><input id="v-date" type="date" value="${date}"></div>
      <div class="field"><label>Tech</label>
        <select id="v-tech"><option value="">Unassigned</option>
          ${DB.techs.map(t => `<option value="${t.id}" ${(existing ? existing.techId : c.tech) === t.id ? 'selected' : ''}>${esc(t.name)}</option>`).join('')}
        </select></div>
    </div>
    <h3 style="margin:6px 0 10px;font-size:14px">Chemistry readings</h3>
    <div class="field-grid three">
      ${Object.keys(RANGES).map(k => `
        <div class="field"><label>${RANGES[k].label.split(' / ')[0]}${RANGES[k].unit ? ' (' + RANGES[k].unit + ')' : ''}</label>
          <input id="v-${k}" type="number" step="any" inputmode="decimal" value="${esc(r[k] != null ? r[k] : '')}"
            placeholder="${RANGES[k].min}–${RANGES[k].max}" oninput="A.readingInput(this,'${k}')"></div>`).join('')}
    </div>
    <div class="hint" style="margin:-4px 0 12px">Blue = below ideal · red = above ideal · green = in range.</div>
    <h3 style="margin:6px 0 10px;font-size:14px">Tasks completed</h3>
    <div class="chip-row" id="task-chips">
      ${TASKS.map(t => `<span class="chip ${existing && (existing.tasks || []).includes(t) ? 'on' : ''}"
        data-task="${esc(t)}" onclick="A.toggleChip(this)">${esc(t)}</span>`).join('')}
    </div>
    <h3 style="margin:16px 0 6px;font-size:14px">Chemicals added</h3>
    <div id="chem-rows"></div>
    <button class="btn ghost sm" onclick="A.addChemRow()">＋ Add chemical</button>
    <div class="field" style="margin-top:14px"><label>Notes</label>
      <textarea id="v-notes" placeholder="Water clear, filter pressure normal…">${esc(existing ? existing.notes : '')}</textarea></div>
  `, `
    <button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn primary" onclick="A.saveVisit('${customerId}','${existing ? existing.id : ''}')">Save visit</button>`);
  // seed chem rows + color existing readings
  ((existing && existing.chemicals) || []).forEach(ch => A.addChemRow(ch.name, ch.qty, ch.unit));
  Object.keys(RANGES).forEach(k => { const el = $('#v-' + k); if (el && el.value !== '') A.readingInput(el, k); });
};

A.saveVisit = (customerId, visitId) => {
  const date = $('#v-date').value;
  if (!date) { toast('Pick a date'); return; }
  const readings = {};
  Object.keys(RANGES).forEach(k => { readings[k] = $('#v-' + k).value.trim(); });
  const tasks = Array.from(document.querySelectorAll('#task-chips .chip.on')).map(el => el.dataset.task);
  const chemicals = Array.from(document.querySelectorAll('.chem-row')).map(row => ({
    name: row.querySelector('.ch-name').value,
    qty: Number(row.querySelector('.ch-qty').value) || 0,
    unit: row.querySelector('.ch-unit').value
  })).filter(ch => ch.qty > 0);
  const data = {
    customerId, date,
    techId: $('#v-tech').value,
    readings, tasks, chemicals,
    notes: $('#v-notes').value.trim()
  };
  // one visit per customer+date: replace an existing one
  const dupe = DB.visits.find(v => v.customerId === customerId && v.date === date && v.id !== visitId);
  if (dupe) DB.visits = DB.visits.filter(v => v.id !== dupe.id);
  if (visitId) {
    const v = DB.visits.find(x => x.id === visitId);
    if (v) Object.assign(v, data);
  } else {
    DB.visits.push(Object.assign({ id: uid('v'), createdAt: todayISO() }, data));
  }
  save('visits');
  closeModal();
  toast('Visit saved');
  render();
};

A.visitDetail = (visitId) => {
  const v = DB.visits.find(x => x.id === visitId);
  if (!v) return;
  const c = getCustomer(v.customerId);
  const rows = Object.keys(RANGES).map(k => {
    const val = (v.readings || {})[k];
    const s = readingState(k, val);
    if (val === '' || val == null) return '';
    const pill = s === 'ok' ? '<span class="pill green">In range</span>'
      : s === 'low' ? '<span class="pill aqua">Low</span>' : '<span class="pill red">High</span>';
    return `<tr><td>${RANGES[k].label}</td><td class="num"><b>${esc(val)}</b> ${RANGES[k].unit}</td>
      <td class="num">${RANGES[k].min}–${RANGES[k].max}</td><td style="text-align:right">${pill}</td></tr>`;
  }).join('');
  openModal(`Visit — ${fmtDate(v.date)}`, `
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
      <span class="pill gray">${esc(c ? c.name : 'Unknown customer')}</span>
      <span class="pill" style="background:${techColor(v.techId)}22;color:${techColor(v.techId)}">${esc(techName(v.techId))}</span>
      ${visitBalancePill(v)}
    </div>
    ${rows ? `<table class="simple"><tr><th>Reading</th><th class="num">Value</th><th class="num">Ideal</th><th></th></tr>${rows}</table>` : '<div class="empty">No readings recorded.</div>'}
    ${(v.tasks || []).length ? `<h3 style="margin:14px 0 8px;font-size:14px">Tasks</h3>
      <div class="chip-row">${v.tasks.map(t => `<span class="chip on">${esc(t)}</span>`).join('')}</div>` : ''}
    ${(v.chemicals || []).length ? `<h3 style="margin:14px 0 8px;font-size:14px">Chemicals added</h3>
      <table class="simple">${v.chemicals.map(ch => `<tr><td>${esc(ch.name)}</td><td class="num">${esc(ch.qty)} ${esc(ch.unit)}</td></tr>`).join('')}</table>` : ''}
    ${v.notes ? `<h3 style="margin:14px 0 6px;font-size:14px">Notes</h3><p style="font-size:14px;color:var(--muted)">${esc(v.notes)}</p>` : ''}
  `, `
    <button class="btn danger" onclick="A.deleteVisit('${v.id}')">Delete</button>
    <span style="flex:1"></span>
    <button class="btn ghost" onclick="closeModal();A.visitForm('${v.customerId}',null,'${v.id}')">Edit</button>
    <button class="btn primary" onclick="closeModal()">Done</button>`);
};

A.deleteVisit = (id) => {
  confirmModal('Delete this visit?', 'The service record will be removed permanently.', () => {
    DB.visits = DB.visits.filter(v => v.id !== id);
    save('visits');
    closeModal();
    toast('Visit deleted');
    render();
  });
};

/* ---------- invoices ---------- */
function nextInvoiceNumber() {
  let max = 1000;
  for (const i of DB.invoices) {
    const m = String(i.number || '').match(/(\d+)\s*$/);
    if (m) max = Math.max(max, Number(m[1]));
  }
  return 'INV-' + (max + 1);
}
function invoiceStatusPill(i) {
  if (i.status === 'paid') return '<span class="pill green">Paid</span>';
  if (i.dueDate && i.dueDate < todayISO()) return '<span class="pill red">Overdue</span>';
  return '<span class="pill amber">Unpaid</span>';
}
function invoiceRow(i) {
  const c = getCustomer(i.customerId);
  return `<div class="row" onclick="A.invoiceDetail('${i.id}')">
    <span class="avatar" style="background:${i.status === 'paid' ? 'var(--green)' : 'var(--amber)'};width:36px;height:36px;font-size:12px">$</span>
    <div class="r-main"><div class="r-title">${esc(i.number)} — ${esc(c ? c.name : 'Unknown')}</div>
      <div class="r-sub">Issued ${fmtDateShort(i.date)} · due ${fmtDateShort(i.dueDate)}</div></div>
    <div class="r-side"><b>${money(i.total)}</b>${invoiceStatusPill(i)}</div>
  </div>`;
}

A.invoiceFilter = (f) => { state.invoiceFilter = f; render(); };

function viewInvoices() {
  const today = todayISO();
  const outstanding = DB.invoices.filter(i => i.status === 'unpaid').reduce((s, i) => s + Number(i.total || 0), 0);
  const paidMTD = DB.invoices.filter(i => i.status === 'paid' && sameMonth(i.paidDate, today)).reduce((s, i) => s + Number(i.total || 0), 0);
  let list = DB.invoices.slice().sort((a, b) => b.date.localeCompare(a.date));
  if (state.invoiceFilter === 'unpaid') list = list.filter(i => i.status === 'unpaid');
  if (state.invoiceFilter === 'paid') list = list.filter(i => i.status === 'paid');
  return `
    <div class="grid tiles" style="grid-template-columns:1fr 1fr">
      <div class="tile"><div class="t-label">Outstanding</div><div class="t-num" style="color:var(--amber)">${money(outstanding)}</div></div>
      <div class="tile"><div class="t-label">Paid (MTD)</div><div class="t-num" style="color:var(--green)">${money(paidMTD)}</div></div>
    </div>
    <div class="section-head">
      <div class="chip-row">
        ${['all', 'unpaid', 'paid'].map(f => `<span class="chip ${state.invoiceFilter === f ? 'on' : ''}"
          onclick="A.invoiceFilter('${f}')">${f[0].toUpperCase() + f.slice(1)}</span>`).join('')}
      </div>
      <button class="btn primary sm" onclick="A.invoiceForm()">＋ New invoice</button>
    </div>
    <div class="card">${list.length ? list.map(invoiceRow).join('') : '<div class="empty"><span class="big">🧾</span>No invoices here.</div>'}</div>`;
}

A.addItemRow = (desc, amount) => {
  const wrap = $('#item-rows');
  const row = document.createElement('div');
  row.className = 'item-row';
  row.style.cssText = 'display:flex;gap:8px;margin-bottom:8px;align-items:center';
  row.innerHTML = `
    <input class="it-desc" placeholder="Description" value="${esc(desc || '')}" style="flex:2;padding:9px 11px;border:1.5px solid var(--line);border-radius:9px">
    <input class="it-amt" type="number" step="0.01" min="0" placeholder="0.00" value="${esc(amount != null ? amount : '')}"
      oninput="A.invTotal()" style="flex:1;max-width:110px;padding:9px 11px;border:1.5px solid var(--line);border-radius:9px">
    <button class="btn danger sm" onclick="this.closest('.item-row').remove();A.invTotal()">✕</button>`;
  wrap.appendChild(row);
};
A.invTotal = () => {
  const total = Array.from(document.querySelectorAll('.item-row .it-amt'))
    .reduce((s, el) => s + (Number(el.value) || 0), 0);
  const el = $('#inv-total');
  if (el) el.textContent = money(total);
  return total;
};
A.addMonthlyCharge = () => {
  const cid = $('#i-customer').value;
  const c = getCustomer(cid);
  if (!c || !c.plan || !c.plan.price) { toast('Pick a customer with a plan price first'); return; }
  const freq = { weekly: 'Weekly', biweekly: 'Bi-weekly', monthly: 'Monthly' }[c.plan.freq] || '';
  A.addItemRow(`Monthly pool service${freq ? ' (' + freq.toLowerCase() + ' plan)' : ''}`, (Number(c.plan.price) * 4).toFixed(2));
  A.invTotal();
};

A.invoiceForm = (id, presetCustomerId) => {
  const inv = id ? DB.invoices.find(i => i.id === id) : null;
  if (!DB.customers.length) { toast('Add a customer first'); return; }
  const date = inv ? inv.date : todayISO();
  const due = inv ? inv.dueDate : addDays(todayISO(), 14);
  openModal(inv ? 'Edit invoice' : 'New invoice', `
    <div class="field"><label>Customer *</label>
      <select id="i-customer">${DB.customers.slice().sort((a, b) => a.name.localeCompare(b.name)).map(c =>
        `<option value="${c.id}" ${(inv ? inv.customerId : presetCustomerId) === c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join('')}
      </select></div>
    <div class="field-grid three">
      <div class="field"><label>Invoice #</label><input id="i-number" value="${esc(inv ? inv.number : nextInvoiceNumber())}"></div>
      <div class="field"><label>Date</label><input id="i-date" type="date" value="${date}"></div>
      <div class="field"><label>Due date</label><input id="i-due" type="date" value="${due}"></div>
    </div>
    <h3 style="margin:8px 0 8px;font-size:14px">Line items</h3>
    <div id="item-rows"></div>
    <div class="btn-row">
      <button class="btn ghost sm" onclick="A.addItemRow();">＋ Add line</button>
      <button class="btn ghost sm" onclick="A.addMonthlyCharge()">＋ Add monthly service charge</button>
    </div>
    <div style="display:flex;justify-content:flex-end;align-items:baseline;gap:10px;margin-top:16px;
      border-top:1.5px solid var(--line);padding-top:12px">
      <span style="font-size:13px;color:var(--muted);font-weight:700">TOTAL</span>
      <span id="inv-total" style="font-size:22px;font-weight:800">$0.00</span>
    </div>
  `, `
    <button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn primary" onclick="A.saveInvoice('${id || ''}')">${inv ? 'Save changes' : 'Create invoice'}</button>`);
  const items = (inv && inv.items && inv.items.length) ? inv.items : [{ desc: '', amount: '' }];
  items.forEach(it => A.addItemRow(it.desc, it.amount === '' ? '' : it.amount));
  A.invTotal();
};

A.saveInvoice = (id) => {
  const items = Array.from(document.querySelectorAll('.item-row')).map(row => ({
    desc: row.querySelector('.it-desc').value.trim(),
    amount: Number(row.querySelector('.it-amt').value) || 0
  })).filter(it => it.desc || it.amount);
  if (!items.length) { toast('Add at least one line item'); return; }
  const data = {
    customerId: $('#i-customer').value,
    number: $('#i-number').value.trim() || nextInvoiceNumber(),
    date: $('#i-date').value || todayISO(),
    dueDate: $('#i-due').value || addDays(todayISO(), 14),
    items,
    total: items.reduce((s, it) => s + it.amount, 0)
  };
  if (id) {
    const inv = DB.invoices.find(i => i.id === id);
    if (inv) Object.assign(inv, data);
  } else {
    DB.invoices.push(Object.assign({ id: uid('i'), status: 'unpaid', paidDate: null }, data));
  }
  save('invoices');
  closeModal();
  toast(id ? 'Invoice updated' : 'Invoice created');
  render();
};

A.invoiceDetail = (id) => {
  const i = DB.invoices.find(x => x.id === id);
  if (!i) return;
  const c = getCustomer(i.customerId);
  openModal(`Invoice ${esc(i.number)}`, `
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
      <span class="pill gray">${esc(c ? c.name : 'Unknown customer')}</span>
      ${invoiceStatusPill(i)}
      ${i.status === 'paid' && i.paidDate ? `<span class="pill gray">paid ${fmtDateShort(i.paidDate)}</span>` : ''}
    </div>
    <dl class="kv" style="margin-bottom:14px">
      <dt>Issued</dt><dd>${fmtDate(i.date)}</dd>
      <dt>Due</dt><dd>${fmtDate(i.dueDate)}</dd>
    </dl>
    <table class="simple">
      <tr><th>Item</th><th class="num">Amount</th></tr>
      ${(i.items || []).map(it => `<tr><td>${esc(it.desc)}</td><td class="num">${money(it.amount)}</td></tr>`).join('')}
      <tr><td style="font-weight:800">Total</td><td class="num" style="font-weight:800">${money(i.total)}</td></tr>
    </table>
  `, `
    <button class="btn danger" onclick="A.deleteInvoice('${i.id}')">Delete</button>
    <span style="flex:1"></span>
    <button class="btn ghost" onclick="closeModal();A.invoiceForm('${i.id}')">Edit</button>
    <button class="btn ${i.status === 'paid' ? 'ghost' : 'primary'}" onclick="A.togglePaid('${i.id}')">
      ${i.status === 'paid' ? 'Mark unpaid' : '✓ Mark paid'}</button>`);
};

A.togglePaid = (id) => {
  const i = DB.invoices.find(x => x.id === id);
  if (!i) return;
  if (i.status === 'paid') { i.status = 'unpaid'; i.paidDate = null; }
  else { i.status = 'paid'; i.paidDate = todayISO(); }
  save('invoices');
  closeModal();
  toast(i.status === 'paid' ? 'Marked paid 💵' : 'Marked unpaid');
  render();
};

A.deleteInvoice = (id) => {
  confirmModal('Delete this invoice?', 'This cannot be undone.', () => {
    DB.invoices = DB.invoices.filter(i => i.id !== id);
    save('invoices');
    closeModal();
    toast('Invoice deleted');
    render();
  });
};

/* ---------- team ---------- */
function viewTeam() {
  return `
    <div class="section-head"><h2>${DB.techs.length} team member${DB.techs.length === 1 ? '' : 's'}</h2>
      <button class="btn primary sm" onclick="A.techForm()">＋ Add tech</button></div>
    <div class="card">
      ${DB.techs.length ? DB.techs.map(t => {
        const count = DB.customers.filter(c => c.tech === t.id).length;
        return `<div class="row" onclick="A.techForm('${t.id}')">
          <span class="avatar" style="background:${t.color}">${esc(initials(t.name))}</span>
          <div class="r-main"><div class="r-title">${esc(t.name)}</div><div class="r-sub">${esc(t.phone || 'No phone')}</div></div>
          <div class="r-side"><span class="pill aqua">${count} account${count === 1 ? '' : 's'}</span></div>
        </div>`;
      }).join('') : '<div class="empty"><span class="big">👷</span>No techs yet — add your crew.</div>'}
    </div>`;
}

A.pickColor = (el) => {
  document.querySelectorAll('.color-dots .dot').forEach(d => d.classList.remove('on'));
  el.classList.add('on');
};
A.techForm = (id) => {
  const t = id ? getTech(id) : null;
  const color = t ? t.color : TECH_PALETTE[DB.techs.length % TECH_PALETTE.length];
  openModal(t ? 'Edit tech' : 'Add tech', `
    <div class="field"><label>Name *</label><input id="t-name" value="${esc(t ? t.name : '')}" placeholder="Mike Rivera"></div>
    <div class="field"><label>Phone</label><input id="t-phone" type="tel" value="${esc(t ? t.phone : '')}"></div>
    <div class="field"><label>Route color</label>
      <div class="color-dots">${TECH_PALETTE.map(c =>
        `<span class="dot ${c === color ? 'on' : ''}" data-color="${c}" style="background:${c}" onclick="A.pickColor(this)"></span>`).join('')}
      </div></div>
  `, `
    ${t ? `<button class="btn danger" onclick="A.deleteTech('${t.id}')">Delete</button><span style="flex:1"></span>` : ''}
    <button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn primary" onclick="A.saveTech('${id || ''}')">${t ? 'Save' : 'Add tech'}</button>`);
};
A.saveTech = (id) => {
  const name = $('#t-name').value.trim();
  if (!name) { toast('Name is required'); return; }
  const dot = document.querySelector('.color-dots .dot.on');
  const data = { name, phone: $('#t-phone').value.trim(), color: dot ? dot.dataset.color : TECH_PALETTE[0] };
  if (id) Object.assign(getTech(id), data);
  else DB.techs.push(Object.assign({ id: uid('t') }, data));
  save('techs');
  closeModal();
  toast(id ? 'Tech updated' : 'Tech added');
  render();
};
A.deleteTech = (id) => {
  const count = DB.customers.filter(c => c.tech === id).length;
  confirmModal('Remove this tech?', count ? `${count} customer(s) will become unassigned.` : 'This cannot be undone.', () => {
    DB.techs = DB.techs.filter(t => t.id !== id);
    DB.customers.forEach(c => { if (c.tech === id) c.tech = ''; });
    save('techs'); save('customers');
    closeModal();
    toast('Tech removed');
    render();
  });
};

/* ---------- reports ---------- */
function viewReports() {
  const today = todayISO();
  const now = fromISO(today);
  const revMTD = DB.invoices.filter(i => i.status === 'paid' && sameMonth(i.paidDate, today)).reduce((s, i) => s + Number(i.total || 0), 0);
  const outstanding = DB.invoices.filter(i => i.status === 'unpaid').reduce((s, i) => s + Number(i.total || 0), 0);
  const wk = addDays(today, -6);
  const visits7 = DB.visits.filter(v => v.date >= wk && v.date <= today).length;
  const active = DB.customers.filter(c => c.status === 'active').length;

  // last 6 months revenue
  const months = [];
  for (let m = 5; m >= 0; m--) {
    const d = new Date(now.getFullYear(), now.getMonth() - m, 1);
    const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
    const total = DB.invoices.filter(i => i.status === 'paid' && (i.paidDate || '').slice(0, 7) === key)
      .reduce((s, i) => s + Number(i.total || 0), 0);
    months.push({ label: MONTHS[d.getMonth()], total });
  }
  const maxRev = Math.max(1, ...months.map(m => m.total));

  // chemical usage this month
  const usage = {};
  DB.visits.filter(v => sameMonth(v.date, today)).forEach(v =>
    (v.chemicals || []).forEach(ch => {
      const key = ch.name + '|' + ch.unit;
      usage[key] = (usage[key] || 0) + (Number(ch.qty) || 0);
    }));
  const usageRows = Object.entries(usage).sort((a, b) => b[1] - a[1]).slice(0, 6);

  return `
    <div class="grid tiles">
      <div class="tile accent"><div class="t-label">Revenue (MTD)</div><div class="t-num">${money(revMTD)}</div></div>
      <div class="tile"><div class="t-label">Outstanding</div><div class="t-num">${money(outstanding)}</div></div>
      <div class="tile"><div class="t-label">Visits (7 days)</div><div class="t-num">${visits7}</div></div>
      <div class="tile"><div class="t-label">Active accounts</div><div class="t-num">${active}</div></div>
    </div>
    <div class="section-head"><h2>Revenue — last 6 months</h2></div>
    <div class="card">
      <div class="bars">
        ${months.map(m => `
          <div class="bar-col">
            <span class="bar-v">${m.total ? '$' + Math.round(m.total).toLocaleString() : ''}</span>
            <div class="bar" style="height:${Math.max(2, Math.round(m.total / maxRev * 100))}%"></div>
            <span class="bar-l">${m.label}</span>
          </div>`).join('')}
      </div>
    </div>
    <div class="section-head"><h2>Chemical usage this month</h2></div>
    <div class="card">
      ${usageRows.length ? `<table class="simple">
        <tr><th>Chemical</th><th class="num">Used</th></tr>
        ${usageRows.map(([key, qty]) => {
          const [name, unit] = key.split('|');
          return `<tr><td>${esc(name)}</td><td class="num"><b>${r1(qty)}</b> ${esc(unit)}</td></tr>`;
        }).join('')}</table>` : '<div class="empty">No chemicals logged this month.</div>'}
    </div>`;
}

/* ---------- tools (dosage calculator) ---------- */
A.doseParamChanged = () => {
  const param = $('#d-param').value;
  const cfg = DOSING[param];
  const cur = Number($('#d-current').value);
  const tgt = Number($('#d-target').value);
  const lowering = !isNaN(cur) && !isNaN(tgt) && tgt < cur;
  let prods = lowering ? (cfg.lowerProducts || []) : cfg.raise.filter(p => !p.formula || p.formula === 'salt');
  const wrap = $('#d-product-wrap');
  if (prods.length > 1) {
    wrap.style.display = '';
    $('#d-product').innerHTML = prods.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
  } else {
    wrap.style.display = 'none';
    $('#d-product').innerHTML = prods.length ? `<option value="${prods[0].id}">${esc(prods[0].name)}</option>` : '';
  }
};
A.calcDose = () => {
  const param = $('#d-param').value;
  const gallons = Number($('#d-gallons').value);
  const current = Number($('#d-current').value);
  const target = Number($('#d-target').value);
  const product = $('#d-product').value;
  const res = calcDose(param, gallons, current, target, product);
  const box = $('#d-result');
  box.style.display = '';
  if (res.err) {
    box.innerHTML = `<div class="r-note" style="color:var(--red);font-weight:700">${esc(res.err)}</div>`;
    return;
  }
  box.innerHTML = `
    <div class="r-big">${esc(res.amount)}</div>
    <div style="font-weight:700;margin-top:2px">${esc(res.product)}</div>
    ${res.note ? `<div class="r-note">${esc(res.note)}</div>` : ''}`;
};

function viewTools() {
  return `
    <div class="section-head"><h2>Ideal water chemistry</h2></div>
    <div class="card">
      <table class="simple">
        <tr><th>Reading</th><th class="num">Ideal</th><th>Notes</th></tr>
        ${Object.keys(RANGES).map(k => {
          const r = RANGES[k];
          return `<tr><td>${r.label}</td><td class="num"><b>${r.min}–${r.max}</b> ${r.unit}</td>
            <td style="color:var(--muted);font-size:13px">${r.note || ''}</td></tr>`;
        }).join('')}
      </table>
    </div>

    <div class="section-head"><h2>Dosage calculator</h2></div>
    <div class="card">
      <div class="field"><label>Parameter</label>
        <select id="d-param" onchange="A.doseParamChanged()">
          ${Object.keys(DOSING).map(p => `<option value="${p}">${DOSING[p].label}</option>`).join('')}
        </select></div>
      <div class="field-grid three">
        <div class="field"><label>Pool volume (gal)</label><input id="d-gallons" type="number" min="0" inputmode="numeric" value="10000"></div>
        <div class="field"><label>Current</label><input id="d-current" type="number" step="any" inputmode="decimal" oninput="A.doseParamChanged()"></div>
        <div class="field"><label>Target</label><input id="d-target" type="number" step="any" inputmode="decimal" oninput="A.doseParamChanged()"></div>
      </div>
      <div class="field" id="d-product-wrap"><label>Product</label><select id="d-product"></select></div>
      <button class="btn primary block" onclick="A.calcDose()">Calculate dose</button>
      <div class="result-box" id="d-result" style="display:none"></div>
      <div class="disclaimer">⚠️ Estimates for typical conditions — add ~¾, run the pump, retest.
        Follow product labels; never mix chemicals.</div>
    </div>`;
}

/* ---------- settings ---------- */
function viewSettings() {
  const co = DB.company || {};
  return `
    <div class="card"><h3>Company</h3>
      <div class="field"><label>Company name</label><input id="s-name" value="${esc(co.name)}"></div>
      <div class="field-grid">
        <div class="field"><label>Phone</label><input id="s-phone" type="tel" value="${esc(co.phone)}"></div>
        <div class="field"><label>Email</label><input id="s-email" type="email" value="${esc(co.email)}"></div>
      </div>
      <div class="field"><label>Service area / address</label><input id="s-address" value="${esc(co.address)}"></div>
      <button class="btn primary" onclick="A.saveCompany()">Save company info</button>
    </div>

    <div class="card"><h3>Data</h3>
      <p class="hint" style="margin-bottom:12px">
        Storage: ${store.ok
          ? '<span class="pill green">Saved on this device</span> Data persists in this browser only — it does not sync between devices.'
          : '<span class="pill red">Session only</span> This browser blocked storage; data will be lost when you close the app.'}
      </p>
      <div class="btn-row">
        <button class="btn ghost sm" onclick="A.exportCustomersCSV()">⬇ Customers (.csv)</button>
        <button class="btn ghost sm" onclick="A.exportInvoicesCSV()">⬇ Invoices (.csv)</button>
        <button class="btn ghost sm" onclick="A.exportBackup()">⬇ Full backup (.json)</button>
      </div>
    </div>

    <div class="card"><h3>Danger zone</h3>
      <div class="btn-row">
        <button class="btn ghost sm" onclick="A.loadSample()">Load sample data</button>
        <button class="btn danger sm" onclick="A.resetAll()">Reset everything</button>
      </div>
    </div>
    <p class="hint" style="margin-top:14px;text-align:center">SPS Pools &amp; Spas Back Office · works offline once installed</p>`;
}

A.saveCompany = () => {
  DB.company = {
    name: $('#s-name').value.trim() || 'SPS Pools & Spas',
    phone: $('#s-phone').value.trim(),
    email: $('#s-email').value.trim(),
    address: $('#s-address').value.trim()
  };
  save('company');
  toast('Company info saved');
  render();
};

/* CSV / JSON export */
function download(filename, text, mime) {
  const blob = new Blob([text], { type: mime || 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
const csvCell = (v) => {
  const s = String(v == null ? '' : v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};
A.exportCustomersCSV = () => {
  const head = ['Name', 'Address', 'Phone', 'Email', 'Plan', 'Day', 'Price/visit', 'Tech', 'Status', 'Gallons', 'Pool type', 'Since'];
  const rows = DB.customers.map(c => [
    c.name, c.address, c.phone, c.email,
    (c.plan || {}).freq || '', (c.plan || {}).day || '', (c.plan || {}).price || '',
    techName(c.tech), c.status, (c.pool || {}).gallons || '', (c.pool || {}).type || '', c.createdAt
  ]);
  download('sps-customers.csv', [head, ...rows].map(r => r.map(csvCell).join(',')).join('\n'), 'text/csv');
  toast('Customers exported');
};
A.exportInvoicesCSV = () => {
  const head = ['Number', 'Customer', 'Date', 'Due date', 'Total', 'Status', 'Paid date'];
  const rows = DB.invoices.map(i => {
    const c = getCustomer(i.customerId);
    return [i.number, c ? c.name : '', i.date, i.dueDate, Number(i.total || 0).toFixed(2), i.status, i.paidDate || ''];
  });
  download('sps-invoices.csv', [head, ...rows].map(r => r.map(csvCell).join(',')).join('\n'), 'text/csv');
  toast('Invoices exported');
};
A.exportBackup = () => {
  download('sps-backup-' + todayISO() + '.json', JSON.stringify({
    exportedAt: new Date().toISOString(),
    company: DB.company, techs: DB.techs, customers: DB.customers,
    visits: DB.visits, invoices: DB.invoices
  }, null, 2), 'application/json');
  toast('Backup downloaded');
};

A.loadSample = () => {
  confirmModal('Load sample data?', 'Demo techs, customers, visits and invoices will be added on top of your current data.', () => {
    seedSampleData();
    closeModal();
    toast('Sample data loaded');
    render();
  });
};
A.resetAll = () => {
  confirmModal('Reset everything?', 'ALL customers, visits, invoices, techs and settings on this device will be permanently erased.', () => {
    Object.values(K).forEach(k => store.remove(k));
    location.reload();
  });
};

/* ---------- modal helpers ---------- */
function openModal(title, bodyHTML, footHTML) {
  $('#modal-root').innerHTML = `
    <div class="overlay" onclick="if(event.target===this)closeModal()">
      <div class="sheet">
        <div class="sheet-head"><h2>${title}</h2><button class="x" onclick="closeModal()">✕</button></div>
        <div class="sheet-body">${bodyHTML}</div>
        ${footHTML !== '' ? `<div class="sheet-foot">${footHTML || ''}</div>` : ''}
      </div>
    </div>`;
}
function closeModal() { $('#modal-root').innerHTML = ''; }
window.closeModal = closeModal;

let confirmCb = null;
function confirmModal(title, message, cb) {
  confirmCb = cb;
  openModal(title, `<p style="font-size:14.5px;color:var(--muted)">${message}</p>`, `
    <button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn danger" onclick="A.confirmYes()">Yes, do it</button>`);
}
A.confirmYes = () => { const cb = confirmCb; confirmCb = null; if (cb) cb(); };

/* ---------- sample data ---------- */
function seedSampleData() {
  const today = todayISO();
  const todayDay = DAYS[new Date().getDay()];
  const otherDay = DAYS[(new Date().getDay() + 2) % 7];

  const t1 = { id: uid('t'), name: 'Mike Rivera', phone: '(555) 201-4488', color: TECH_PALETTE[0] };
  const t2 = { id: uid('t'), name: 'Dana Brooks', phone: '(555) 201-9917', color: TECH_PALETTE[1] };
  DB.techs.push(t1, t2);

  const mk = (name, address, phone, freq, day, price, tech, gallons, type, extras) => Object.assign({
    id: uid('c'), name, address, phone, email: name.toLowerCase().replace(/[^a-z]+/g, '.') + '@example.com',
    plan: { freq, day, price }, tech,
    pool: Object.assign({ gallons, type, surface: 'Plaster', equipment: 'Single-speed pump, cartridge filter' }, (extras && extras.pool) || {}),
    access: Object.assign({ gate: '', pet: '', notes: '' }, (extras && extras.access) || {}),
    status: 'active', createdAt: addDays(today, -84)
  }, (extras && extras.top) || {});

  const c1 = mk('Harold Jenkins', '412 Cypress Bend Dr', '(555) 314-2210', 'weekly', todayDay, 45, t1.id, 15000, 'Chlorine',
    { access: { gate: '#4482', pet: 'Golden retriever — friendly', notes: 'Gate sticks; lift while pushing' } });
  const c2 = mk('Maria Delgado', '88 Bluewater Ct', '(555) 887-4451', 'weekly', todayDay, 50, t1.id, 12000, 'Saltwater',
    { pool: { equipment: 'Variable-speed pump, salt cell, DE filter' } });
  const c3 = mk('The Whitfields', '1509 Sandpiper Ln', '(555) 662-1078', 'biweekly', todayDay, 60, t2.id, 18000, 'Chlorine',
    { top: { createdAt: addDays(today, -28) }, access: { pet: 'Two cats (indoor)', gate: 'Keypad 7715' } });
  const c4 = mk('Sunrise HOA — Cabana Pool', '200 Sunrise Blvd', '(555) 440-9090', 'weekly', otherDay, 120, t2.id, 32000, 'Chlorine',
    { pool: { surface: 'Pebble', equipment: 'Dual pumps, sand filter, chlorinator' } });
  const c5 = mk('Grace Okafor', '77 Lagoon View Ter', '(555) 219-8834', 'monthly', todayDay, 85, t1.id, 10000, 'Spa',
    { top: { createdAt: addDays(today, -120) } });
  const c6 = mk('Tom Baxter', '963 Coral Reef Rd', '(555) 705-1123', 'weekly', otherDay, 45, t2.id, 14000, 'Chlorine',
    { top: { status: 'paused' } });
  DB.customers.push(c1, c2, c3, c4, c5, c6);

  DB.visits.push({
    id: uid('v'), customerId: c1.id, date: addDays(today, -7), techId: t1.id,
    readings: { fc: '2.5', ph: '7.5', ta: '95', cya: '40', ch: '250', salt: '' },
    tasks: ['Skim & net', 'Brush walls', 'Empty baskets', 'Test water'],
    chemicals: [{ name: 'Liquid chlorine', qty: 32, unit: 'fl oz' }],
    notes: 'Water clear. Filter pressure normal.', createdAt: addDays(today, -7)
  }, {
    id: uid('v'), customerId: c2.id, date: addDays(today, -7), techId: t1.id,
    readings: { fc: '4.5', ph: '7.9', ta: '110', cya: '70', ch: '300', salt: '3100' },
    tasks: ['Skim & net', 'Test water', 'Add chemicals', 'Equipment check'],
    chemicals: [{ name: 'Muriatic acid', qty: 16, unit: 'fl oz' }],
    notes: 'pH trending high — added acid, recheck next visit.', createdAt: addDays(today, -7)
  }, {
    id: uid('v'), customerId: c4.id, date: addDays(today, -3), techId: t2.id,
    readings: { fc: '1.5', ph: '7.4', ta: '85', cya: '35', ch: '220', salt: '' },
    tasks: ['Skim & net', 'Vacuum', 'Empty baskets', 'Test water', 'Add chemicals'],
    chemicals: [{ name: 'Liquid chlorine', qty: 1, unit: 'gal' }, { name: 'Baking soda', qty: 2, unit: 'lb' }],
    notes: 'Heavy leaf load after wind. HOA notified about tree trimming.', createdAt: addDays(today, -3)
  });

  const num = (n) => 'INV-' + n;
  DB.invoices.push({
    id: uid('i'), customerId: c1.id, number: num(1001), date: addDays(today, -20), dueDate: addDays(today, -6),
    items: [{ desc: 'Monthly pool service (weekly plan)', amount: 180 }], total: 180, status: 'unpaid', paidDate: null
  }, {
    id: uid('i'), customerId: c2.id, number: num(1002), date: addDays(today, -12), dueDate: addDays(today, 2),
    items: [{ desc: 'Monthly pool service (weekly plan)', amount: 200 }, { desc: 'Salt cell cleaning', amount: 35 }],
    total: 235, status: 'paid', paidDate: addDays(today, -4)
  }, {
    id: uid('i'), customerId: c4.id, number: num(1003), date: addDays(today, -5), dueDate: addDays(today, 9),
    items: [{ desc: 'Commercial pool service — monthly', amount: 480 }], total: 480, status: 'unpaid', paidDate: null
  });

  save('techs'); save('customers'); save('visits'); save('invoices');
}

/* ---------- first-run setup ---------- */
function showSetup() {
  $('#setup').hidden = false;
  $('#app').hidden = true;
  $('#setup').innerHTML = `
    <div class="setup-card">
      <div class="brand"><span class="brand-badge">SPS</span></div>
      <h1>Welcome to your back office</h1>
      <p class="lead">Customers, routes, service logs, invoices and reports — all on this device, online or off.</p>
      <div class="field"><label>Company name</label><input id="su-name" value="SPS Pools &amp; Spas"></div>
      <div class="field-grid">
        <div class="field"><label>Phone</label><input id="su-phone" type="tel" placeholder="(555) 555-0100"></div>
        <div class="field"><label>Email</label><input id="su-email" type="email" placeholder="office@spspools.com"></div>
      </div>
      <div class="field"><label>Service area</label><input id="su-address" placeholder="Palm Harbor & surrounding"></div>
      <button class="btn primary block" style="margin-bottom:10px" onclick="A.finishSetup(false)">Create back office</button>
      <button class="btn ghost block" onclick="A.finishSetup(true)">Start with sample data</button>
    </div>`;
}
A.finishSetup = (withSample) => {
  DB.company = {
    name: $('#su-name').value.trim() || 'SPS Pools & Spas',
    phone: $('#su-phone').value.trim(),
    email: $('#su-email').value.trim(),
    address: $('#su-address').value.trim()
  };
  save('company');
  if (withSample) seedSampleData();
  $('#setup').hidden = true;
  $('#app').hidden = false;
  render();
  toast(withSample ? 'Sample data loaded — explore away!' : 'Back office ready');
};

/* ---------- iOS add-to-home-screen hint ---------- */
function maybeShowIosHint() {
  const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const standalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  if (!isIos || standalone || store.get(K.iosHint, false)) return;
  const el = $('#ios-hint');
  el.hidden = false;
  el.innerHTML = `<span>📲 Install this app: tap <b>Share</b> then <b>Add to Home Screen</b>.</span>
    <button onclick="this.parentElement.hidden=true;A.dismissIosHint()">Got it</button>`;
}
A.dismissIosHint = () => store.set(K.iosHint, true);

/* ---------- init ---------- */
window.A = A;
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  });
}
buildNav();
if (!DB.company) showSetup();
else { $('#app').hidden = false; render(); }
maybeShowIosHint();
