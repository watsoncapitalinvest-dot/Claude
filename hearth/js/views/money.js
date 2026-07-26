// views/money.js — accounts/net worth, spending log, budgets, bills
import { h, money, moneyShort, todayISO, fmtDate, relDay, daysUntil, iso, parseISO, sum, sortBy, groupBy, uid, monthKey, fmtMonth } from '../utils.js';
import {
  state, update, netWorth, accountBalance, catById, CATEGORIES, ACCOUNT_TYPES, acctType, isLiability,
  txForMonth, spentByCategory, monthSpend, monthIncome, billNextDue,
} from '../store.js';
import { subTabs, pageHeader, registerFab } from '../nav.js';
import { formModal, field, input, select, segmented, closeModal, confirmDialog, toast, modal } from '../ui.js';
import { whoPill, progress } from './parts.js';
import { navigate } from '../router.js';

const peopleOpts = () => [{ value: '', label: 'Anyone' }, ...state.profile.people.map(p => ({ value: p.id, label: p.name }))];
const catOpts = () => CATEGORIES.map(c => ({ value: c.id, label: `${c.icon} ${c.name}` }));
const acctOpts = () => state.accounts.map(a => ({ value: a.id, label: a.name }));

// ============================================================
// OVERVIEW — accounts & net worth
// ============================================================
export function renderOverview() {
  registerFab('/money', () => accountModal());
  const wrap = h('div');
  wrap.append(pageHeader('Money', state.profile.home,
    h('button', { class: 'btn primary hide-mobile', onClick: () => accountModal() }, '+ Account')));
  wrap.append(subTabs('money'));

  const nw = netWorth();
  wrap.append(h('div', { class: 'grid cols-3 keep', style: { marginBottom: '18px' } },
    bigStat('Net worth', money(nw.net), 'assets − debts', 'var(--green)'),
    bigStat('Assets', money(nw.assets), `${state.accounts.filter(a=>!isLiability(a.type)).length} accounts`, 'var(--blue)'),
    bigStat('Debts', money(nw.debts), `${state.accounts.filter(a=>isLiability(a.type)).length} accounts`, 'var(--red)'),
  ));

  if (!state.accounts.length) {
    wrap.append(h('div', { class: 'card' }, h('div', { class: 'list-empty' },
      h('span', { class: 'em' }, '🏦'),
      h('div', { style: { fontWeight: 650 } }, 'Add your accounts'),
      h('div', { style: { fontSize: '13px', marginTop: '4px' } }, 'Checking, savings, credit cards, investments — see everything in one place.'),
      h('button', { class: 'btn primary', style: { marginTop: '14px' }, onClick: () => accountModal() }, '+ Add an account'),
    )));
    return wrap;
  }

  // group assets vs liabilities
  const assets = state.accounts.filter(a => !isLiability(a.type));
  const debts = state.accounts.filter(a => isLiability(a.type));
  const renderGroup = (title, list) => {
    if (!list.length) return null;
    const card = h('div', { class: 'card', style: { marginBottom: '16px' } });
    card.append(h('div', { class: 'row', style: { background: 'var(--surface-2)', borderRadius: '16px 16px 0 0' } },
      h('div', { class: 't grow' }, title),
      h('div', { class: 'amt' }, money(sum(list, accountBalance)))));
    for (const a of sortBy(list, x => -accountBalance(x))) {
      const bal = accountBalance(a);
      card.append(h('div', { class: 'row pointer', onClick: () => accountModal(a) },
        h('div', { class: 'lead', style: { background: (a.color || 'var(--surface-2)') + '22', color: a.color } }, acctType(a.type).icon),
        h('div', { class: 'grow' },
          h('div', { class: 't' }, a.name),
          h('div', { class: 's' }, [acctType(a.type).name, a.institution].filter(Boolean).join(' · '))),
        h('div', { class: 'amt', style: isLiability(a.type) ? { color: 'var(--red)' } : {} }, money(bal)),
      ));
    }
    return card;
  };
  wrap.append(renderGroup('Assets', assets));
  wrap.append(renderGroup('Debts', debts));
  return wrap;
}

