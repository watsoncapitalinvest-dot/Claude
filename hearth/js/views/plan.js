// views/plan.js — tasks & shared calendar
import { h, todayISO, iso, parseISO, fmtDate, relDay, daysUntil, sortBy, groupBy, uid, MONTHS, DOW_LABELS, money } from '../utils.js';
import { state, update, catById, billNextDue } from '../store.js';
import { subTabs, pageHeader, registerFab } from '../nav.js';
import { formModal, field, input, select, segmented, textarea, closeModal, confirmDialog, toast, modal } from '../ui.js';
import { whoPill, personDot, peopleOpts, emptyCard } from './parts.js';
import { navigate } from '../router.js';

// ============================================================
// TASKS
// ============================================================
let taskFilter = '';
export function renderTasks() {
  registerFab('/tasks', () => taskModal());
  const wrap = h('div');
  wrap.append(pageHeader('Tasks', 'Shared to-dos for the two of you',
    h('button', { class: 'btn primary hide-mobile', onClick: () => taskModal() }, '+ Task')));
  wrap.append(subTabs('plan'));

  // filter by person
  const filterBar = h('div', { class: 'flex gap-6 wrap', style: { marginBottom: '16px' } },
    chip('Everyone', taskFilter === '', () => { taskFilter = ''; navigate('/tasks'); }),
    ...state.profile.people.map(p => chip(p.name, taskFilter === p.id, () => { taskFilter = p.id; navigate('/tasks'); }, p.color)),
  );
  wrap.append(filterBar);

  let tasks = state.tasks.filter(t => !taskFilter || t.who === taskFilter);
  const open = tasks.filter(t => !t.done);
  const done = tasks.filter(t => t.done);

  if (!tasks.length) {
    wrap.append(emptyCard('✅', 'No tasks yet', 'Add chores, errands, and to-dos — assign them to either of you.', () => taskModal()));
    return wrap;
  }

  // buckets
  const overdue = sortBy(open.filter(t => t.due && daysUntil(t.due) < 0), t => t.due);
  const todayT = open.filter(t => t.due === todayISO());
  const upcoming = sortBy(open.filter(t => t.due && daysUntil(t.due) > 0), t => t.due);
  const someday = open.filter(t => !t.due);

  const addBucket = (label, list, cls) => {
    if (!list.length) return;
    wrap.append(h('h2', { class: 'sec' }, label, h('span', { class: 'chip', style: { marginLeft: '4px' } }, String(list.length))));
    const card = h('div', { class: 'card' });
    list.forEach(t => card.append(taskRow(t, cls)));
    wrap.append(card);
  };
  addBucket('⚠️ Overdue', overdue, 'over');
  addBucket('☀️ Today', todayT);
  addBucket('🗓️ Upcoming', upcoming);
  addBucket('💭 Someday', someday);

  if (done.length) {
    wrap.append(h('h2', { class: 'sec between' },
      h('span', {}, `✓ Done (${done.length})`),
      h('button', { class: 'btn ghost sm', onClick: () => confirmDialog({ title: 'Clear completed?', message: `Remove ${done.length} finished tasks?`, confirm: 'Clear', onConfirm: () => { update(s => s.tasks = s.tasks.filter(t => !t.done || (taskFilter && t.who !== taskFilter))); toast('Cleared'); } }) }, 'Clear')));
    const card = h('div', { class: 'card' });
    sortBy(done, t => t.due || '', -1).slice(0, 20).forEach(t => card.append(taskRow(t)));
    wrap.append(card);
  }
  return wrap;
}

