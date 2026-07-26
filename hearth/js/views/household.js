// views/household.js — shopping lists, meal plan, home inventory
import { h, iso, todayISO, fmtDate, sortBy, uid, DOW_LABELS, sum } from '../utils.js';
import { state, update } from '../store.js';
import { subTabs, pageHeader, registerFab } from '../nav.js';
import { formModal, field, input, textarea, closeModal, confirmDialog, toast, modal } from '../ui.js';
import { emptyCard } from './parts.js';
import { navigate } from '../router.js';

// ============================================================
// SHOPPING LISTS
// ============================================================
let activeList = null;
export function renderShopping() {
  registerFab('/shopping', () => activeList ? quickAddItem() : newListModal());
  const wrap = h('div');
  if (!state.lists.length) {
    wrap.append(pageHeader('Shopping', 'Shared lists you both can edit'));
    wrap.append(subTabs('household'));
    wrap.append(emptyCard('🛒', 'No lists yet', 'Make a grocery list, hardware list, anything.', () => newListModal()));
    return wrap;
  }
  if (!activeList || !state.lists.find(l => l.id === activeList)) activeList = state.lists[0].id;
  const list = state.lists.find(l => l.id === activeList);

  wrap.append(pageHeader('Shopping', `${state.lists.length} list${state.lists.length > 1 ? 's' : ''}`,
    h('button', { class: 'btn hide-mobile', onClick: () => newListModal() }, '+ New list')));
  wrap.append(subTabs('household'));

  // list tabs
  const tabs = h('div', { class: 'flex gap-6 wrap', style: { marginBottom: '16px' } });
  state.lists.forEach(l => {
    const cnt = l.items.filter(i => !i.done).length;
    tabs.append(h('button', { class: 'chip pointer', style: l.id === activeList ? { background: 'var(--accent)', color: '#fff' } : {}, onClick: () => { activeList = l.id; navigate('/shopping'); } },
      l.name, cnt ? h('span', { class: 'badge', style: { background: 'rgba(255,255,255,.25)', color: 'inherit' } }, String(cnt)) : null));
  });
  tabs.append(h('button', { class: 'chip pointer', onClick: () => newListModal() }, '+'));
  wrap.append(tabs);

  // add item input (inline)
  const addInput = h('input', { class: 'input', placeholder: `Add to ${list.name}…`, style: { flex: '1' } });
  const addForm = h('form', { class: 'flex gap-8', style: { marginBottom: '16px' }, onSubmit: (e) => {
    e.preventDefault(); const v = addInput.value.trim(); if (!v) return;
    update(s => s.lists.find(l => l.id === activeList).items.unshift({ id: uid('i'), text: v, done: false }));
    addInput.value = ''; setTimeout(() => document.querySelector('.content input')?.focus(), 30);
  } }, addInput, h('button', { class: 'btn primary', type: 'submit' }, 'Add'));
  wrap.append(addForm);

  const todo = list.items.filter(i => !i.done);
  const done = list.items.filter(i => i.done);

  const card = h('div', { class: 'card' });
  if (!todo.length && !done.length) card.append(h('div', { class: 'list-empty', style: { padding: '26px' } }, 'List is empty — add something above'));
  todo.forEach(it => card.append(itemRow(list.id, it)));
  if (done.length) {
    card.append(h('div', { class: 'row', style: { background: 'var(--surface-2)' } },
      h('div', { class: 's grow', style: { fontWeight: 600 } }, `✓ In cart (${done.length})`),
      h('button', { class: 'btn ghost sm', onClick: () => update(s => { const l = s.lists.find(x => x.id === list.id); l.items = l.items.filter(i => !i.done); }) }, 'Clear')));
    done.forEach(it => card.append(itemRow(list.id, it)));
  }
  wrap.append(card);

  // list actions
  wrap.append(h('div', { class: 'flex gap-8', style: { marginTop: '14px' } },
    h('button', { class: 'btn sm', onClick: () => renameList(list) }, '✎ Rename'),
    state.lists.length > 1 ? h('button', { class: 'btn sm danger', onClick: () => confirmDialog({ title: 'Delete list?', message: `Delete "${list.name}" and its items?`, confirm: 'Delete', onConfirm: () => { update(s => s.lists = s.lists.filter(l => l.id !== list.id)); activeList = null; toast('List deleted'); } }) }, '🗑 Delete list') : null,
  ));
  return wrap;
}

