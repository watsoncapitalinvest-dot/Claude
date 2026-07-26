// views/dashboard.js — the home overview
import { h, money, moneyShort, todayISO, relDay, daysUntil, iso, fmtDate, sum, sortBy } from '../utils.js';
import { state, update, netWorth, monthSpend, monthIncome, billNextDue, catById, spentByCategory, totalDebt, creditCardDebt, debtPayoffPlan, addMonths } from '../store.js';
import { navigate } from '../router.js';
import { whoPill, progress } from './parts.js';

function greeting() {
  const hr = new Date().getHours();
  const g = hr < 5 ? 'Good night' : hr < 12 ? 'Good morning' : hr < 18 ? 'Good afternoon' : 'Good evening';
  const names = state.profile.people.map(p => p.name).filter(Boolean);
  return names.length ? `${g}, ${names.join(' & ')}` : g;
}

export function renderDashboard() {
  const wrap = h('div');
  const nw = netWorth();
  const spend = monthSpend(), income = monthIncome();

  wrap.append(h('div', { class: 'page-head' },
    h('div', {},
      h('div', { class: 'page-title' }, greeting()),
      h('div', { class: 'page-sub' }, fmtDate(new Date(), { withYear: true, weekday: true })),
    ),
    h('div', { class: 'flex gap-8' },
      h('button', { class: 'btn hide-mobile', onClick: () => navigate('/settings') }, '⚙️ Settings'),
    ),
  ));

  // ---- top stat tiles ----
  const tiles = h('div', { class: 'grid cols-4 keep', style: { marginBottom: '20px' } },
    statTile('Net worth', money(nw.net, { cents: false }), nw.debts ? `${money(nw.assets,{cents:false})} − ${money(nw.debts,{cents:false})} debt` : 'across all accounts', '/money', 'var(--green)'),
    statTile('Spent this month', money(spend, { cents: false }), income ? `${money(income,{cents:false})} in` : 'so far', '/spending', 'var(--accent)'),
    statTile('Open tasks', String(state.tasks.filter(t => !t.done).length), `${state.tasks.filter(t=>!t.done && t.due && daysUntil(t.due)<0).length} overdue`, '/tasks', 'var(--blue)'),
    statTile('Shopping', String(sum(state.lists, l => l.items.filter(i => !i.done).length)), 'items to buy', '/shopping', 'var(--violet)'),
  );
  wrap.append(tiles);

  // ---- two column body ----
  const cols = h('div', { class: 'grid cols-2', style: { alignItems: 'start' } });

  // LEFT: money side
  const left = h('div', { class: 'grid', style: { gap: '16px' } });
  left.append(debtSummaryCard());
  left.append(upcomingBillsCard());
  left.append(budgetGlanceCard());
  left.append(goalsCard());

  // RIGHT: life side
  const right = h('div', { class: 'grid', style: { gap: '16px' } });
  right.append(todayCard());
  right.append(tasksCard());
  right.append(shoppingCard());

  cols.append(left, right);
  wrap.append(cols);
  return wrap;
}

function statTile(label, value, delta, route, color) {
  return h('div', { class: 'card stat pointer', onClick: () => navigate(route) },
    h('div', { class: 'label' }, label),
    h('div', { class: 'value sm', style: { color } }, value),
    h('div', { class: 'delta muted' }, delta),
  );
}

function cardShell(title, route, bodyNodes, actionLabel) {
  const head = h('div', { class: 'row between', style: { borderBottom: '1px solid var(--border)' } },
    h('div', { class: 't' }, title),
    route ? h('button', { class: 'btn ghost sm', onClick: () => navigate(route) }, actionLabel || 'View all →') : null,
  );
  return h('div', { class: 'card' }, head, ...[].concat(bodyNodes));
}

function debtSummaryCard() {
  const total = totalDebt();
  if (total <= 0.5) return null;
  const cc = creditCardDebt();
  const plan = debtPayoffPlan(state.debtPlan || {});
  const free = plan.feasible ? addMonths(plan.months) : null;
  const body = [
    h('div', { class: 'row', style: { alignItems: 'stretch' } },
      h('div', { class: 'grow' },
        h('div', { class: 's', style: { fontWeight: 600 } }, 'Credit card debt'),
        h('div', { style: { fontSize: '24px', fontWeight: 750, color: 'var(--red)', letterSpacing: '-.02em' } }, money(cc, { cents: false }))),
      h('div', { class: 'tr' },
        h('div', { class: 's', style: { fontWeight: 600 } }, 'Total debt'),
        h('div', { style: { fontSize: '24px', fontWeight: 750, letterSpacing: '-.02em' } }, money(total, { cents: false })))),
  ];
  if (free) body.push(h('div', { class: 'row', style: { background: 'var(--green-soft)' } },
    h('div', { class: 'grow t', style: { color: 'var(--green)' } }, '🎯 Debt-free target'),
    h('div', { class: 'amt', style: { color: 'var(--green)' } }, fmtDate(free, { withYear: true }).replace(/\s\d+,/, ','))));
  return cardShell('💳 Debt', '/debt', body, 'Payoff plan →');
}