function taskRow(t, cls) {
  const overdue = cls === 'over';
  return h('div', { class: 'row' },
    h('div', { class: 'check' + (t.done ? ' on' : ''), onClick: () => update(s => { const x = s.tasks.find(y => y.id === t.id); x.done = !x.done; }) }, t.done ? '✓' : ''),
    h('div', { class: 'grow pointer', onClick: () => taskModal(t) },
      h('div', { class: 't' + (t.done ? ' done-text' : '') }, priorityDot(t.priority), t.title),
      t.due ? h('div', { class: 's', style: overdue ? { color: 'var(--red)', fontWeight: 600 } : {} }, relDay(t.due)) : null),
    t.who ? whoPill(t.who) : null,
  );
}
function priorityDot(p) {
  if (p === 'high') return h('span', { style: { color: 'var(--red)', marginRight: '5px' } }, '●');
  if (p === 'low') return h('span', { style: { color: 'var(--text-dim)', marginRight: '5px' } }, '○');
  return '';
}

function taskModal(task = null) {
  const editing = !!task;
  let priority = task?.priority || 'normal';
  formModal({
    title: editing ? 'Edit task' : 'New task',
    submitLabel: editing ? 'Save' : 'Add task',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.tasks = s.tasks.filter(x => x.id !== task.id)); closeModal(); toast('Deleted'); } }, 'Delete') : null,
    build(refs) {
      refs.title = input({ placeholder: 'What needs doing?', value: task?.title || '' });
      refs.due = input({ type: 'date', value: task?.due || '' });
      refs.who = select(peopleOpts(), task?.who || '');
      refs.prio = segmented([{ value: 'low', label: 'Low' }, { value: 'normal', label: 'Normal' }, { value: 'high', label: 'High' }], priority, v => priority = v);
      refs.notes = textarea({ placeholder: 'Notes (optional)', value: task?.notes || '', rows: 2 });
      return [
        field('Task', refs.title),
        h('div', { class: 'row-2' }, field('Due date', refs.due), field('Who', refs.who)),
        field('Priority', refs.prio),
        field('Notes', refs.notes),
      ];
    },
    onSubmit(refs) {
      const title = refs.title.value.trim();
      if (!title) throw new Error('Enter a task');
      const data = { title, due: refs.due.value || '', who: refs.who.value || '', priority, notes: refs.notes.value.trim() };
      update(s => { if (editing) Object.assign(s.tasks.find(x => x.id === task.id), data); else s.tasks.unshift({ id: uid('t'), done: false, ...data }); });
      closeModal(); toast(editing ? 'Saved' : 'Added');
    },
  });
}

