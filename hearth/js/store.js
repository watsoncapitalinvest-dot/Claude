// store.js — single source of truth: state, persistence, migrations, computed helpers
import { uid, todayISO, monthKey, iso, parseISO, today, sum } from './utils.js';

const KEY = 'hearth.v1';
const VERSION = 1;

// ---- default categories (spending) ----
export const CATEGORIES = [
  { id: 'groceries',   name: 'Groceries',      icon: '🛒', color: '#3f8a5c' },
  { id: 'dining',      name: 'Dining Out',     icon: '🍽️', color: '#c8632b' },
  { id: 'housing',     name: 'Housing / Rent', icon: '🏠', color: '#3f6fa8' },
  { id: 'utilities',   name: 'Utilities',      icon: '💡', color: '#c79a2e' },
  { id: 'transport',   name: 'Transport',      icon: '🚗', color: '#7a5aa6' },
  { id: 'health',      name: 'Health',         icon: '❤️', color: '#c0433a' },
  { id: 'kids',        name: 'Kids',           icon: '🧸', color: '#d98cae' },
  { id: 'shopping',    name: 'Shopping',       icon: '🛍️', color: '#5a8a8f' },
  { id: 'fun',         name: 'Entertainment',  icon: '🎬', color: '#b5622e' },
  { id: 'travel',      name: 'Travel',         icon: '✈️', color: '#2f8fb0' },
  { id: 'subs',        name: 'Subscriptions',  icon: '📺', color: '#8a6d3b' },
  { id: 'income',      name: 'Income',         icon: '💰', color: '#3f8a5c' },
  { id: 'savings',     name: 'Savings',        icon: '🐷', color: '#c79a2e' },
  { id: 'other',       name: 'Other',          icon: '•',  color: '#9a8f82' },
];
export const catById = (id) => CATEGORIES.find(c => c.id === id) || CATEGORIES.at(-1);

export const ACCOUNT_TYPES = [
  { id: 'checking',   name: 'Checking',   icon: '🏦' },
  { id: 'savings',    name: 'Savings',    icon: '🐷' },
  { id: 'credit',     name: 'Credit Card',icon: '💳' },
  { id: 'cash',       name: 'Cash',       icon: '💵' },
  { id: 'investment', name: 'Investment', icon: '📈' },
  { id: 'loan',       name: 'Loan / Debt',icon: '📉' },
  { id: 'other',      name: 'Other',      icon: '📁' },
];
export const acctType = (id) => ACCOUNT_TYPES.find(a => a.id === id) || ACCOUNT_TYPES.at(-1);
// credit / loan are liabilities (their balance is money owed)
export const isLiability = (t) => t === 'credit' || t === 'loan';

function defaultState() {
  return {
    version: VERSION,
    createdAt: Date.now(),
    profile: {
      home: 'Our Home',
      currency: 'USD',
      people: [
        { id: 'p1', name: 'Me',   color: '#c8632b' },
        { id: 'p2', name: 'Us',   color: '#3f6fa8' },
      ],
      pin: null,          // 4-digit string or null
      theme: 'auto',      // auto | light | dark
      onboarded: false,
    },
    accounts: [],
    transactions: [],
    budgets: {},          // { 'catId': monthlyAmount }
    bills: [],
    tasks: [],
    events: [],
    lists: [],            // shopping lists
    meals: {},            // { 'YYYY-MM-DD': {breakfast,lunch,dinner} }
    goals: [],
    notes: [],
    inventory: [],
  };
}

// ---------- persistence ----------
function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return defaultState();
    const data = JSON.parse(raw);
    return migrate(data);
  } catch (e) {
    console.error('Load failed, starting fresh', e);
    return defaultState();
  }
}
function migrate(data) {
  // future migrations keyed on data.version go here
  const base = defaultState();
  return { ...base, ...data, profile: { ...base.profile, ...(data.profile || {}) } };
}

let saveTimer = null;
export function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    try { localStorage.setItem(KEY, JSON.stringify(state)); }
    catch (e) { console.error('Save failed', e); }
  }, 120);
}

// ---------- reactive layer ----------
export let state = load();
const subs = new Set();
export function subscribe(fn) { subs.add(fn); return () => subs.delete(fn); }
export function commit() { save(); subs.forEach(fn => fn()); }

// generic mutate helper
export function update(fn) { fn(state); commit(); }

// ---------- people helpers ----------
export const people = () => state.profile.people;
export const personById = (id) => state.profile.people.find(p => p.id === id);