function bigStat(label, value, sub, color) {
  return h('div', { class: 'card stat' },
    h('div', { class: 'label' }, label),
    h('div', { class: 'value', style: { color } }, value),
    h('div', { class: 'delta muted' }, sub));
}

function accountModal(acc = null) {
  const editing = !!acc;
  formModal({
    title: editing ? 'Edit account' : 'Add account',
    submitLabel: editing ? 'Save' : 'Add account',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => {
      confirmDialog({ title: 'Delete account?', message: `Remove "${acc.name}"? Transactions stay but lose their account link.`, confirm: 'Delete', onConfirm: () => { update(s => s.accounts = s.accounts.filter(a => a.id !== acc.id)); toast('Account deleted'); } });
    } }, 'Delete') : null,
    build(refs) {
      refs.name = input({ placeholder: 'e.g. Everyday Checking', value: acc?.name || '' });
      refs.type = select(ACCOUNT_TYPES.map(t => ({ value: t.id, label: `${t.icon} ${t.name}` })), acc?.type || 'checking');
      refs.bal = input({ type: 'number', step: '0.01', inputmode: 'decimal', placeholder: '0.00', value: acc ? accountBalance(acc) : '' });
      refs.inst = input({ placeholder: 'Bank / provider (optional)', value: acc?.institution || '' });
      refs.color = input({ type: 'color', value: acc?.color || '#3f6fa8', style: { height: '44px', padding: '4px' } });
      const balLabel = h('label', {}, editing ? 'Current balance' : 'Starting balance');
      const liabNote = h('div', { class: 'hint' }, 'For credit cards & loans, enter the amount you owe.');
      return [
        field('Account name', refs.name),
        h('div', { class: 'row-2' }, field('Type', refs.type), field('Provider', refs.inst)),
        h('div', { class: 'field' }, balLabel, refs.bal, liabNote),
        field('Color', refs.color),
      ];
    },
    onSubmit(refs) {
      const name = refs.name.value.trim();
      if (!name) throw new Error('Give the account a name');
      const type = refs.type.value;
      const enteredBal = parseFloat(refs.bal.value || '0') || 0;
      update(s => {
        if (editing) {
          const a = s.accounts.find(x => x.id === acc.id);
          // adjust opening so computed balance matches entered
          const others = accountBalance(a) - a.opening;
          Object.assign(a, { name, type, institution: refs.inst.value.trim(), color: refs.color.value, opening: enteredBal - others });
        } else {
          s.accounts.push({ id: uid('acc'), name, type, institution: refs.inst.value.trim(), color: refs.color.value, opening: enteredBal });
        }
      });
      closeModal();
      toast(editing ? 'Account saved' : 'Account added');
    },
  });
}

// ============================================================
// SPENDING — transaction log
// ============================================================
let spendMonth = monthKey();
export function renderSpending() {
  registerFab('/spending', () => txModal());
  const wrap = h('div');
  wrap.append(pageHeader('Spending', 'Track what comes in and goes out',
    h('button', { class: 'btn primary hide-mobile', onClick: () => txModal() }, '+ Transaction')));
  wrap.append(subTabs('money'));

  // month selector
  wrap.append(monthNav(spendMonth, (m) => { spendMonth = m; navigate('/spending'); }));

  const txs = sortBy(txForMonth(spendMonth), t => t.date, -1);
  const inc = monthIncome(spendMonth), spent = monthSpend(spendMonth);
  wrap.append(h('div', { class: 'grid cols-3 keep', style: { margin: '14px 0 18px' } },
    bigStat('In', money(inc), 'income', 'var(--green)'),
    bigStat('Out', money(spent), 'expenses', 'var(--red)'),
    bigStat('Net', money(inc - spent), inc - spent >= 0 ? 'saved' : 'over', inc - spent >= 0 ? 'var(--green)' : 'var(--red)'),
  ));

  if (!txs.length) {
    wrap.append(h('div', { class: 'card' }, h('div', { class: 'list-empty' },
      h('span', { class: 'em' }, '🧾'),
      h('div', { style: { fontWeight: 650 } }, 'No transactions this month'),
      h('button', { class: 'btn primary', style: { marginTop: '14px' }, onClick: () => txModal() }, '+ Add one'))));
    return wrap;
  }

  const byDay = groupBy(txs, t => t.date);
  const card = h('div', { class: 'card' });
  for (const day of sortBy(Object.keys(byDay), d => d, -1)) {
    card.append(h('div', { class: 'row', style: { background: 'var(--surface-2)', padding: '7px 16px' } },
      h('div', { class: 's grow', style: { fontWeight: 700, color: 'var(--text-soft)' } }, fmtDate(day, { weekday: true, withYear: parseISO(day).getFullYear() !== new Date().getFullYear() })),
      h('div', { class: 's tabnum' }, money(sum(byDay[day].filter(t=>t.type==='expense'), t=>t.amount) - sum(byDay[day].filter(t=>t.type==='income'), t=>t.amount), { sign: false }))));
    for (const t of byDay[day]) card.append(txRow(t));
  }
  wrap.append(card);
  return wrap;
}