// ============================================================
// CALENDAR
// ============================================================
let calCursor = { y: new Date().getFullYear(), m: new Date().getMonth() };
export function renderCalendar() {
  registerFab('/calendar', () => eventModal(null, todayISO()));
  const wrap = h('div');
  wrap.append(pageHeader('Calendar', 'Everything on one shared calendar',
    h('button', { class: 'btn primary hide-mobile', onClick: () => eventModal(null, todayISO()) }, '+ Event')));
  wrap.append(subTabs('plan'));

  // month header
  wrap.append(h('div', { class: 'flex between', style: { marginBottom: '14px' } },
    h('div', { style: { fontSize: '19px', fontWeight: '750' } }, `${MONTHS[calCursor.m]} ${calCursor.y}`),
    h('div', { class: 'flex gap-6' },
      h('button', { class: 'btn sm', onClick: () => { calCursor = { y: new Date().getFullYear(), m: new Date().getMonth() }; navigate('/calendar'); } }, 'Today'),
      h('button', { class: 'icon-btn', onClick: () => { shiftMonth(-1); navigate('/calendar'); } }, '‹'),
      h('button', { class: 'icon-btn', onClick: () => { shiftMonth(1); navigate('/calendar'); } }, '›'),
    )));

  // build event map for the month (events + task dues + bills)
  const items = calendarItems(calCursor.y, calCursor.m);

  // grid
  const grid = h('div', { class: 'card pad' });
  const dows = h('div', { class: 'cal-grid' });
  DOW_LABELS.forEach(d => dows.append(h('div', { class: 'cal-dow' }, d)));
  grid.append(dows);

  const cells = h('div', { class: 'cal-grid', style: { marginTop: '5px' } });
  const first = new Date(calCursor.y, calCursor.m, 1);
  const startDow = first.getDay();
  const daysInMonth = new Date(calCursor.y, calCursor.m + 1, 0).getDate();
  const prevDays = new Date(calCursor.y, calCursor.m, 0).getDate();
  const total = Math.ceil((startDow + daysInMonth) / 7) * 7;
  for (let i = 0; i < total; i++) {
    const dayNum = i - startDow + 1;
    const inMonth = dayNum >= 1 && dayNum <= daysInMonth;
    const dd = inMonth ? dayNum : dayNum < 1 ? prevDays + dayNum : dayNum - daysInMonth;
    const cellDate = inMonth ? iso(new Date(calCursor.y, calCursor.m, dayNum)) : null;
    const dayItems = cellDate ? (items[cellDate] || []) : [];
    const isToday = cellDate === todayISO();
    const cell = h('div', { class: 'cal-cell' + (inMonth ? '' : ' out') + (isToday ? ' today' : ''), onClick: inMonth ? () => dayModal(cellDate) : null },
      h('div', { class: 'dnum' }, String(dd)),
      dayItems.length ? h('div', { class: 'cal-dots' }, ...dayItems.slice(0, 4).map(it => h('i', { style: { background: it.color } }))) : null,
    );
    cells.append(cell);
  }
  grid.append(cells);
  wrap.append(grid);

  // upcoming list
  wrap.append(h('h2', { class: 'sec' }, '🗓️ Coming up'));
  const upcoming = upcomingItems(21);
  if (!upcoming.length) wrap.append(emptyCard('🌿', 'Nothing scheduled', 'Tap a day or add an event.', () => eventModal(null, todayISO())));
  else {
    const card = h('div', { class: 'card' });
    upcoming.forEach(it => card.append(h('div', { class: 'row' + (it.kind === 'event' ? ' pointer' : '') },
      h('div', { class: 'lead', style: { background: it.color + '22', color: it.color } }, it.icon),
      h('div', { class: 'grow', onClick: it.kind === 'event' ? () => eventModal(it.ref, it.date) : null },
        h('div', { class: 't' }, it.title),
        h('div', { class: 's' }, relDay(it.date) + (it.time ? ' · ' + fmtTime(it.time) : ''))),
      it.who ? whoPill(it.who) : (it.amount != null ? h('div', { class: 'amt' }, money(it.amount)) : null),
    )));
    wrap.append(card);
  }
  return wrap;
}

function shiftMonth(n) {
  let m = calCursor.m + n, y = calCursor.y;
  if (m < 0) { m = 11; y--; } if (m > 11) { m = 0; y++; }
  calCursor = { y, m };
}
function fmtTime(t) {
  if (!t) return '';
  const [h24, min] = t.split(':').map(Number);
  const ap = h24 >= 12 ? 'pm' : 'am'; const h12 = h24 % 12 || 12;
  return `${h12}:${String(min).padStart(2, '0')}${ap}`;
}

function calendarItems(y, m) {
  const map = {};
  const push = (date, obj) => { (map[date] ||= []).push(obj); };
  // events
  for (const e of state.events) push(e.date, { color: personColor(e.who) || 'var(--accent)' });
  // task due dates
  for (const t of state.tasks) if (t.due && !t.done) push(t.due, { color: 'var(--gold)' });
  // bills (next occurrence)
  for (const b of state.bills) push(billNextDue(b), { color: 'var(--red)' });
  return map;
}
function personColor(id) { return state.profile.people.find(p => p.id === id)?.color; }

function upcomingItems(days) {
  const out = [];
  for (const e of state.events) if (daysUntil(e.date) >= 0 && daysUntil(e.date) <= days) out.push({ kind: 'event', title: e.title, date: e.date, time: e.time, who: e.who, icon: '📌', color: personColor(e.who) || '#c8632b', ref: e });
  for (const t of state.tasks) if (!t.done && t.due && daysUntil(t.due) >= 0 && daysUntil(t.due) <= days) out.push({ kind: 'task', title: t.title, date: t.due, who: t.who, icon: '✅', color: '#c79a2e' });
  for (const b of state.bills) { const d = billNextDue(b); if (daysUntil(d) <= days) out.push({ kind: 'bill', title: b.name, date: d, icon: catById(b.category).icon, color: '#c0433a', amount: b.amount }); }
  return sortBy(out, x => x.date + (x.time || '')).slice(0, 30);
}

