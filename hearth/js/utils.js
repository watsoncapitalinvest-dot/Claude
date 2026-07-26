// utils.js — small helpers used everywhere

export const uid = (p = 'id') =>
  p + '_' + Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4);

// ---------- money ----------
export function money(n, { sign = false, cents = true } = {}) {
  const cur = window.Hearth?.state?.profile?.currency || 'USD';
  const symbols = { USD: '$', EUR: '€', GBP: '£', CAD: '$', AUD: '$', JPY: '¥', INR: '₹', MXN: '$' };
  const sym = symbols[cur] || '$';
  const v = Number(n || 0);
  const abs = Math.abs(v);
  const str = abs.toLocaleString(undefined, {
    minimumFractionDigits: cents ? 2 : 0,
    maximumFractionDigits: cents ? 2 : 0,
  });
  const s = (v < 0 ? '−' : sign && v > 0 ? '+' : '') + sym + str;
  return s;
}
export function moneyShort(n) {
  const v = Number(n || 0), a = Math.abs(v);
  const sym = { USD:'$',EUR:'€',GBP:'£',JPY:'¥',INR:'₹' }[window.Hearth?.state?.profile?.currency] || '$';
  let out;
  if (a >= 1_000_000) out = (v/1_000_000).toFixed(a>=10_000_000?0:1)+'M';
  else if (a >= 1000) out = (v/1000).toFixed(a>=10000?0:1)+'k';
  else out = a.toFixed(0);
  return (v<0?'−':'')+sym+out;
}

// ---------- dates ----------
export const DAY = 86400000;
export function today() { const d = new Date(); d.setHours(0,0,0,0); return d; }
export function iso(d) { // -> 'YYYY-MM-DD' in local time
  const x = (d instanceof Date) ? d : new Date(d);
  return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}-${String(x.getDate()).padStart(2,'0')}`;
}
export function parseISO(s) { const [y,m,d] = String(s).split('-').map(Number); return new Date(y, m-1, d); }
export function todayISO() { return iso(new Date()); }
export function monthKey(d = new Date()) { const x = (d instanceof Date)?d:parseISO(d); return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}`; }

const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const MONFULL = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

export function fmtDate(s, { withYear = false, weekday = false } = {}) {
  if (!s) return '';
  const d = (s instanceof Date) ? s : parseISO(s);
  const wd = weekday ? DOW[d.getDay()] + ' ' : '';
  return `${wd}${MON[d.getMonth()]} ${d.getDate()}${withYear ? ', ' + d.getFullYear() : ''}`;
}
export function fmtMonth(key) { const [y,m] = key.split('-').map(Number); return `${MONFULL[m-1]} ${y}`; }
export function relDay(s) {
  if (!s) return '';
  const d = parseISO(iso(s)); const t = today();
  const diff = Math.round((d - t) / DAY);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff === -1) return 'Yesterday';
  if (diff > 1 && diff <= 7) return `In ${diff} days`;
  if (diff < -1 && diff >= -7) return `${-diff} days ago`;
  if (diff < 0) return `${-diff} days ago`;
  return fmtDate(s, { withYear: d.getFullYear() !== t.getFullYear() });
}
export function daysUntil(s) { return Math.round((parseISO(iso(s)) - today()) / DAY); }
export const MONTHS = MONFULL;
export const DOW_LABELS = DOW;

// ---------- misc ----------
export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}
export function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }
export function sum(arr, f = x => x) { return arr.reduce((a, x) => a + (Number(f(x)) || 0), 0); }
export function groupBy(arr, f) { const m = {}; for (const x of arr) { const k = f(x); (m[k] ||= []).push(x); } return m; }
export function sortBy(arr, f, dir = 1) { return [...arr].sort((a, b) => { const x = f(a), y = f(b); return x < y ? -dir : x > y ? dir : 0; }); }

// tiny DOM builder
export function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k in el && k !== 'list') { try { el[k] = v; } catch { el.setAttribute(k, v); } }
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