function txRow(t) {
  const c = catById(t.category);
  const acc = state.accounts.find(a => a.id === t.accountId);
  const isIn = t.type === 'income';
  return h('div', { class: 'row pointer', onClick: () => txModal(t) },
    h('div', { class: 'lead', style: { background: c.color + '22', color: c.color } }, isIn ? '💰' : c.icon),
    h('div', { class: 'grow' },
      h('div', { class: 't' }, t.note || c.name),
      h('div', { class: 's' }, [c.name, acc?.name].filter(Boolean).join(' · '))),
    t.who ? whoPill(t.who) : null,
    h('div', { class: 'amt', style: { color: isIn ? 'var(--green)' : 'var(--text)' } },
      (isIn ? '+' : t.type === 'transfer' ? '⇄ ' : '−') + money(t.amount)),
  );
}

function txModal(tx = null) {
  const editing = !!tx;
  if (!state.accounts.length) { toast('Add an account first'); accountModal(); return; }
  let type = tx?.type || 'expense';
  formModal({
    title: editing ? 'Edit transaction' : 'Add transaction',
    submitLabel: editing ? 'Save' : 'Add',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.transactions = s.transactions.filter(x => x.id !== tx.id)); closeModal(); toast('Deleted'); } }, 'Delete') : null,
    build(refs) {
      refs.typeSeg = segmented([{ value: 'expense', label: '− Expense' }, { value: 'income', label: '+ Income' }, { value: 'transfer', label: '⇄ Transfer' }], type, (v) => {
        type = v;
        refs.catField.style.display = v === 'expense' ? '' : 'none';
        refs.toField.style.display = v === 'transfer' ? '' : 'none';
      });
      refs.amount = input({ type: 'number', step: '0.01', inputmode: 'decimal', placeholder: '0.00', value: tx?.amount || '', style: { fontSize: '22px', fontWeight: '700' } });
      refs.note = input({ placeholder: 'What was it? (optional)', value: tx?.note || '' });
      refs.cat = select(catOpts(), tx?.category || 'groceries');
      refs.acct = select(acctOpts(), tx?.accountId || state.accounts[0].id);
      refs.toAcct = select(acctOpts(), tx?.toAccountId || state.accounts[1]?.id || state.accounts[0].id);
      refs.date = input({ type: 'date', value: tx?.date || todayISO() });
      refs.who = select(peopleOpts(), tx?.who || '');
      refs.catField = field('Category', refs.cat);
      refs.toField = field('To account', refs.toAcct);
      refs.catField.style.display = type === 'expense' ? '' : 'none';
      refs.toField.style.display = type === 'transfer' ? '' : 'none';
      return [
        field(null, refs.typeSeg),
        field('Amount', refs.amount),
        field('Note', refs.note),
        refs.catField,
        field(type === 'transfer' ? 'From account' : 'Account', refs.acct),
        refs.toField,
        h('div', { class: 'row-2' }, field('Date', refs.date), field('Who', refs.who)),
      ];
    },
    onSubmit(refs) {
      const amount = parseFloat(refs.amount.value);
      if (!amount || amount <= 0) throw new Error('Enter an amount');
      const data = {
        type, amount, note: refs.note.value.trim(), date: refs.date.value || todayISO(),
        accountId: refs.acct.value, who: refs.who.value || '',
        category: type === 'expense' ? refs.cat.value : (type === 'income' ? 'income' : 'other'),
        toAccountId: type === 'transfer' ? refs.toAcct.value : undefined,
      };
      update(s => {
        if (editing) Object.assign(s.transactions.find(x => x.id === tx.id), data, { toAccountId: data.toAccountId });
        else s.transactions.unshift({ id: uid('tx'), ...data });
      });
      closeModal();
      toast(editing ? 'Saved' : 'Added');
    },
  });
}

