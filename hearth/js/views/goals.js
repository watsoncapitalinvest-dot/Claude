// views/goals.js — shared savings goals & notes
import { h, money, moneyShort, fmtDate, relDay, daysUntil, sortBy, uid, todayISO, esc } from '../utils.js';
import { state, update } from '../store.js';
import { subTabs, pageHeader, registerFab } from '../nav.js';
import { formModal, field, input, textarea, closeModal, confirmDialog, toast, modal } from '../ui.js';
import { progress } from './parts.js';
import { navigate } from '../router.js';

// ============================================================
// GOALS
// ============================================================
export function renderGoals() {
  registerFab('/goals', () => goalModal());
  const wrap = h('div');
  wrap.append(pageHeader('Goals', 'Save toward what matters — together',
    h('button', { class: 'btn primary hide-mobile', onClick: () => goalModal() }, '+ Goal')));
  wrap.append(subTabs('goals'));

  if (!state.goals.length) {
    wrap.append(emptyCard('✨', 'Set a shared goal', 'Vacation, a new couch, an emergency fund — track progress together.', () => goalModal()));
    return wrap;
  }

  const totalSaved = state.goals.reduce((a, g) => a + (g.saved || 0), 0);
  const totalTarget = state.goals.reduce((a, g) => a + (g.target || 0), 0);
  wrap.append(h('div', { class: 'card pad', style: { marginBottom: '18px' } },
    h('div', { class: 'flex between', style: { marginBottom: '10px' } },
      h('div', { class: 't' }, 'All goals'),
      h('div', { class: 'amt' }, `${money(totalSaved, { cents: false })} / ${money(totalTarget, { cents: false })}`)),
    progress(totalTarget ? (totalSaved / totalTarget) * 100 : 0, 'var(--green)')));

  const grid = h('div', { class: 'grid auto' });
  for (const g of state.goals) {
    const pct = g.target ? (g.saved / g.target) * 100 : 0;
    const remaining = Math.max(0, (g.target || 0) - (g.saved || 0));
    grid.append(h('div', { class: 'card pad', style: { display: 'flex', flexDirection: 'column', gap: '10px' } },
      h('div', { class: 'flex between' },
        h('div', { style: { fontWeight: 700, fontSize: '16px' } }, g.name),
        h('button', { class: 'icon-btn', onClick: () => goalModal(g) }, '✎')),
      g.targetDate ? h('div', { class: 's dim' }, '🎯 by ' + fmtDate(g.targetDate, { withYear: true })) : null,
      g.note ? h('div', { class: 's' }, g.note) : null,
      h('div', { style: { marginTop: 'auto' } },
        h('div', { class: 'flex between', style: { marginBottom: '6px' } },
          h('span', { style: { fontWeight: 750, fontSize: '19px' } }, money(g.saved || 0, { cents: false })),
          h('span', { class: 's dim' }, `of ${money(g.target || 0, { cents: false })}`)),
        progress(pct, g.color),
        h('div', { class: 'hint', style: { margin: '6px 0 0' } }, pct >= 100 ? '🎉 Goal reached!' : `${money(remaining, { cents: false })} to go`)),
      h('div', { class: 'flex gap-8', style: { marginTop: '4px' } },
        h('button', { class: 'btn sm block', onClick: () => contributeModal(g) }, '+ Add money')),
    ));
  }
  wrap.append(grid);
  return wrap;
}

function goalModal(goal = null) {
  const editing = !!goal;
  const colors = ['#c8632b', '#3f8a5c', '#3f6fa8', '#7a5aa6', '#c79a2e', '#2f8fb0', '#c0433a'];
  let color = goal?.color || colors[0];
  formModal({
    title: editing ? 'Edit goal' : 'New goal',
    submitLabel: editing ? 'Save' : 'Create',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.goals = s.goals.filter(x => x.id !== goal.id)); closeModal(); toast('Deleted'); } }, 'Delete') : null,
    build(refs) {
      refs.name = input({ placeholder: 'e.g. Summer vacation', value: goal?.name || '' });
      refs.target = input({ type: 'number', step: '1', inputmode: 'decimal', placeholder: '0', value: goal?.target || '' });
      refs.saved = input({ type: 'number', step: '1', inputmode: 'decimal', placeholder: '0', value: goal?.saved || '' });
      refs.date = input({ type: 'date', value: goal?.targetDate || '' });
      refs.note = input({ placeholder: 'Note (optional)', value: goal?.note || '' });
      const swatches = h('div', { class: 'flex gap-8' }, ...colors.map(c => {
        const b = h('button', { type: 'button', style: { width: '30px', height: '30px', borderRadius: '9px', background: c, border: c === color ? '3px solid var(--text)' : '2px solid var(--border)' } });
        b.addEventListener('click', () => { color = c; swatches.querySelectorAll('button').forEach((x, i) => x.style.border = colors[i] === c ? '3px solid var(--text)' : '2px solid var(--border)'); });
        return b;
      }));
      return [
        field('Goal name', refs.name),
        h('div', { class: 'row-2' }, field('Target amount', refs.target), field('Saved so far', refs.saved)),
        field('Target date (optional)', refs.date),
        field('Note', refs.note),
        field('Color', swatches),
      ];
    },
    onSubmit(refs) {
      const name = refs.name.value.trim(); if (!name) throw new Error('Name the goal');
      const data = { name, target: parseFloat(refs.target.value) || 0, saved: parseFloat(refs.saved.value) || 0, targetDate: refs.date.value, note: refs.note.value.trim(), color };
      update(s => { if (editing) Object.assign(s.goals.find(x => x.id === goal.id), data); else s.goals.push({ id: uid('g'), ...data }); });
      closeModal(); toast(editing ? 'Saved' : 'Goal created');
    },
  });
}
function contributeModal(goal) {
  formModal({
    title: `Add to ${goal.name}`,
    submitLabel: 'Add money',
    build(refs) {
      refs.amt = input({ type: 'number', step: '1', inputmode: 'decimal', placeholder: '0.00', style: { fontSize: '22px', fontWeight: '700' } });
      return [
        h('p', { class: 'hint', style: { marginTop: 0 } }, `Saved ${money(goal.saved || 0)} of ${money(goal.target || 0)}.`),
        field('Amount to add', refs.amt),
      ];
    },
    onSubmit(refs) {
      const amt = parseFloat(refs.amt.value); if (!amt) throw new Error('Enter an amount');
      update(s => { const g = s.goals.find(x => x.id === goal.id); g.saved = (g.saved || 0) + amt; });
      closeModal(); toast('Added ' + money(amt));
    },
  });
}

