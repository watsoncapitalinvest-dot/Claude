// views/onboarding.js — first-run setup
import { h } from '../utils.js';
import { state, commit, loadSample } from '../store.js';

export function renderOnboarding(done) {
  const app = document.getElementById('app');
  app.innerHTML = '';
  let step = 0;

  const homeInput = h('input', { class: 'input', placeholder: 'e.g. The Riverside House', value: state.profile.home === 'Our Home' ? '' : state.profile.home });
  const p1 = h('input', { class: 'input', placeholder: 'Your name', value: '' });
  const p2 = h('input', { class: 'input', placeholder: "Partner's name", value: '' });
  const curSel = h('select', { class: 'input' },
    ...['USD','EUR','GBP','CAD','AUD','INR','MXN','JPY'].map(c => h('option', { value: c }, c)));

  const wrap = h('div', { class: 'lock', style: { alignItems: 'flex-start', overflowY: 'auto' } });
  const card = h('div', { class: 'lock-card', style: { maxWidth: '400px', marginTop: '6vh', textAlign: 'left', width: '100%' } });

  function step0() {
    card.innerHTML = '';
    card.append(
      h('div', { class: 'brand-mark', style: { margin: '0 0 18px' } }, '🔥'),
      h('div', { style: { fontSize: '26px', fontWeight: '750', letterSpacing: '-.03em' } }, 'Welcome to Hearth'),
      h('p', { class: 'muted', style: { margin: '8px 0 22px', fontSize: '15px' } },
        'A private, shared home base for your family — money, plans, and everything you do together. Everything stays on your own device.'),
      h('div', { class: 'field' }, h('label', {}, 'What should we call your home?'), homeInput),
      h('div', { class: 'row-2' },
        h('div', { class: 'field' }, h('label', {}, 'You'), p1),
        h('div', { class: 'field' }, h('label', {}, 'Partner'), p2),
      ),
      h('div', { class: 'field' }, h('label', {}, 'Currency'), curSel),
      h('button', { class: 'btn primary block', style: { marginTop: '8px' }, onClick: () => { save(false); done(); } }, 'Start fresh →'),
      h('button', { class: 'btn ghost block', style: { marginTop: '10px' }, onClick: () => { save(false); loadSample(); done(); } }, 'Explore with sample data first'),
      h('p', { class: 'dim', style: { fontSize: '12px', textAlign: 'center', marginTop: '14px' } },
        'No account needed. Your data never leaves this device unless you export it.'),
    );
  }
  function save(sample) {
    state.profile.home = homeInput.value.trim() || 'Our Home';
    const people = [];
    if (p1.value.trim()) people.push({ id: 'p1', name: p1.value.trim(), color: '#c8632b' });
    if (p2.value.trim()) people.push({ id: 'p2', name: p2.value.trim(), color: '#3f6fa8' });
    if (people.length) state.profile.people = people;
    state.profile.currency = curSel.value;
    state.profile.onboarded = true;
    commit();
  }

  step0();
  wrap.append(card);
  app.append(wrap);
}