function monthNav(mk, onChange) {
  const shift = (n) => {
    const [y, m] = mk.split('-').map(Number);
    const d = new Date(y, m - 1 + n, 1);
    onChange(monthKey(d));
  };
  return h('div', { class: 'flex between', style: { marginBottom: '2px' } },
    h('button', { class: 'icon-btn', onClick: () => shift(-1) }, '‹'),
    h('div', { style: { fontWeight: 700, fontSize: '15px' } }, fmtMonth(mk)),
    h('button', { class: 'icon-btn', onClick: () => shift(1) }, '›'),
  );
}

// ============================================================
// BUDGETS
// ============================================================
export function renderBudgets() {
  registerFab('/budgets', () => budgetModal());
  const wrap = h('div');
  wrap.append(pageHeader('Budgets', 'Monthly targets by category',
    h('button', { class: 'btn primary hide-mobile', onClick: () => budgetModal() }, 'Set budgets')));
  wrap.append(subTabs('money'));

  const spentMap = spentByCategory();
  const budgets = Object.entries(state.budgets).filter(([, v]) => v > 0);
  const totalBudget = sum(budgets, ([, v]) => v);
  const totalSpent = sum(budgets, ([c]) => spentMap[c] || 0);

  wrap.append(h('div', { class: 'card pad', style: { marginBottom: '16px' } },
    h('div', { class: 'flex between', style: { marginBottom: '10px' } },
      h('div', { class: 't' }, `${fmtMonth(monthKey())}`),
      h('div', { class: 'amt' }, `${money(totalSpent, { cents: false })} / ${money(totalBudget, { cents: false })}`)),
    progress(totalBudget ? (totalSpent / totalBudget) * 100 : 0, totalSpent > totalBudget ? 'var(--red)' : 'var(--green)'),
    h('div', { class: 'hint', style: { marginTop: '8px' } }, totalBudget ? `${money(Math.max(0, totalBudget - totalSpent), { cents: false })} left to spend` : 'No budgets set yet'),
  ));

  if (!budgets.length) {
    wrap.append(h('div', { class: 'card' }, h('div', { class: 'list-empty' },
      h('span', { class: 'em' }, '📊'),
      h('div', { style: { fontWeight: 650 } }, 'Set your first budget'),
      h('div', { style: { fontSize: '13px', marginTop: '4px' } }, 'Pick monthly spending targets for the categories that matter.'),
      h('button', { class: 'btn primary', style: { marginTop: '14px' }, onClick: () => budgetModal() }, 'Set budgets'))));
    return wrap;
  }

  const card = h('div', { class: 'card' });
  for (const [cat, amt] of sortBy(budgets, ([c]) => -((spentMap[c]||0)/state.budgets[c]))) {
    const c = catById(cat); const spent = spentMap[cat] || 0; const pct = (spent / amt) * 100;
    const left = amt - spent;
    card.append(h('div', { class: 'row pointer', style: { flexDirection: 'column', alignItems: 'stretch', gap: '8px' }, onClick: () => budgetModal(cat) },
      h('div', { class: 'flex between' },
        h('div', { class: 'flex gap-8' }, h('span', { style: { fontSize: '18px' } }, c.icon), h('span', { class: 't' }, c.name)),
        h('div', { class: 's tabnum', style: pct > 100 ? { color: 'var(--red)', fontWeight: 700 } : {} }, `${money(spent, { cents: false })} / ${money(amt, { cents: false })}`)),
      progress(pct, pct > 100 ? 'var(--red)' : pct > 85 ? 'var(--gold)' : c.color),
      h('div', { class: 'hint', style: { margin: 0 } }, left >= 0 ? `${money(left, { cents: false })} left` : `${money(-left, { cents: false })} over budget`),
    ));
  }
  wrap.append(card);
  return wrap;
}

