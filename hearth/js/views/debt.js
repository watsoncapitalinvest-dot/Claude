// views/debt.js — credit-card & debt payoff tracker with amortization
import { h, money, moneyShort, fmtDate, sortBy, sum, clamp } from '../utils.js';
import {
  state, update, accountBalance, acctType, isLiability, catById,
  liabilities, creditCardDebt, totalDebt, totalMinPayments,
  amortize, debtPayoffPlan, addMonths,
} from '../store.js';
import { subTabs, pageHeader, registerFab } from '../nav.js';
import { formModal, field, input, select, segmented, closeModal, toast, modal } from '../ui.js';
import { progress } from './parts.js';
import { navigate } from '../router.js';

export function renderDebt() {
  registerFab('/debt', () => navigate('/money'));
  const wrap = h('div');
  wrap.append(pageHeader('Debt Payoff', 'Your path to paying it all off',
    h('button', { class: 'btn hide-mobile', onClick: () => navigate('/money') }, '+ Add a debt')));
  wrap.append(subTabs('money'));

  const debts = liabilities();
  const cc = creditCardDebt();
  const all = totalDebt();

  // ---- empty / celebration ----
  if (!debts.length || all <= 0.5) {
    wrap.append(h('div', { class: 'card' }, h('div', { class: 'list-empty' },
      h('span', { class: 'em' }, debts.length ? '🎉' : '💳'),
      h('div', { style: { fontWeight: 700, fontSize: '17px' } }, debts.length ? "You're debt-free!" : 'No debts tracked'),
      h('div', { style: { fontSize: '13.5px', marginTop: '6px', maxWidth: '360px', margin: '6px auto 0' } },
        debts.length ? 'Nothing owed across your accounts. Amazing.' : 'Add a credit card or loan account with its balance, interest rate, and monthly payment to see how long until it’s paid off.'),
      !debts.length ? h('button', { class: 'btn primary', style: { marginTop: '14px' }, onClick: () => navigate('/money') }, 'Add a debt account') : null,
    )));
    return wrap;
  }

  // ---- grand totals ----
  wrap.append(h('div', { class: 'grid cols-3 keep', style: { marginBottom: '16px' } },
    totalTile('Credit card debt', money(cc), `${state.accounts.filter(a => a.type === 'credit').length} card${state.accounts.filter(a => a.type === 'credit').length !== 1 ? 's' : ''}`, 'var(--red)'),
    totalTile('Total debt', money(all), `${debts.length} account${debts.length !== 1 ? 's' : ''}`, 'var(--accent)'),
    totalTile('Monthly minimums', money(totalMinPayments()), 'due each month', 'var(--gold)'),
  ));

  // ---- combined payoff plan ----
  wrap.append(payoffPlanCard());

  // ---- per-debt cards ----
  wrap.append(h('h2', { class: 'sec' }, '💳 Each debt'));
  const grid = h('div', { class: 'grid auto' });
  for (const a of sortBy(debts, x => -accountBalance(x))) grid.append(debtCard(a));
  wrap.append(grid);

  return wrap;
}

function totalTile(label, value, sub, color) {
  return h('div', { class: 'card stat' },
    h('div', { class: 'label' }, label),
    h('div', { class: 'value sm', style: { color } }, value),
    h('div', { class: 'delta muted' }, sub));
}