function itemRow(listId, it) {
  return h('div', { class: 'row' },
    h('div', { class: 'check' + (it.done ? ' on' : ''), onClick: () => update(s => { const x = s.lists.find(l => l.id === listId).items.find(i => i.id === it.id); x.done = !x.done; }) }, it.done ? '✓' : ''),
    h('div', { class: 'grow t' + (it.done ? ' done-text' : ''), contentEditable: 'false', onClick: () => editItem(listId, it) }, it.text),
    h('button', { class: 'icon-btn', onClick: () => update(s => { const l = s.lists.find(x => x.id === listId); l.items = l.items.filter(i => i.id !== it.id); }) }, '✕'),
  );
}
function editItem(listId, it) {
  formModal({ title: 'Edit item', submitLabel: 'Save', build(refs) { refs.text = input({ value: it.text }); return [field('Item', refs.text)]; },
    onSubmit(refs) { const v = refs.text.value.trim(); if (!v) throw new Error('Enter text'); update(s => s.lists.find(l => l.id === listId).items.find(i => i.id === it.id).text = v); closeModal(); } });
}
function quickAddItem() {
  const list = state.lists.find(l => l.id === activeList) || state.lists[0];
  if (!list) return newListModal();
  formModal({ title: `Add to ${list.name}`, submitLabel: 'Add', build(refs) { refs.text = input({ placeholder: 'Item' }); return [field('Item', refs.text)]; },
    onSubmit(refs) { const v = refs.text.value.trim(); if (!v) throw new Error('Enter an item'); update(s => s.lists.find(l => l.id === list.id).items.unshift({ id: uid('i'), text: v, done: false })); closeModal(); toast('Added'); } });
}
function newListModal() {
  formModal({ title: 'New list', submitLabel: 'Create', build(refs) { refs.name = input({ placeholder: 'e.g. Groceries, Hardware store' }); return [field('List name', refs.name)]; },
    onSubmit(refs) { const v = refs.name.value.trim(); if (!v) throw new Error('Name the list'); const id = uid('l'); update(s => s.lists.push({ id, name: v, items: [] })); activeList = id; closeModal(); toast('List created'); } });
}
function renameList(list) {
  formModal({ title: 'Rename list', submitLabel: 'Save', build(refs) { refs.name = input({ value: list.name }); return [field('List name', refs.name)]; },
    onSubmit(refs) { const v = refs.name.value.trim(); if (!v) throw new Error('Name required'); update(s => s.lists.find(l => l.id === list.id).name = v); closeModal(); } });
}

// ============================================================
// MEAL PLAN — week view
// ============================================================
let weekStart = startOfWeek(new Date());
function startOfWeek(d) { const x = new Date(d); x.setDate(x.getDate() - x.getDay()); x.setHours(0,0,0,0); return x; }

export function renderMeals() {
  registerFab('/meals', () => mealModal(todayISO()));
  const wrap = h('div');
  wrap.append(pageHeader('Meal Plan', "What's for dinner this week"));
  wrap.append(subTabs('household'));

  wrap.append(h('div', { class: 'flex between', style: { marginBottom: '14px' } },
    h('div', { style: { fontWeight: 700 } }, weekLabel()),
    h('div', { class: 'flex gap-6' },
      h('button', { class: 'btn sm', onClick: () => { weekStart = startOfWeek(new Date()); navigate('/meals'); } }, 'This week'),
      h('button', { class: 'icon-btn', onClick: () => { weekStart = new Date(weekStart.getTime() - 7 * 86400000); navigate('/meals'); } }, '‹'),
      h('button', { class: 'icon-btn', onClick: () => { weekStart = new Date(weekStart.getTime() + 7 * 86400000); navigate('/meals'); } }, '›'),
    )));

  const card = h('div', { class: 'card' });
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart.getTime() + i * 86400000);
    const key = iso(d);
    const meal = state.meals[key] || {};
    const isToday = key === todayISO();
    card.append(h('div', { class: 'row pointer', style: isToday ? { background: 'var(--accent-soft)' } : {}, onClick: () => mealModal(key) },
      h('div', { class: 'lead', style: { flexDirection: 'column', fontSize: '11px', lineHeight: '1.1', fontWeight: '700', gap: '1px', background: 'var(--surface-2)' } },
        h('span', { style: { color: 'var(--text-dim)' } }, DOW_LABELS[d.getDay()]), h('span', { style: { fontSize: '15px' } }, String(d.getDate()))),
      h('div', { class: 'grow' },
        meal.dinner ? h('div', { class: 't' }, meal.dinner) : h('div', { class: 's dim' }, 'Tap to plan dinner'),
        (meal.lunch || meal.breakfast) ? h('div', { class: 's' }, [meal.breakfast && '🌅 ' + meal.breakfast, meal.lunch && '☀️ ' + meal.lunch].filter(Boolean).join('   ')) : null),
    ));
  }
  wrap.append(card);

  // quick action: add this week's dinners to a grocery list
  wrap.append(h('p', { class: 'hint', style: { marginTop: '14px' } }, 'Tip: plan dinners here, then jot ingredients into a Shopping list.'));
  return wrap;
}
function weekLabel() {
  const end = new Date(weekStart.getTime() + 6 * 86400000);
  return `${fmtDate(weekStart)} – ${fmtDate(end, { withYear: end.getFullYear() !== new Date().getFullYear() })}`;
}
function mealModal(key) {
  const meal = state.meals[key] || {};
  formModal({
    title: fmtDate(key, { weekday: true, withYear: false }),
    submitLabel: 'Save',
    extraFoot: (meal.breakfast || meal.lunch || meal.dinner) ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => delete s.meals[key]); closeModal(); toast('Cleared'); } }, 'Clear') : null,
    build(refs) {
      refs.b = input({ placeholder: 'Breakfast (optional)', value: meal.breakfast || '' });
      refs.l = input({ placeholder: 'Lunch (optional)', value: meal.lunch || '' });
      refs.d = input({ placeholder: 'Dinner', value: meal.dinner || '' });
      return [field('🌅 Breakfast', refs.b), field('☀️ Lunch', refs.l), field('🌙 Dinner', refs.d)];
    },
    onSubmit(refs) {
      const m = { breakfast: refs.b.value.trim(), lunch: refs.l.value.trim(), dinner: refs.d.value.trim() };
      update(s => { if (m.breakfast || m.lunch || m.dinner) s.meals[key] = m; else delete s.meals[key]; });
      closeModal(); toast('Saved');
    },
  });
}