function budgetModal(focusCat = null) {
  const refs = {};
  const body = h('div');
  body.append(h('p', { class: 'hint', style: { marginTop: 0, marginBottom: '14px' } }, 'Set a monthly amount for any category. Leave blank to skip.'));
  for (const c of CATEGORIES.filter(c => !['income'].includes(c.id))) {
    const inp = input({ type: 'number', step: '1', inputmode: 'decimal', placeholder: '—', value: state.budgets[c.id] || '', style: { textAlign: 'right' } });
    refs[c.id] = inp;
    body.append(h('div', { class: 'flex gap-12', style: { padding: '7px 0', borderBottom: '1px solid var(--border)' } },
      h('span', { style: { fontSize: '17px', width: '26px' } }, c.icon),
      h('div', { class: 't grow' }, c.name),
      h('div', { style: { width: '110px' } }, inp)));
  }
  modal({
    title: 'Monthly budgets',
    body,
    footer: [
      h('button', { class: 'btn ghost', onClick: closeModal }, 'Cancel'),
      h('button', { class: 'btn primary', onClick: () => {
        update(s => { for (const c of CATEGORIES) { const v = parseFloat(refs[c.id]?.value); if (v > 0) s.budgets[c.id] = v; else delete s.budgets[c.id]; } });
        closeModal(); toast('Budgets saved');
      } }, 'Save budgets'),
    ],
  });
  if (focusCat && refs[focusCat]) setTimeout(() => refs[focusCat].focus(), 60);
}

// ============================================================
// BILLS & SUBSCRIPTIONS
// ============================================================
export function renderBills() {
  registerFab('/bills', () => billModal());
  const wrap = h('div');
  wrap.append(pageHeader('Bills & Subscriptions', 'Never miss a due date',
    h('button', { class: 'btn primary hide-mobile', onClick: () => billModal() }, '+ Bill')));
  wrap.append(subTabs('money'));

  const monthlyTotal = sum(state.bills, b => b.cadence === 'monthly' ? b.amount : b.cadence === 'weekly' ? b.amount * 4.33 : b.cadence === 'yearly' ? b.amount / 12 : 0);
  wrap.append(h('div', { class: 'grid cols-2 keep', style: { marginBottom: '18px' } },
    bigStat('Monthly total', money(monthlyTotal), `${state.bills.length} bills`, 'var(--accent)'),
    bigStat('Due in 7 days', money(sum(state.bills.filter(b => daysUntil(billNextDue(b)) <= 7), b => b.amount)), 'coming up', 'var(--gold)'),
  ));

  if (!state.bills.length) {
    wrap.append(h('div', { class: 'card' }, h('div', { class: 'list-empty' },
      h('span', { class: 'em' }, '📅'),
      h('div', { style: { fontWeight: 650 } }, 'Add your bills & subscriptions'),
      h('div', { style: { fontSize: '13px', marginTop: '4px' } }, 'Rent, utilities, streaming — track amounts and due dates.'),
      h('button', { class: 'btn primary', style: { marginTop: '14px' }, onClick: () => billModal() }, '+ Add a bill'))));
    return wrap;
  }

  const withDue = sortBy(state.bills.map(b => ({ b, due: billNextDue(b), d: daysUntil(billNextDue(b)) })), x => x.d);
  const card = h('div', { class: 'card' });
  for (const { b, due, d } of withDue) {
    const c = catById(b.category);
    const soon = d <= 3;
    card.append(h('div', { class: 'row pointer', onClick: () => billModal(b) },
      h('div', { class: 'lead', style: { background: c.color + '22', color: c.color } }, c.icon),
      h('div', { class: 'grow' },
        h('div', { class: 't' }, b.name),
        h('div', { class: 's flex gap-6', style: soon ? { color: 'var(--accent-ink)', fontWeight: 600 } : {} },
          h('span', {}, cadenceLabel(b) + ' · ' + relDay(due)),
          b.autopay ? h('span', { class: 'badge green', style: { fontSize: '10px' } }, 'auto') : null)),
      h('div', { class: 'amt' }, money(b.amount)),
    ));
  }
  wrap.append(card);
  return wrap;
}

