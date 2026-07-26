// views/settings.js — profile, people, security, backup/restore
import { h, todayISO } from '../utils.js';
import { state, update, commit, exportData, importData, wipe, loadSample } from '../store.js';
import { pageHeader } from '../nav.js';
import { formModal, field, input, select, closeModal, confirmDialog, toast, modal } from '../ui.js';

export function renderSettings() {
  const wrap = h('div');
  wrap.append(pageHeader('Settings', state.profile.home));

  // ---- Home & people ----
  wrap.append(sectionCard('🏠 Home', [
    settingRow('Home name', state.profile.home, () => editHome()),
    settingRow('Currency', state.profile.currency, () => editCurrency()),
  ]));

  const peopleCard = h('div', { class: 'card', style: { marginBottom: '18px' } });
  peopleCard.append(cardHead('👥 The two of you'));
  state.profile.people.forEach((p, i) => peopleCard.append(h('div', { class: 'row' },
    h('div', { class: 'lead', style: { background: p.color, color: '#fff', fontWeight: 800 } }, (p.name[0] || '•').toUpperCase()),
    h('div', { class: 'grow t' }, p.name),
    h('button', { class: 'btn ghost sm', onClick: () => editPerson(i) }, 'Edit'),
  )));
  if (state.profile.people.length < 6) peopleCard.append(h('div', { class: 'row' }, h('button', { class: 'btn ghost sm', onClick: () => editPerson(-1) }, '+ Add a person')));
  wrap.append(peopleCard);

  // ---- Appearance ----
  wrap.append(sectionCard('🎨 Appearance', [
    settingRow('Theme', { auto: 'Automatic', light: 'Light', dark: 'Dark' }[state.profile.theme || 'auto'], () => editTheme()),
  ]));

  // ---- Security ----
  wrap.append(sectionCard('🔒 Privacy & security', [
    settingRow('App lock (PIN)', state.profile.pin ? 'On' : 'Off', () => editPin()),
  ], 'Your data is stored only on this device. A PIN adds a lock screen when the app opens.'));

  // ---- Backup / restore ----
  const backupCard = h('div', { class: 'card', style: { marginBottom: '18px' } });
  backupCard.append(cardHead('💾 Backup & share'));
  backupCard.append(h('div', { style: { padding: '16px' } },
    h('p', { class: 'muted', style: { fontSize: '13.5px', marginBottom: '14px' } },
      'Everything lives on this device. Export a backup file to keep it safe or to share your data with your partner’s phone — they just import it.'),
    h('div', { class: 'grid cols-2 keep', style: { gap: '10px' } },
      h('button', { class: 'btn primary', onClick: doExport }, '⬇ Export backup'),
      h('button', { class: 'btn', onClick: doImport }, '⬆ Import backup'),
    ),
  ));
  wrap.append(backupCard);

  // ---- Data ----
  wrap.append(sectionCard('🗄️ Data', [
    !hasData() ? settingRow('Load sample data', 'Explore the app', () => { loadSample(); toast('Sample data loaded'); }) : null,
    settingRow('Reset everything', 'Delete all data', () => confirmDialog({ title: 'Erase all data?', message: 'This permanently deletes everything on this device and cannot be undone. Export a backup first if you want to keep it.', confirm: 'Erase everything', onConfirm: () => { wipe(); toast('All data erased'); location.hash = '/dashboard'; } }), true),
  ].filter(Boolean)));

  wrap.append(h('p', { class: 'dim', style: { fontSize: '12px', textAlign: 'center', margin: '20px 0' } },
    'Hearth · a private home base · v1.0'));
  return wrap;
}

function hasData() {
  return state.accounts.length || state.transactions.length || state.tasks.length || state.bills.length || state.goals.length || state.notes.length || state.lists.length;
}

function sectionCard(title, rows, footNote) {
  const card = h('div', { class: 'card', style: { marginBottom: '18px' } });
  card.append(cardHead(title));
  rows.forEach(r => card.append(r));
  if (footNote) card.append(h('div', { style: { padding: '4px 16px 14px' } }, h('p', { class: 'dim', style: { fontSize: '12.5px' } }, footNote)));
  return card;
}
function cardHead(title) { return h('div', { class: 'row', style: { background: 'var(--surface-2)', fontWeight: 700, fontSize: '13px' } }, title); }
function settingRow(label, value, onClick, danger) {
  return h('div', { class: 'row pointer', onClick },
    h('div', { class: 'grow t', style: danger ? { color: 'var(--red)' } : {} }, label),
    h('div', { class: 's dim' }, value),
    h('div', { class: 'dim', style: { fontSize: '18px' } }, '›'),
  );
}

