// views/parts.js — small shared render helpers
import { h } from '../utils.js';
import { state, personById } from '../store.js';

// dropdown options for "who" selects (shared across views)
export const peopleOpts = () => [{ value: '', label: 'Anyone' }, ...state.profile.people.map(p => ({ value: p.id, label: p.name }))];

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

export function emptyCard(icon, title, sub, onAdd) {
  return h('div', { class: 'card' }, h('div', { class: 'list-empty' },
    h('span', { class: 'em' }, icon),
    h('div', { style: { fontWeight: 650 } }, title),
    h('div', { style: { fontSize: '13px', marginTop: '4px' } }, sub),
    onAdd ? h('button', { class: 'btn primary', style: { marginTop: '14px' }, onClick: onAdd }, '+ Add') : null));
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