function upcomingBillsCard() {
  const upcoming = sortBy(
    state.bills.map(b => ({ b, due: billNextDue(b), d: daysUntil(billNextDue(b)) })),
    x => x.d).slice(0, 4);
  const body = upcoming.length ? upcoming.map(({ b, due, d }) =>
    h('div', { class: 'row' },
      h('div', { class: 'lead' }, catById(b.category).icon),
      h('div', { class: 'grow' },
        h('div', { class: 't' }, b.name),
        h('div', { class: 's' }, relDay(due) + (b.autopay ? ' · auto-pay' : '')),
      ),
      h('div', { class: 'amt' }, money(b.amount)),
    ))
    : [h('div', { class: 'list-empty', style: { padding: '22px' } }, 'No bills yet')];
  return cardShell('📅 Upcoming bills', '/bills', body);
}

function budgetGlanceCard() {
  const budgets = Object.entries(state.budgets).filter(([,v]) => v > 0);
  if (!budgets.length) return null;
  const spentMap = spentByCategory();
  const rows = sortBy(budgets, ([cat, amt]) => -((spentMap[cat]||0)/amt)).slice(0, 4).map(([cat, amt]) => {
    const spent = spentMap[cat] || 0; const pct = (spent/amt)*100;
    const c = catById(cat);
    return h('div', { class: 'row', style: { flexDirection: 'column', alignItems: 'stretch', gap: '7px' } },
      h('div', { class: 'flex between' },
        h('div', { class: 'flex gap-8' }, h('span', {}, c.icon), h('span', { class: 't' }, c.name)),
        h('div', { class: 's tabnum' }, `${money(spent,{cents:false})} / ${money(amt,{cents:false})}`),
      ),
      progress(pct, pct > 100 ? 'var(--red)' : pct > 85 ? 'var(--gold)' : c.color),
    );
  });
  return cardShell('📊 Budget this month', '/budgets', rows);
}

function goalsCard() {
  if (!state.goals.length) return null;
  const rows = state.goals.slice(0, 3).map(g => {
    const pct = g.target ? (g.saved / g.target) * 100 : 0;
    return h('div', { class: 'row', style: { flexDirection: 'column', alignItems: 'stretch', gap: '7px' } },
      h('div', { class: 'flex between' },
        h('span', { class: 't' }, g.name),
        h('span', { class: 's tabnum' }, `${money(g.saved,{cents:false})} / ${money(g.target,{cents:false})}`),
      ),
      progress(pct, g.color),
    );
  });
  return cardShell('✨ Goals', '/goals', rows);
}

function todayCard() {
  const t = todayISO();
  const events = sortBy(state.events.filter(e => e.date === t), e => e.time || '');
  const meal = state.meals[t];
  const body = [];
  if (meal?.dinner) body.push(h('div', { class: 'row' }, h('div', { class: 'lead' }, '🍽️'),
    h('div', { class: 'grow' }, h('div', { class: 't' }, meal.dinner), h('div', { class: 's' }, "Tonight's dinner"))));
  events.forEach(e => body.push(h('div', { class: 'row' },
    h('div', { class: 'lead' }, '📌'),
    h('div', { class: 'grow' }, h('div', { class: 't' }, e.title), h('div', { class: 's' }, e.time || 'Today')),
    e.who ? whoPill(e.who) : null)));
  if (!body.length) body.push(h('div', { class: 'list-empty', style: { padding: '22px' } }, 'Nothing scheduled today 🌿'));
  return cardShell('☀️ Today', '/calendar', body);
}

function tasksCard() {
  const open = sortBy(state.tasks.filter(t => !t.done), t => t.due || '9999').slice(0, 5);
  const body = open.length ? open.map(t => h('div', { class: 'row' },
    h('div', { class: 'check', onClick: (e) => { e.stopPropagation(); toggleTask(t.id); } }, ''),
    h('div', { class: 'grow' },
      h('div', { class: 't' }, t.title),
      t.due ? h('div', { class: 's', style: daysUntil(t.due) < 0 ? { color: 'var(--red)' } : {} }, relDay(t.due)) : null),
    t.who ? whoPill(t.who) : null,
  )) : [h('div', { class: 'list-empty', style: { padding: '22px' } }, 'All caught up ✅')];
  return cardShell('✅ Tasks', '/tasks', body);
}
function toggleTask(id) {
  update(s => { const t = s.tasks.find(x => x.id === id); if (t) t.done = !t.done; });
}

function shoppingCard() {
  const list = state.lists.find(l => l.items.some(i => !i.done)) || state.lists[0];
  if (!list) return cardShell('🛒 Shopping', '/shopping', [h('div', { class: 'list-empty', style: { padding: '22px' } }, 'No lists yet')]);
  const todo = list.items.filter(i => !i.done).slice(0, 5);
  const body = todo.length ? todo.map(i => h('div', { class: 'row' },
    h('div', { class: 'check', onClick: () => toggleItem(list.id, i.id) }, ''),
    h('div', { class: 'grow t' }, i.text)))
    : [h('div', { class: 'list-empty', style: { padding: '22px' } }, `${list.name} — all done!`)];
  return cardShell(`🛒 ${list.name}`, '/shopping', body);
}
function toggleItem(listId, itemId) {
  update(s => { const l = s.lists.find(x => x.id === listId); const it = l?.items.find(x => x.id === itemId); if (it) it.done = !it.done; });
}
