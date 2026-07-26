// views/parts.js — small shared render helpers
import { h } from '../utils.js';
import { personById } from '../store.js';

export function whoPill(personId) {
  const p = personById(personId);
  if (!p) return null;
  const initials = p.name.trim().slice(0, 2).toUpperCase();
  return h('span', { class: 'who-pill' },
    h('span', { class: 'av', style: { background: p.color } }, initials[0] || '•'),
    p.name);
}

export function personDot(personId, size = 8) {
  const p = personById(personId);
  return h('i', { style: { width: size + 'px', height: size + 'px', borderRadius: '50%', background: p?.color || 'var(--text-dim)', display: 'inline-block' } });
}

export function progress(pct, color) {
  const p = Math.max(0, Math.min(100, pct));
  return h('div', { class: 'bar' }, h('span', { style: { width: p + '%', background: color || 'var(--accent)' } }));
}

export function sectionTitle(icon, text, right) {
  return h('h2', { class: 'sec between' },
    h('span', { class: 'flex gap-8' }, h('span', {}, icon), text),
    right || null);
}

export function personOptions(includeAll = true) {
  const opts = [];
  if (includeAll) opts.push({ value: '', label: '— Anyone —' });
  return opts;
}