// ---- editors ----
function editHome() {
  formModal({ title: 'Home name', submitLabel: 'Save', build(refs) { refs.v = input({ value: state.profile.home }); return [field('What do you call home?', refs.v)]; },
    onSubmit(refs) { update(s => s.profile.home = refs.v.value.trim() || 'Our Home'); closeModal(); } });
}
function editCurrency() {
  formModal({ title: 'Currency', submitLabel: 'Save', build(refs) { refs.v = select(['USD','EUR','GBP','CAD','AUD','INR','MXN','JPY'].map(c => ({ value: c, label: c })), state.profile.currency); return [field('Currency', refs.v)]; },
    onSubmit(refs) { update(s => s.profile.currency = refs.v.value); closeModal(); } });
}
function editPerson(idx) {
  const editing = idx >= 0;
  const p = editing ? state.profile.people[idx] : { name: '', color: '#c8632b' };
  formModal({
    title: editing ? 'Edit person' : 'Add person',
    submitLabel: 'Save',
    extraFoot: editing && state.profile.people.length > 1 ? h('button', { type: 'button', class: 'btn danger', onClick: () => { update(s => s.profile.people.splice(idx, 1)); closeModal(); } }, 'Remove') : null,
    build(refs) { refs.name = input({ value: p.name, placeholder: 'Name' }); refs.color = input({ type: 'color', value: p.color, style: { height: '44px', padding: '4px' } }); return [field('Name', refs.name), field('Color', refs.color)]; },
    onSubmit(refs) {
      const name = refs.name.value.trim(); if (!name) throw new Error('Enter a name');
      update(s => { if (editing) Object.assign(s.profile.people[idx], { name, color: refs.color.value }); else s.profile.people.push({ id: 'p' + Date.now().toString(36), name, color: refs.color.value }); });
      closeModal();
    },
  });
}
function editTheme() {
  formModal({ title: 'Theme', submitLabel: 'Save', build(refs) { refs.v = select([{ value: 'auto', label: 'Automatic (match device)' }, { value: 'light', label: 'Light' }, { value: 'dark', label: 'Dark' }], state.profile.theme || 'auto'); return [field('Appearance', refs.v)]; },
    onSubmit(refs) { update(s => s.profile.theme = refs.v.value); closeModal(); } });
}
function editPin() {
  if (state.profile.pin) {
    confirmDialog({ title: 'Turn off app lock?', message: 'Remove the PIN lock screen?', confirm: 'Turn off', danger: true, onConfirm: () => { update(s => s.profile.pin = null); toast('App lock off'); } });
    return;
  }
  formModal({
    title: 'Set a 4-digit PIN',
    submitLabel: 'Turn on',
    build(refs) {
      refs.pin = input({ type: 'tel', inputmode: 'numeric', maxLength: 4, placeholder: '••••', style: { textAlign: 'center', fontSize: '26px', letterSpacing: '10px' } });
      return [h('p', { class: 'hint', style: { marginTop: 0 } }, 'You’ll enter this each time the app opens on this device.'), field('PIN', refs.pin)];
    },
    onSubmit(refs) { const pin = refs.pin.value.replace(/\D/g, ''); if (pin.length !== 4) throw new Error('Enter 4 digits'); update(s => s.profile.pin = pin); closeModal(); toast('App lock on'); },
  });
}

// ---- backup / restore ----
function doExport() {
  const data = exportData();
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `hearth-backup-${todayISO()}.json`;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast('Backup downloaded');
}
function doImport() {
  const inp = document.createElement('input');
  inp.type = 'file'; inp.accept = 'application/json,.json';
  inp.onchange = () => {
    const file = inp.files[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const json = reader.result;
      modal({
        title: 'Import backup',
        body: h('div', {}, h('p', { class: 'muted', style: { fontSize: '14px' } }, 'How should we bring in this backup?')),
        footer: [
          h('button', { class: 'btn', onClick: () => { try { importData(json, { merge: true }); closeModal(); toast('Merged in'); location.hash = '/dashboard'; } catch (e) { toast(e.message); } } }, 'Merge with mine'),
          h('button', { class: 'btn primary', onClick: () => { confirmDialog({ title: 'Replace all data?', message: 'This overwrites everything on this device with the backup.', confirm: 'Replace', onConfirm: () => { try { importData(json, { merge: false }); toast('Restored'); location.hash = '/dashboard'; } catch (e) { toast(e.message); } } }); } }, 'Replace everything'),
        ],
      });
    };
    reader.readAsText(file);
  };
  inp.click();
}
