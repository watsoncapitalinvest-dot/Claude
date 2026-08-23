/**
 * SCFL Jeopardy — league log endpoint.
 *
 * A Google Apps Script web app bound to a spreadsheet. The game POSTs one
 * finished game to it; the sheet is the league's record book. A GET hands
 * the whole log back so every copy of the game can show the league table.
 *
 * Setup lives in LEAGUE-SETUP.md next to this file.
 */

/* Set a word here and put the same word in the game's Connect box. Anyone
   with the URL can read; only someone with the word can write. Leave it
   empty and writes are open to anyone holding the URL. */
const WRITE_KEY = '';

const SHEET_NAME = 'games';

/* Must stay in step with CSV_COLS in the game. */
const COLS = ['date','time','club','owner','round1','round2','final_wager',
  'final_result','total','right','asked','accuracy','seconds',
  'r1_right','r1_asked','r2_right','r2_asked','best_category','worst_category',
  'categories','id','received'];

function sheet_(){
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh){
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(COLS);
    sh.setFrozenRows(1);
  }
  if (sh.getLastRow() === 0) sh.appendRow(COLS);
  return sh;
}

function json_(obj){
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/* ---- write: one finished game ---------------------------------------- */
function doPost(e){
  try {
    const body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (WRITE_KEY && body.key !== WRITE_KEY) return json_({ ok: false, error: 'bad key' });

    const games = Array.isArray(body.games) ? body.games : (body.game ? [body.game] : []);
    if (!games.length) return json_({ ok: false, error: 'no games' });

    const lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      const sh = sheet_();
      const idCol = COLS.indexOf('id') + 1;
      const last = sh.getLastRow();
      const have = {};
      if (last > 1){
        sh.getRange(2, idCol, last - 1, 1).getValues()
          .forEach(function(r){ if (r[0]) have[String(r[0])] = 1; });
      }
      const rows = [], stamp = new Date();
      games.forEach(function(g){
        const id = String(g.id || '');
        if (!id || have[id]) return;
        have[id] = 1;
        rows.push(COLS.map(function(c){ return c === 'received' ? stamp : (g[c] === undefined ? '' : g[c]); }));
      });
      if (rows.length) sh.getRange(sh.getLastRow() + 1, 1, rows.length, COLS.length).setValues(rows);
      return json_({ ok: true, added: rows.length, skipped: games.length - rows.length });
    } finally { lock.releaseLock(); }
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

/* ---- read: the whole log --------------------------------------------- */
function doGet(e){
  try {
    const sh = sheet_();
    const last = sh.getLastRow();
    if (last < 2) return json_({ ok: true, games: [] });
    const values = sh.getRange(1, 1, last, COLS.length).getValues();
    const head = values[0].map(String);
    const out = values.slice(1).map(function(r){
      const o = {};
      head.forEach(function(h, i){ o[h] = r[i] instanceof Date ? r[i].toISOString() : r[i]; });
      return o;
    }).filter(function(o){ return o.id; });
    const since = e && e.parameter && e.parameter.since;
    return json_({ ok: true, games: since ? out.filter(function(o){ return String(o.id) > String(since); }) : out });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}