// ---------- computed: money ----------
export function accountBalance(acc) {
  // stored balance + all transactions touching it
  let bal = Number(acc.opening || 0);
  for (const t of state.transactions) {
    if (t.accountId === acc.id) {
      if (t.type === 'income') bal += t.amount;
      else if (t.type === 'expense') bal -= t.amount;
      else if (t.type === 'transfer') bal -= t.amount; // out of this account
    }
    if (t.toAccountId === acc.id && t.type === 'transfer') bal += t.amount; // into this account
  }
  return bal;
}
export function netWorth() {
  let assets = 0, debts = 0;
  for (const a of state.accounts) {
    const b = accountBalance(a);
    if (isLiability(a.type)) debts += b;      // amount owed
    else assets += b;
  }
  return { assets, debts, net: assets - debts };
}
export function txForMonth(mk = monthKey()) {
  return state.transactions.filter(t => monthKey(t.date) === mk);
}
export function spentByCategory(mk = monthKey()) {
  const out = {};
  for (const t of txForMonth(mk)) {
    if (t.type === 'expense') out[t.category] = (out[t.category] || 0) + t.amount;
  }
  return out;
}
export function monthIncome(mk = monthKey()) {
  return sum(txForMonth(mk).filter(t => t.type === 'income'), t => t.amount);
}
export function monthSpend(mk = monthKey()) {
  return sum(txForMonth(mk).filter(t => t.type === 'expense'), t => t.amount);
}

// ---------- bills ----------
export function billNextDue(bill) {
  // returns ISO date of the next occurrence >= today (or today)
  const t = today();
  if (bill.cadence === 'once') return bill.dueDate;
  let d;
  if (bill.cadence === 'weekly') {
    d = new Date(t);
    const target = bill.dueDow ?? 1;
    d.setDate(d.getDate() + ((target - d.getDay() + 7) % 7));
  } else if (bill.cadence === 'yearly') {
    const y = t.getFullYear();
    d = new Date(y, (bill.dueMonth ?? 1) - 1, bill.dueDay ?? 1);
    if (d < t) d = new Date(y + 1, (bill.dueMonth ?? 1) - 1, bill.dueDay ?? 1);
  } else { // monthly
    const day = Math.min(bill.dueDay ?? 1, 28);
    d = new Date(t.getFullYear(), t.getMonth(), day);
    if (d < t) d = new Date(t.getFullYear(), t.getMonth() + 1, day);
  }
  return iso(d);
}
export function billPaidThisCycle(bill) {
  if (!bill.lastPaid) return false;
  const next = billNextDue(bill);
  // if lastPaid is within this cycle window (after previous due), consider paid
  const paid = parseISO(bill.lastPaid);
  const nextD = parseISO(next);
  // paid counts if it's on/after the most recent past due date
  return paid >= new Date(nextD.getFullYear(), nextD.getMonth() - (bill.cadence==='monthly'?1:0), 1) && paid <= today();
}

// ---------- CRUD helpers (thin) ----------
export function addTx(tx) { update(s => s.transactions.unshift({ id: uid('tx'), date: todayISO(), ...tx })); }
export function removeTx(id) { update(s => s.transactions = s.transactions.filter(t => t.id !== id)); }

// ---------- export / import ----------
export function exportData() {
  return JSON.stringify({ app: 'hearth', version: VERSION, exportedAt: new Date().toISOString(), state }, null, 2);
}
export function importData(json, { merge = false } = {}) {
  const parsed = JSON.parse(json);
  const incoming = parsed.state || parsed;
  if (!incoming || typeof incoming !== 'object') throw new Error('Not a valid Hearth backup');
  if (merge) {
    // shallow merge arrays by id
    const merged = migrate(incoming);
    for (const key of ['accounts','transactions','bills','tasks','events','lists','goals','notes','inventory']) {
      const byId = new Map((state[key]||[]).map(x => [x.id, x]));
      for (const x of (merged[key]||[])) byId.set(x.id, x);
      state[key] = [...byId.values()];
    }
    Object.assign(state.budgets, merged.budgets || {});
    Object.assign(state.meals, merged.meals || {});
  } else {
    state = migrate(incoming);
  }
  window.Hearth.state = state;
  commit();
}
export function wipe() { state = defaultState(); window.Hearth.state = state; commit(); }

// expose for utils (currency) + debugging
window.Hearth = { get state() { return state; }, set state(v) { state = v; } };

