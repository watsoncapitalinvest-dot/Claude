// app.js — bootstrap, shell, lock screen, onboarding
import { h } from './utils.js';
import { state, subscribe, commit, update } from './store.js';
import { route, render, startRouter, navigate, currentPath } from './router.js';
import { SECTIONS, sectionOf, getFab } from './nav.js';
import { toast } from './ui.js';

// views
import { renderDashboard } from './views/dashboard.js';
import { renderOverview, renderSpending, renderBudgets, renderBills } from './views/money.js';
import { renderDebt } from './views/debt.js';
import { renderTasks, renderCalendar } from './views/plan.js';
import { renderShopping, renderMeals, renderInventory } from './views/household.js';
import { renderGoals, renderNotes } from './views/goals.js';
import { renderSettings } from './views/settings.js';
import { renderOnboarding } from './views/onboarding.js';

// ---- register routes ----
route('/dashboard', renderDashboard);
route('/money', renderOverview);
route('/spending', renderSpending);
route('/budgets', renderBudgets);
route('/bills', renderBills);
route('/debt', renderDebt);
route('/tasks', renderTasks);
route('/calendar', renderCalendar);
route('/shopping', renderShopping);
route('/meals', renderMeals);
route('/inventory', renderInventory);
route('/goals', renderGoals);
route('/notes', renderNotes);
route('/settings', renderSettings);