function cadenceLabel(b) {
  return { monthly: 'Monthly', weekly: 'Weekly', yearly: 'Yearly', once: 'One-time' }[b.cadence] || 'Monthly';
}

function billModal(bill = null) {
  const editing = !!bill;
  let cadence = bill?.cadence || 'monthly';
  formModal({
    title: editing ? 'Edit bill' : 'Add bill',
    submitLabel: editing ? 'Save' : 'Add bill',
    extraFoot: editing ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.bills = s.bills.filter(x => x.id !== bill.id)); closeModal(); toast('Deleted'); } }, 'Delete') : null,
    build(refs) {
      refs.name = input({ placeholder: 'e.g. Electric bill', value: bill?.name || '' });
      refs.amount = input({ type: 'number', step: '0.01', inputmode: 'decimal', placeholder: '0.00', value: bill?.amount || '' });
      refs.cat = select(catOpts(), bill?.category || 'utilities');
      refs.cadence = segmented([{ value: 'monthly', label: 'Monthly' }, { value: 'weekly', label: 'Weekly' }, { value: 'yearly', label: 'Yearly' }, { value: 'once', label: 'Once' }], cadence, (v) => {
        cadence = v; refs.dayField.style.display = v === 'weekly' || v === 'once' ? 'none' : '';
        refs.dowField.style.display = v === 'weekly' ? '' : 'none';
        refs.dateField.style.display = v === 'once' ? '' : 'none';
      });
      refs.day = input({ type: 'number', min: '1', max: '28', placeholder: '1', value: bill?.dueDay || '1' });
      refs.dow = select(['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map((d, i) => ({ value: i, label: d })), bill?.dueDow ?? 1);
      refs.date = input({ type: 'date', value: bill?.dueDate || todayISO() });
      refs.autopay = h('input', { type: 'checkbox', checked: bill?.autopay || false });
      refs.dayField = field('Day of month (1–28)', refs.day);
      refs.dowField = field('Day of week', refs.dow);
      refs.dateField = field('Due date', refs.date);
      refs.dayField.style.display = cadence === 'weekly' || cadence === 'once' ? 'none' : '';
      refs.dowField.style.display = cadence === 'weekly' ? '' : 'none';
      refs.dateField.style.display = cadence === 'once' ? '' : 'none';
      return [
        field('Name', refs.name),
        h('div', { class: 'row-2' }, field('Amount', refs.amount), field('Category', refs.cat)),
        field('How often', refs.cadence),
        refs.dayField, refs.dowField, refs.dateField,
        h('label', { class: 'flex gap-8', style: { fontSize: '14px', fontWeight: '600', cursor: 'pointer', marginTop: '4px' } }, refs.autopay, 'Set up on auto-pay'),
      ];
    },
    onSubmit(refs) {
      const name = refs.name.value.trim();
      if (!name) throw new Error('Give the bill a name');
      const data = {
        name, amount: parseFloat(refs.amount.value) || 0, category: refs.cat.value, cadence,
        dueDay: parseInt(refs.day.value) || 1, dueDow: parseInt(refs.dow.value), dueDate: refs.date.value,
        autopay: refs.autopay.checked,
      };
      update(s => { if (editing) Object.assign(s.bills.find(x => x.id === bill.id), data); else s.bills.push({ id: uid('bill'), ...data }); });
      closeModal(); toast(editing ? 'Saved' : 'Added');
    },
  });
}