// ---------- sample data (optional, from settings) ----------
export function loadSample() {
  const s = defaultState();
  const money = (n) => n;
  const A = (o) => ({ id: uid('acc'), opening: 0, ...o });
  const chk = A({ name: 'Everyday Checking', type: 'checking', opening: 4820.5, institution: 'Home Bank', color:'#3f6fa8' });
  const sav = A({ name: 'Emergency Fund', type: 'savings', opening: 11200, institution: 'Home Bank', color:'#3f8a5c' });
  const cc  = A({ name: 'Rewards Card', type: 'credit', opening: 940.25, institution: 'Card Co', color:'#c0433a' });
  const inv = A({ name: 'Retirement', type: 'investment', opening: 68400, institution: 'Broker', color:'#7a5aa6' });
  s.accounts = [chk, sav, cc, inv];
  s.profile.people = [{ id:'p1', name:'Alex', color:'#c8632b' }, { id:'p2', name:'Sam', color:'#3f6fa8' }];
  s.profile.home = 'The Riverside House';
  s.profile.onboarded = true;

  const d = (off) => iso(new Date(Date.now() + off*86400000));
  s.transactions = [
    { id: uid('tx'), accountId: chk.id, date: d(-1), amount: 82.4, type:'expense', category:'groceries', note:'Weekly shop', who:'p1' },
    { id: uid('tx'), accountId: cc.id,  date: d(-2), amount: 48.0, type:'expense', category:'dining', note:'Date night', who:'p2' },
    { id: uid('tx'), accountId: chk.id, date: d(-3), amount: 60.0, type:'expense', category:'utilities', note:'Electric', who:'p1' },
    { id: uid('tx'), accountId: chk.id, date: d(-5), amount: 3200, type:'income', category:'income', note:'Paycheck', who:'p1' },
    { id: uid('tx'), accountId: cc.id,  date: d(-6), amount: 15.99, type:'expense', category:'subs', note:'Streaming', who:'p2' },
    { id: uid('tx'), accountId: chk.id, date: d(-8), amount: 41.2, type:'expense', category:'transport', note:'Gas', who:'p1' },
  ];
  s.budgets = { groceries: 600, dining: 250, utilities: 300, transport: 200, fun: 150, shopping: 200 };
  s.bills = [
    { id: uid('bill'), name:'Rent', amount:1850, cadence:'monthly', dueDay:1, category:'housing', autopay:true },
    { id: uid('bill'), name:'Electric', amount:120, cadence:'monthly', dueDay:12, category:'utilities', autopay:false },
    { id: uid('bill'), name:'Internet', amount:70, cadence:'monthly', dueDay:18, category:'utilities', autopay:true },
    { id: uid('bill'), name:'Car Insurance', amount:140, cadence:'monthly', dueDay:22, category:'transport', autopay:true },
    { id: uid('bill'), name:'Streaming', amount:15.99, cadence:'monthly', dueDay:8, category:'subs', autopay:true },
  ];
  s.tasks = [
    { id: uid('t'), title:'Call plumber about kitchen sink', done:false, due:d(1), who:'p1', priority:'high' },
    { id: uid('t'), title:'Book dentist for the kids', done:false, due:d(3), who:'p2', priority:'normal' },
    { id: uid('t'), title:'Return library books', done:false, due:d(0), who:'p2', priority:'normal' },
    { id: uid('t'), title:'Take out recycling', done:true, due:d(-1), who:'p1', priority:'low' },
  ];
  s.events = [
    { id: uid('e'), title:"Sam's work dinner", date:d(2), time:'19:00', who:'p2' },
    { id: uid('e'), title:'Family movie night', date:d(4), time:'18:30', who:'p2' },
    { id: uid('e'), title:'Car service', date:d(9), time:'09:00', who:'p1' },
  ];
  s.lists = [
    { id: uid('l'), name:'Groceries', items:[
      { id:uid('i'), text:'Milk', done:false }, { id:uid('i'), text:'Eggs', done:false },
      { id:uid('i'), text:'Bread', done:true }, { id:uid('i'), text:'Coffee', done:false },
      { id:uid('i'), text:'Bananas', done:false },
    ]},
    { id: uid('l'), name:'Hardware store', items:[
      { id:uid('i'), text:'Light bulbs', done:false }, { id:uid('i'), text:'Batteries (AA)', done:false },
    ]},
  ];
  const wd = (off) => iso(new Date(Date.now() + off*86400000));
  s.meals = {
    [wd(0)]: { dinner:'Sheet-pan chicken & veg' },
    [wd(1)]: { dinner:'Pasta night' },
    [wd(2)]: { dinner:'Tacos' },
    [wd(3)]: { dinner:'Leftovers' },
  };
  s.goals = [
    { id: uid('g'), name:'Summer vacation', target:4000, saved:1450, targetDate:'2026-06-01', color:'#2f8fb0', note:'Beach trip' },
    { id: uid('g'), name:'New couch', target:1200, saved:800, color:'#c8632b' },
    { id: uid('g'), name:'Emergency fund (6 mo)', target:18000, saved:11200, color:'#3f8a5c' },
  ];
  s.notes = [
    { id: uid('n'), title:'Wifi & home info', body:'Wifi: OurHome_5G\nPassword: (ask Alex)\nThermostat: hold at 68°', updated:Date.now(), pinned:true },
    { id: uid('n'), title:'Gift ideas', body:"- Sam: pottery class\n- Mom: garden tools\n- Kids: bikes for spring", updated:Date.now()-86400000, pinned:false },
  ];
  s.inventory = [
    { id: uid('v'), name:'Paper towels', qty:6, location:'Pantry' },
    { id: uid('v'), name:'Dish soap', qty:1, location:'Under sink', note:'running low' },
    { id: uid('v'), name:'Furnace filter', qty:2, location:'Garage', note:'20x25x1' },
  ];
  state = s; window.Hearth.state = s; commit();
}