// ---------- combined plan ----------
function payoffPlanCard() {
  const plan = state.debtPlan || { extra: 0, strategy: 'avalanche' };
  const result = debtPayoffPlan(plan);
  const card = h('div', { class: 'card pad', style: { marginBottom: '4px' } });

  card.append(h('div', { class: 'flex between wrap', style: { gap: '10px', marginBottom: '14px' } },
    h('div', { class: 't', style: { fontSize: '16px' } }, '🎯 Your payoff plan'),
    h('div', { class: 'flex gap-6' },
      strategyBtn('avalanche', 'Avalanche', plan),
      strategyBtn('snowball', 'Snowball', plan),
    )));

  // extra payment control
  const extraInput = h('input', {
    class: 'input', type: 'number', inputmode: 'decimal', min: '0', step: '10',
    value: plan.extra || 0, style: { maxWidth: '140px' },
    onInput: (e) => { const v = Math.max(0, parseFloat(e.target.value) || 0); update(s => s.debtPlan = { ...s.debtPlan, extra: v }); },
  });
  card.append(h('div', { class: 'flex between wrap', style: { gap: '10px', alignItems: 'center', marginBottom: '14px' } },
    h('div', {}, h('div', { style: { fontWeight: 600, fontSize: '14px' } }, 'Extra payment / month'),
      h('div', { class: 'hint', style: { margin: 0 } }, 'Anything on top of the minimums')),
    h('div', { class: 'flex gap-6', style: { alignItems: 'center' } }, h('span', { class: 'dim' }, '+'), extraInput)));

  if (!result.feasible) {
    card.append(h('div', { class: 'card pad', style: { background: 'var(--red-soft)', color: 'var(--red)', fontSize: '13.5px', fontWeight: 600 } },
      '⚠️ At these payments the balances never fully clear — the interest is too high. Try adding a bit more to the monthly payment above.'));
    return card;
  }

  const debtFree = addMonths(result.months);
  card.append(h('div', { class: 'grid cols-3 keep', style: { gap: '12px', marginTop: '4px' } },
    planStat('Debt-free in', humanMonths(result.months)),
    planStat('Payoff date', debtFree ? fmtDate(debtFree, { withYear: true }).replace(/\s\d+,/, ',') : '—'),
    planStat('Total interest', money(result.totalInterest, { cents: false })),
  ));

  // payoff order timeline
  const ordered = sortBy(Object.entries(result.perDebt), ([, p]) => p.paidMonth || 9999);
  if (ordered.length > 1) {
    card.append(h('div', { class: 'divider' }));
    card.append(h('div', { class: 'hint', style: { marginTop: 0, marginBottom: '8px', fontWeight: 700 } }, `Order they’ll be cleared (${plan.strategy})`));
    ordered.forEach(([id, p], i) => {
      const d = addMonths(p.paidMonth);
      card.append(h('div', { class: 'flex gap-12', style: { padding: '6px 0', alignItems: 'center' } },
        h('div', { style: { width: '22px', height: '22px', borderRadius: '50%', background: p.color || 'var(--accent)', color: '#fff', display: 'grid', placeItems: 'center', fontSize: '11px', fontWeight: 800, flex: '0 0 auto' } }, String(i + 1)),
        h('div', { class: 'grow t', style: { fontSize: '14px' } }, p.name),
        h('div', { class: 's dim nowrap' }, d ? fmtDate(d, { withYear: true }).replace(/\s\d+,/, ',') : '—'),
      ));
    });
    // compare with minimum-only
    const baseline = debtPayoffPlan({ extra: 0, strategy: plan.strategy });
    if (plan.extra > 0 && baseline.feasible && baseline.months > result.months) {
      const saved = baseline.totalInterest - result.totalInterest;
      const faster = baseline.months - result.months;
      card.append(h('div', { class: 'card pad', style: { background: 'var(--green-soft)', color: 'var(--green)', fontSize: '13px', fontWeight: 650, marginTop: '10px' } },
        `💪 That extra ${money(plan.extra, { cents: false })}/mo pays you off ${humanMonths(faster)} sooner and saves ${money(saved, { cents: false })} in interest.`));
    }
  }
  return card;
}

function strategyBtn(key, label, plan) {
  const on = (plan.strategy || 'avalanche') === key;
  return h('button', { class: 'btn sm' + (on ? ' primary' : ''), title: key === 'avalanche' ? 'Highest interest rate first (saves the most)' : 'Smallest balance first (quick wins)',
    onClick: () => update(s => s.debtPlan = { ...s.debtPlan, strategy: key }) }, label);
}
function planStat(label, value) {
  return h('div', { style: { textAlign: 'center', padding: '4px' } },
    h('div', { class: 'label', style: { fontSize: '11px', color: 'var(--text-soft)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.03em' } }, label),
    h('div', { style: { fontSize: '19px', fontWeight: 750, letterSpacing: '-.02em', marginTop: '3px' } }, value));
}