// ============================================================
// NOTES
// ============================================================
export function renderNotes() {
  registerFab('/notes', () => noteModal());
  const wrap = h('div');
  wrap.append(pageHeader('Notes', 'A shared space for anything',
    h('button', { class: 'btn primary hide-mobile', onClick: () => noteModal() }, '+ Note')));
  wrap.append(subTabs('goals'));

  if (!state.notes.length) {
    wrap.append(emptyCard('📝', 'No notes yet', 'Wifi passwords, gift ideas, reminders, lists — keep them here.', () => noteModal()));
    return wrap;
  }
  const notes = sortBy(state.notes, n => (n.pinned ? '0' : '1') + String(9e15 - (n.updated || 0)));
  const grid = h('div', { class: 'grid auto' });
  for (const n of notes) {
    grid.append(h('div', { class: 'card pad pointer', style: { display: 'flex', flexDirection: 'column', gap: '6px', minHeight: '120px' }, onClick: () => noteModal(n) },
      h('div', { class: 'flex between' },
        h('div', { style: { fontWeight: 700, fontSize: '15.5px' } }, n.pinned ? '📌 ' : '', n.title || 'Untitled'),
      ),
      h('div', { class: 's', style: { whiteSpace: 'pre-wrap', color: 'var(--text-soft)', flex: '1', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: '6', WebkitBoxOrient: 'vertical' } }, n.body || ''),
      h('div', { class: 'dim', style: { fontSize: '11px' } }, n.updated ? 'Updated ' + fmtDate(new Date(n.updated), { withYear: true }) : ''),
    ));
  }
  wrap.append(grid);
  return wrap;
}
function noteModal(note = null) {
  const editing = !!note;
  let pinned = note?.pinned || false;
  formModal({
    title: editing ? 'Edit note' : 'New note',
    submitLabel: 'Save',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.notes = s.notes.filter(x => x.id !== note.id)); closeModal(); toast('Deleted'); } }, 'Delete') : null,
    build(refs) {
      refs.title = input({ placeholder: 'Title', value: note?.title || '' });
      refs.body = textarea({ placeholder: 'Write anything…', value: note?.body || '', rows: 8, style: { minHeight: '160px' } });
      const pinBtn = h('button', { type: 'button', class: 'btn sm' + (pinned ? ' primary' : ''), onClick: () => { pinned = !pinned; pinBtn.className = 'btn sm' + (pinned ? ' primary' : ''); pinBtn.textContent = pinned ? '📌 Pinned' : '📌 Pin'; } }, pinned ? '📌 Pinned' : '📌 Pin');
      return [field('Title', refs.title), field('Note', refs.body), pinBtn];
    },
    onSubmit(refs) {
      const title = refs.title.value.trim(); const body = refs.body.value.trim();
      if (!title && !body) throw new Error('Write something first');
      update(s => { if (editing) Object.assign(s.notes.find(x => x.id === note.id), { title, body, pinned, updated: Date.now() }); else s.notes.unshift({ id: uid('n'), title, body, pinned, updated: Date.now() }); });
      closeModal(); toast('Saved');
    },
  });
}

function emptyCard(icon, title, sub, onAdd) {
  return h('div', { class: 'card' }, h('div', { class: 'list-empty' },
    h('span', { class: 'em' }, icon),
    h('div', { style: { fontWeight: 650 } }, title),
    h('div', { style: { fontSize: '13px', marginTop: '4px' } }, sub),
    onAdd ? h('button', { class: 'btn primary', style: { marginTop: '14px' }, onClick: onAdd }, '+ Add') : null));
}