// ---------- theme ----------
export function applyTheme() {
  const t = state.profile.theme || 'auto';
  if (t === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', t);
}

// ---------- shell ----------
function buildShell() {
  const app = document.getElementById('app');
  app.innerHTML = '';

  const brand = h('div', { class: 'brand', style: { cursor: 'pointer' }, onClick: () => navigate('/dashboard') },
    h('div', { class: 'brand-mark' }, '🔥'),
    h('div', {},
      h('div', { class: 'brand-name' }, 'Hearth'),
      h('div', { class: 'brand-sub' }, state.profile.home || 'Our Home'),
    ),
  );

  // sidebar
  const side = h('aside', { class: 'sidebar' }, brand);
  const groups = [
    { label: null, items: [{ r: '/dashboard', i: '🏠', l: 'Home' }] },
    { label: 'Money', items: [
      { r: '/money', i: '💰', l: 'Accounts' },
      { r: '/spending', i: '🧾', l: 'Spending' },
      { r: '/budgets', i: '📊', l: 'Budgets' },
      { r: '/bills', i: '📅', l: 'Bills & Subscriptions' },
      { r: '/debt', i: '💳', l: 'Debt Payoff' },
    ]},
    { label: 'Plan', items: [
      { r: '/tasks', i: '✅', l: 'Tasks' },
      { r: '/calendar', i: '🗓️', l: 'Calendar' },
    ]},
    { label: 'Household', items: [
      { r: '/shopping', i: '🛒', l: 'Shopping Lists' },
      { r: '/meals', i: '🍽️', l: 'Meal Plan' },
      { r: '/inventory', i: '📦', l: 'Home Inventory' },
    ]},
    { label: 'Together', items: [
      { r: '/goals', i: '✨', l: 'Goals' },
      { r: '/notes', i: '📝', l: 'Notes' },
    ]},
  ];
  for (const g of groups) {
    if (g.label) side.append(h('div', { class: 'nav-section' }, g.label));
    for (const it of g.items) {
      side.append(h('a', { class: 'nav-link', href: '#' + it.r, 'data-route': it.r },
        h('span', { class: 'ico' }, it.i), it.l));
    }
  }
  side.append(h('div', { class: 'sidebar-foot' },
    h('a', { class: 'nav-link', href: '#/settings', 'data-route': '/settings' },
      h('span', { class: 'ico' }, '⚙️'), 'Settings'),
  ));

  // top bar (mobile)
  const topbar = h('div', { class: 'topbar' },
    h('div', { class: 'brand-mark', style: { width: '30px', height: '30px', fontSize: '17px' }, onClick: () => navigate('/dashboard') }, '🔥'),
    h('div', { class: 'brand-name', style: { fontSize: '17px', flex: '1' } }, 'Hearth'),
    h('button', { class: 'icon-btn', 'aria-label': 'Settings', onClick: () => navigate('/settings') }, '⚙️'),
  );

  // main + outlet
  const outlet = h('div', { id: 'view-outlet' });
  const main = h('main', { class: 'main' }, topbar, h('div', { class: 'content' }, outlet));

  // bottom nav (mobile)
  const bottom = h('nav', { class: 'bottom-nav' });
  for (const s of SECTIONS) {
    bottom.append(h('a', { href: '#' + s.route, 'data-section': s.key },
      h('span', { class: 'ico' }, s.icon), s.label));
  }

  const fab = h('button', { class: 'fab', id: 'fab', 'aria-label': 'Add', onClick: onFab }, '+');

  const shell = h('div', { class: 'app-shell' }, side, main);
  app.append(shell, bottom, fab);
}

function highlightNav() {
  const path = currentPath();
  const sec = sectionOf(path);
  document.querySelectorAll('.nav-link[data-route]').forEach(a => {
    const r = a.getAttribute('data-route');
    a.classList.toggle('active', r === path || ('/' + path.split('/')[1]) === r);
  });
  document.querySelectorAll('.bottom-nav a[data-section]').forEach(a => {
    a.classList.toggle('active', a.getAttribute('data-section') === sec);
  });
  // show FAB on views that support quick-add
  const fab = document.getElementById('fab');
  if (fab) fab.classList.toggle('show', !!getFab(path));
}

function onFab() { getFab(currentPath())?.(); }

// ---------- lock screen ----------
let unlocked = false;
function renderLock() {
  const app = document.getElementById('app');
  app.innerHTML = '';
  let entered = '';
  const dots = h('div', { class: 'pin-dots' }, ...[0,1,2,3].map(() => h('span')));
  const msg = h('div', { class: 'muted', style: { minHeight: '20px', fontSize: '14px' } }, 'Enter your PIN');
  const refresh = () => dots.querySelectorAll('span').forEach((s, i) => s.classList.toggle('on', i < entered.length));
  const press = (d) => {
    if (entered.length >= 4) return;
    entered += d; refresh();
    if (entered.length === 4) {
      setTimeout(() => {
        if (entered === state.profile.pin) { unlocked = true; boot(); }
        else { msg.textContent = 'Incorrect PIN — try again'; entered = ''; refresh(); }
      }, 120);
    }
  };
  const del = () => { entered = entered.slice(0, -1); refresh(); };
  const keypad = h('div', { class: 'keypad' });
  ['1','2','3','4','5','6','7','8','9'].forEach(n => keypad.append(h('button', { onClick: () => press(n) }, n)));
  keypad.append(h('button', { class: 'ghost', style: { fontSize: '15px', color: 'var(--text-dim)' } }, ''));
  keypad.append(h('button', { onClick: () => press('0') }, '0'));
  keypad.append(h('button', { style: { fontSize: '20px' }, onClick: del }, '⌫'));

  app.append(h('div', { class: 'lock' },
    h('div', { class: 'lock-card' },
      h('div', { class: 'brand-mark' }, '🔥'),
      h('div', { class: 'brand-name', style: { fontSize: '24px' } }, 'Hearth'),
      msg, dots, keypad,
    ),
  ));
}

// ---------- boot ----------
function boot() {
  applyTheme();
  if (state.profile.pin && !unlocked) { renderLock(); return; }
  if (!state.profile.onboarded) { renderOnboarding(finishBoot); return; }
  finishBoot();
}
function finishBoot() {
  buildShell();
  startRouter();
  render();
  highlightNav();
}

subscribe(() => {
  // re-render current view + nav on any state change (unless on lock/onboard)
  if (document.getElementById('view-outlet')) { render(); highlightNav(); applyThemeIfChanged(); }
});
document.addEventListener('route:changed', highlightNav);

let lastTheme = state.profile.theme;
function applyThemeIfChanged() {
  if (state.profile.theme !== lastTheme) { lastTheme = state.profile.theme; applyTheme(); }
  const homeEl = document.querySelector('.brand-sub');
  if (homeEl) homeEl.textContent = state.profile.home || 'Our Home';
}

// service worker (offline)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}));
}

boot();
export { boot };