// ---------- per-debt ----------
function debtCard(a) {
  const bal = accountBalance(a);
  const orig = Number(a.originalBalance) || bal;
  const paidOff = clamp(((orig - bal) / (orig || 1)) * 100, 0, 100);
  const hasDetails = a.apr != null && a.minPayment != null && a.minPayment > 0;
  const am = hasDetails ? amortize(bal, a.apr, a.minPayment) : null;

  const card = h('div', { class: 'card pad', style: { display: 'flex', flexDirection: 'column', gap: '10px' } });
  card.append(h('div', { class: 'flex between' },
    h('div', { class: 'flex gap-8' },
      h('div', { class: 'lead', style: { width: '34px', height: '34px', background: (a.color || '#c0433a') + '22', color: a.color || '#c0433a' } }, acctType(a.type).icon),
      h('div', {}, h('div', { style: { fontWeight: 700 } }, a.name), a.institution ? h('div', { class: 's dim' }, a.institution) : null)),
    h('button', { class: 'icon-btn', title: 'Edit', onClick: () => navigate('/money') }, '✎')));

  card.append(h('div', {},
    h('div', { class: 'flex between', style: { marginBottom: '6px', alignItems: 'baseline' } },
      h('span', { style: { fontWeight: 750, fontSize: '22px', color: 'var(--red)' } }, money(bal)),
      h('span', { class: 's dim' }, orig > bal ? `of ${money(orig, { cents: false })}` : 'owed')),
    progress(paidOff, 'var(--green)'),
    h('div', { class: 'hint', style: { margin: '5px 0 0' } }, orig > bal ? `${Math.round(paidOff)}% paid off` : 'Set an original balance to track progress')));

  // stats row
  card.append(h('div', { class: 'flex gap-8 wrap', style: { fontSize: '12.5px' } },
    a.apr != null ? h('span', { class: 'chip' }, `${a.apr}% APR`) : h('span', { class: 'chip', style: { color: 'var(--accent-ink)' } }, 'Add APR'),
    a.minPayment ? h('span', { class: 'chip' }, `${money(a.minPayment, { cents: false })}/mo`) : h('span', { class: 'chip', style: { color: 'var(--accent-ink)' } }, 'Add payment'),
  ));

  if (am) {
    if (am.neverPayoff) {
      card.append(h('div', { class: 'card pad', style: { background: 'var(--red-soft)', color: 'var(--red)', fontSize: '12.5px', fontWeight: 600 } },
        `⚠️ ${money(a.minPayment, { cents: false })}/mo barely covers interest — this won't pay down. Needs at least ${money(am.minToCover + 5, { cents: false })}/mo.`));
    } else {
      const d = addMonths(am.months);
      card.append(h('div', { class: 'flex between', style: { background: 'var(--surface-2)', borderRadius: '11px', padding: '10px 12px' } },
        h('div', {}, h('div', { class: 'dim', style: { fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' } }, 'Paid off in'),
          h('div', { style: { fontWeight: 700 } }, humanMonths(am.months))),
        h('div', { class: 'tr' }, h('div', { class: 'dim', style: { fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' } }, 'By'),
          h('div', { style: { fontWeight: 700 } }, d ? fmtDate(d, { withYear: true }).replace(/\s\d+,/, ',') : '—'))));
      card.append(h('button', { class: 'btn sm block', onClick: () => scheduleModal(a, am) }, '📅 See payoff schedule'));
    }
  } else {
    card.append(h('button', { class: 'btn sm primary block', onClick: () => navigate('/money') }, 'Add rate & payment →'));
  }
  return card;
}

// ---------- amortization schedule ----------
function scheduleModal(a, am) {
  const body = h('div');
  const d = addMonths(am.months);
  body.append(h('div', { class: 'flex between', style: { marginBottom: '12px', flexWrap: 'wrap', gap: '8px' } },
    h('div', { class: 'chip' }, `${money(accountBalance(a))} at ${a.apr}% APR`),
    h('div', { class: 'chip' }, `${money(a.minPayment, { cents: false })}/mo`)));
  body.append(h('div', { class: 'grid cols-3 keep', style: { gap: '10px', marginBottom: '14px' } },
    planStat('Months', String(am.months)),
    planStat('Payoff', d ? fmtDate(d, { withYear: true }).replace(/\s\d+,/, ',') : '—'),
    planStat('Interest', money(am.totalInterest, { cents: false }))));

  // schedule table (show every month; group by year for readability)
  const tableWrap = h('div', { style: { overflowX: 'auto', border: '1px solid var(--border)', borderRadius: '12px' } });
  const rows = [h('div', { class: 'row', style: { background: 'var(--surface-2)', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text-soft)', padding: '8px 12px' } },
    h('div', { style: { width: '60px', flex: '0 0 auto' } }, 'When'),
    h('div', { class: 'grow tr' }, 'Payment'),
    h('div', { class: 'grow tr' }, 'Interest'),
    h('div', { class: 'grow tr' }, 'Balance'))];
  am.payments.forEach((p, i) => {
    const md = addMonths(p.month);
    rows.push(h('div', { class: 'row', style: { padding: '7px 12px', fontSize: '12.5px' } },
      h('div', { style: { width: '60px', flex: '0 0 auto', fontWeight: 600 } }, md ? shortMonth(md) : '#' + p.month),
      h('div', { class: 'grow tr tabnum' }, money(p.payment)),
      h('div', { class: 'grow tr tabnum', style: { color: 'var(--red)' } }, money(p.interest)),
      h('div', { class: 'grow tr tabnum', style: { fontWeight: 600 } }, money(p.balance))));
  });
  tableWrap.append(...rows);
  body.append(tableWrap);

  modal({ title: `${a.name} — payoff schedule`, body, wide: true,
    footer: [h('button', { class: 'btn primary block', onClick: closeModal }, 'Close')] });
}

// ---------- helpers ----------
function humanMonths(n) {
  if (!isFinite(n)) return '—';
  if (n <= 0) return 'now';
  const y = Math.floor(n / 12), m = n % 12;
  if (y === 0) return `${m} mo`;
  if (m === 0) return `${y} yr`;
  return `${y} yr ${m} mo`;
}
function shortMonth(d) {
  return `${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()]} ’${String(d.getFullYear()).slice(2)}`;
}
