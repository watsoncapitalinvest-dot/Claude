// nav.js — navigation config + shared layout parts
import { h } from './utils.js';
import { navigate, currentPath } from './router.js';

// Top-level sections (bottom nav + sidebar groups)
export const SECTIONS = [
  { key: 'home',      label: 'Home',      icon: '🏠', route: '/dashboard' },
  { key: 'money',     label: 'Money',     icon: '💰', route: '/money' },
  { key: 'plan',      label: 'Plan',      icon: '🗓️', route: '/tasks' },
  { key: 'household', label: 'Household', icon: '🧺', route: '/shopping' },
  { key: 'goals',     label: 'Goals',     icon: '✨', route: '/goals' },
];

// Sub-tabs per section
export const TABS = {
  money:     [ { r: '/money', l: 'Overview' }, { r: '/spending', l: 'Spending' }, { r: '/budgets', l: 'Budgets' }, { r: '/bills', l: 'Bills' } ],
  plan:      [ { r: '/tasks', l: 'Tasks' }, { r: '/calendar', l: 'Calendar' } ],
  household: [ { r: '/shopping', l: 'Shopping' }, { r: '/meals', l: 'Meals' }, { r: '/inventory', l: 'Inventory' } ],
  goals:     [ { r: '/goals', l: 'Goals' }, { r: '/notes', l: 'Notes' } ],
};

// which section a route belongs to
export function sectionOf(path) {
  const p = '/' + path.split('/')[1];
  if (p === '/dashboard') return 'home';
  if (['/money','/spending','/budgets','/bills'].includes(p)) return 'money';
  if (['/tasks','/calendar'].includes(p)) return 'plan';
  if (['/shopping','/meals','/inventory'].includes(p)) return 'household';
  if (['/goals','/notes'].includes(p)) return 'goals';
  if (p === '/settings') return 'settings';
  return 'home';
}

// sub-tab bar for a section
export function subTabs(sectionKey) {
  const tabs = TABS[sectionKey];
  if (!tabs) return null;
  const cur = currentPath();
  const bar = h('div', { class: 'tabs', style: { marginBottom: '18px' } });
  for (const t of tabs) {
    const on = cur === t.r || ('/' + cur.split('/')[1]) === t.r;
    const b = h('button', { class: on ? 'on' : '', onClick: () => navigate(t.r) }, t.l);
    bar.append(b);
  }
  return bar;
}

// ---- FAB (mobile quick-add) registry ----
const fabRegistry = {};
export function registerFab(routeKey, fn) { fabRegistry[routeKey] = fn; }
export function getFab(path) {
  return fabRegistry['/' + path.split('/')[1]] || fabRegistry[sectionOf(path)] || null;
}

// page header with optional action button(s)
export function pageHeader(title, sub, actions) {
  return h('div', { class: 'page-head' },
    h('div', {},
      h('div', { class: 'page-title' }, title),
      sub ? h('div', { class: 'page-sub' }, sub) : null,
    ),
    actions ? h('div', { class: 'flex gap-8 wrap' }, ...[].concat(actions)) : null,
  );
}
