// ui.js — modal, toast, confirm, and small form helpers
import { h, esc } from './utils.js';

// ---------- toast ----------
export function toast(msg, ms = 2200) {
  const wrap = document.getElementById('toast-wrap');
  const el = h('div', { class: 'toast' }, msg);
  wrap.append(el);
  setTimeout(() => { el.style.transition = 'opacity .3s, transform .3s'; el.style.opacity = '0'; el.style.transform = 'translateY(8px)'; setTimeout(() => el.remove(), 300); }, ms);
}

// ---------- modal ----------
let closeCb = null;
export function modal({ title, body, footer, onClose, wide = false }) {
  closeModal();
  const root = document.getElementById('modal-root');
  const bodyEl = typeof body === 'string' ? h('div', { html: body }) : body;
  const scrim = h('div', { class: 'scrim' });
  const modalEl = h('div', { class: 'modal', style: wide ? { maxWidth: '640px' } : {} },
    h('div', { class: 'modal-head' },
      h('div', { class: 'modal-title' }, title || ''),
      h('button', { class: 'icon-btn', 'aria-label': 'Close', onClick: closeModal }, '✕'),
    ),
    h('div', { class: 'modal-body' }, bodyEl),
    footer ? h('div', { class: 'modal-foot' }, footer) : null,
  );
  scrim.append(modalEl);
  scrim.addEventListener('mousedown', (e) => { if (e.target === scrim) closeModal(); });
  root.append(scrim);
  closeCb = onClose;
  document.addEventListener('keydown', escClose);
  // focus first input
  setTimeout(() => modalEl.querySelector('input,textarea,select,button.primary')?.focus(), 40);
  return { close: closeModal, el: modalEl };
}
function escClose(e) { if (e.key === 'Escape') closeModal(); }
export function closeModal() {
  const root = document.getElementById('modal-root');
  if (root.firstChild) { root.innerHTML = ''; document.removeEventListener('keydown', escClose); const cb = closeCb; closeCb = null; cb?.(); }
}

export function confirmDialog({ title = 'Are you sure?', message = '', confirm = 'Confirm', danger = true, onConfirm }) {
  const foot = [
    h('button', { class: 'btn ghost', onClick: closeModal }, 'Cancel'),
    h('button', { class: `btn ${danger ? 'danger' : 'primary'}`, onClick: () => { closeModal(); onConfirm?.(); } }, confirm),
  ];
  modal({ title, body: h('p', { class: 'muted', style: { fontSize: '14.5px' } }, message), footer: foot });
}

// ---------- form helpers ----------
export function field(label, control, hint) {
  return h('div', { class: 'field' },
    label ? h('label', {}, label) : null,
    control,
    hint ? h('div', { class: 'hint' }, hint) : null,
  );
}
export function input(attrs = {}) { return h('input', { class: 'input', ...attrs }); }
export function textarea(attrs = {}) { return h('textarea', { class: 'input', ...attrs }); }
export function select(options, value, attrs = {}) {
  const el = h('select', { class: 'input', ...attrs });
  for (const o of options) {
    const opt = h('option', { value: o.value }, o.label);
    if (String(o.value) === String(value)) opt.selected = true;
    el.append(opt);
  }
  return el;
}
// segmented control returning an object with .value
export function segmented(options, value, onChange) {
  const wrap = h('div', { class: 'seg' });
  const state = { value };
  options.forEach(o => {
    const b = h('button', { type: 'button', class: String(o.value) === String(value) ? 'on' : '' }, o.label);
    b.addEventListener('click', () => {
      state.value = o.value;
      wrap.querySelectorAll('button').forEach(x => x.classList.remove('on'));
      b.classList.add('on');
      onChange?.(o.value);
    });
    wrap.append(b);
  });
  wrap.getValue = () => state.value;
  return wrap;
}

export function iconChoice(items, value, onChange) {
  const wrap = h('div', { class: 'seg', style: { flexWrap: 'wrap' } });
  const state = { value };
  items.forEach(it => {
    const b = h('button', { type: 'button', class: String(it.value) === String(value) ? 'on' : '' },
      it.icon ? it.icon + ' ' : '', it.label);
    b.addEventListener('click', () => {
      state.value = it.value;
      wrap.querySelectorAll('button').forEach(x => x.classList.remove('on'));
      b.classList.add('on');
      onChange?.(it.value);
    });
    wrap.append(b);
  });
  wrap.getValue = () => state.value;
  return wrap;
}

// build a standard modal form; fields is a fn(refs) -> nodes; onSubmit(refs)
export function formModal({ title, build, submitLabel = 'Save', onSubmit, extraFoot }) {
  const refs = {};
  const bodyNodes = build(refs);
  const submit = () => { try { onSubmit(refs); } catch (e) { toast(e.message || 'Something went wrong'); } };
  const form = h('form', { onSubmit: (e) => { e.preventDefault(); submit(); } }, ...[].concat(bodyNodes));
  // hidden submit to allow Enter
  form.append(h('button', { type: 'submit', style: { display: 'none' } }));
  const foot = [
    extraFoot || h('button', { type: 'button', class: 'btn ghost', onClick: closeModal }, 'Cancel'),
    h('button', { type: 'button', class: 'btn primary', onClick: submit }, submitLabel),
  ];
  return modal({ title, body: form, footer: foot });
}

// empty state
export function empty(icon, title, sub) {
  return h('div', { class: 'list-empty' },
    h('span', { class: 'em' }, icon),
    h('div', { style: { fontWeight: 650, color: 'var(--text-soft)' } }, title),
    sub ? h('div', { style: { fontSize: '13px', marginTop: '4px' } }, sub) : null,
  );
}