// ============================================================
// HOME INVENTORY
// ============================================================
export function renderInventory() {
  registerFab('/inventory', () => invModal());
  const wrap = h('div');
  wrap.append(pageHeader('Home Inventory', 'Track supplies & household info',
    h('button', { class: 'btn primary hide-mobile', onClick: () => invModal() }, '+ Item')));
  wrap.append(subTabs('household'));

  if (!state.inventory.length) {
    wrap.append(emptyCard('📦', 'Nothing tracked yet', 'Keep tabs on supplies you restock — filters, batteries, pantry staples.', () => invModal()));
    return wrap;
  }
  const byLoc = {};
  for (const it of state.inventory) (byLoc[it.location || 'Other'] ||= []).push(it);
  for (const loc of Object.keys(byLoc).sort()) {
    wrap.append(h('h2', { class: 'sec' }, '📍 ' + loc));
    const card = h('div', { class: 'card' });
    sortBy(byLoc[loc], x => x.name.toLowerCase()).forEach(it => card.append(h('div', { class: 'row pointer', onClick: () => invModal(it) },
      h('div', { class: 'grow' }, h('div', { class: 't' }, it.name), it.note ? h('div', { class: 's' }, it.note) : null),
      h('div', { class: 'chip' }, '×' + (it.qty ?? 1)),
    )));
    wrap.append(card);
  }
  return wrap;
}
function invModal(it = null) {
  const editing = !!it;
  formModal({
    title: editing ? 'Edit item' : 'Add item',
    submitLabel: editing ? 'Save' : 'Add',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.inventory = s.inventory.filter(x => x.id !== it.id)); closeModal(); toast('Deleted'); } }, 'Delete') : null,
    build(refs) {
      refs.name = input({ placeholder: 'e.g. Furnace filter', value: it?.name || '' });
      refs.qty = input({ type: 'number', min: '0', value: it?.qty ?? 1 });
      refs.loc = input({ placeholder: 'e.g. Garage, Pantry', value: it?.location || '', list: 'inv-locs' });
      refs.note = input({ placeholder: 'Size, brand, notes (optional)', value: it?.note || '' });
      const dl = h('datalist', { id: 'inv-locs' }, ...[...new Set(state.inventory.map(x => x.location).filter(Boolean))].map(l => h('option', { value: l })));
      return [
        field('Item', refs.name),
        h('div', { class: 'row-2' }, field('Quantity', refs.qty), field('Location', refs.loc)),
        field('Notes', refs.note), dl,
      ];
    },
    onSubmit(refs) {
      const name = refs.name.value.trim(); if (!name) throw new Error('Name the item');
      const data = { name, qty: parseInt(refs.qty.value) || 0, location: refs.loc.value.trim(), note: refs.note.value.trim() };
      update(s => { if (editing) Object.assign(s.inventory.find(x => x.id === it.id), data); else s.inventory.push({ id: uid('v'), ...data }); });
      closeModal(); toast(editing ? 'Saved' : 'Added');
    },
  });
}