function dayModal(date) {
  const events = sortBy(state.events.filter(e => e.date === date), e => e.time || '');
  const tasks = state.tasks.filter(t => t.due === date && !t.done);
  const bills = state.bills.filter(b => billNextDue(b) === date);
  const body = h('div');
  const list = h('div', { class: 'card', style: { marginBottom: '14px' } });
  let any = false;
  events.forEach(e => { any = true; list.append(h('div', { class: 'row pointer', onClick: () => eventModal(e, date) },
    h('div', { class: 'lead' }, '📌'), h('div', { class: 'grow' }, h('div', { class: 't' }, e.title), h('div', { class: 's' }, e.time ? fmtTime(e.time) : 'All day')), e.who ? whoPill(e.who) : null)); });
  tasks.forEach(t => { any = true; list.append(h('div', { class: 'row' }, h('div', { class: 'lead' }, '✅'), h('div', { class: 'grow t' }, t.title), t.who ? whoPill(t.who) : null)); });
  bills.forEach(b => { any = true; list.append(h('div', { class: 'row' }, h('div', { class: 'lead' }, catById(b.category).icon), h('div', { class: 'grow t' }, b.name + ' due'), h('div', { class: 'amt' }, money(b.amount)))); });
  if (!any) list.append(h('div', { class: 'list-empty', style: { padding: '20px' } }, 'Nothing scheduled'));
  body.append(list);
  modal({
    title: fmtDate(date, { withYear: true, weekday: true }),
    body,
    footer: [h('button', { class: 'btn ghost', onClick: closeModal }, 'Close'), h('button', { class: 'btn primary', onClick: () => eventModal(null, date) }, '+ Add event')],
  });
}

function eventModal(ev = null, date = todayISO()) {
  const editing = !!ev;
  formModal({
    title: editing ? 'Edit event' : 'New event',
    submitLabel: editing ? 'Save' : 'Add',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.events = s.events.filter(x => x.id !== ev.id)); closeModal(); toast('Deleted'); } }, 'Delete') : null,
    build(refs) {
      refs.title = input({ placeholder: 'e.g. Dinner with friends', value: ev?.title || '' });
      refs.date = input({ type: 'date', value: ev?.date || date });
      refs.time = input({ type: 'time', value: ev?.time || '' });
      refs.who = select(peopleOpts(), ev?.who || '');
      refs.notes = textarea({ placeholder: 'Notes (optional)', value: ev?.notes || '', rows: 2 });
      return [
        field('Title', refs.title),
        h('div', { class: 'row-2' }, field('Date', refs.date), field('Time', refs.time)),
        field('Who', refs.who),
        field('Notes', refs.notes),
      ];
    },
    onSubmit(refs) {
      const title = refs.title.value.trim();
      if (!title) throw new Error('Enter a title');
      const data = { title, date: refs.date.value, time: refs.time.value, who: refs.who.value || '', notes: refs.notes.value.trim() };
      update(s => { if (editing) Object.assign(s.events.find(x => x.id === ev.id), data); else s.events.push({ id: uid('e'), ...data }); });
      closeModal(); toast(editing ? 'Saved' : 'Added');
    },
  });
}

// shared bits
function chip(label, on, onClick, color) {
  return h('button', { class: 'chip pointer', style: on ? { background: 'var(--accent-soft)', color: 'var(--accent-ink)' } : {}, onClick },
    color ? h('i', { style: { width: '8px', height: '8px', borderRadius: '50%', background: color, display: 'inline-block' } }) : null, label);
}
