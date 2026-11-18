// ===================================================================================================
// G.I. Joe: Cobra Economy Simulator — engine (STORY, 17 Nov 2026)
// Mode 1 is a faithful port of story_tools/act1_cobra_sim_v6.py (Act 1 as designed).
// Mode 2 is the parked supply-split design (claude/COBRA_SUPPLY_SPLIT_v1.md); its numbers are first guesses.
// ===================================================================================================
const SIM = (() => {

function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a;
  t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const median = v => { if (!v.length) return null; const s = [...v].sort((a, b) => a - b), n = s.length;
  return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };
const mean = v => v.length ? v.reduce((a, b) => a + b, 0) / v.length : 0;

// ---------------------------------------------------------------------------- MODE 1: ACT 1 ECONOMY
const TREE = [{"name":"RIFLES","dept":"ARMORY","cost":20,"mpp":2,"early":3,"late":8,"req":[]},{"name":"GRENADES","dept":"ARMORY","cost":20,"mpp":2,"early":3,"late":8,"req":["RIFLES"]},{"name":"LASERS","dept":"ARMORY","cost":40,"mpp":3,"early":8,"late":14,"req":["GRENADES"]},{"name":"BODY_ARMOR","dept":"ARMORY","cost":40,"mpp":2,"early":12,"late":20,"req":["LASERS"]},{"name":"STINGER","dept":"MOTOR_POOL","cost":30,"mpp":2,"early":3,"late":8,"req":[]},{"name":"HISS_TANK","dept":"MOTOR_POOL","cost":30,"mpp":3,"early":6,"late":12,"req":["STINGER"]},{"name":"HEAVY_WEAPONS","dept":"MOTOR_POOL","cost":40,"mpp":3,"early":9,"late":14,"req":["HISS_TANK"]},{"name":"MAGGOT","dept":"MOTOR_POOL","cost":40,"mpp":3,"early":12,"late":20,"req":["HEAVY_WEAPONS"]},{"name":"RATTLER","dept":"AIR_WING","cost":20,"mpp":3,"early":3,"late":8,"req":[]},{"name":"NIGHT_RAVEN","dept":"AIR_WING","cost":20,"mpp":3,"early":6,"late":12,"req":["RATTLER"]},{"name":"AIR_SUPERIORITY","dept":"AIR_WING","cost":30,"mpp":3,"early":8,"late":12,"req":["NIGHT_RAVEN"]},{"name":"PATROL_BOATS","dept":"NAVY","cost":40,"mpp":2,"early":4,"late":12,"req":[]},{"name":"FLAGGED_SHIPS","dept":"NAVY","cost":40,"mpp":3,"early":8,"late":16,"req":["PATROL_BOATS"]},{"name":"OFFICER_CORPS","dept":"TROOPS","cost":30,"mpp":1,"early":3,"late":8,"req":[]},{"name":"VIPER_PROGRAM","dept":"TROOPS","cost":30,"mpp":2,"early":12,"late":20,"req":["OFFICER_CORPS"]},{"name":"MEDI_VIPER","dept":"BIOLOGY","cost":30,"mpp":1,"early":3,"late":8,"req":[]},{"name":"MEDICINE","dept":"BIOLOGY","cost":40,"mpp":2,"early":6,"late":14,"req":["MEDI_VIPER"]},{"name":"SPY_NETWORK","dept":"INTELLIGENCE","cost":40,"mpp":2,"early":4,"late":12,"req":[]},{"name":"JOE_GEAR_TEARDOWN","dept":"INTELLIGENCE","cost":40,"mpp":2,"early":6,"late":16,"req":["SPY_NETWORK"]},{"name":"BANK_JOBS","dept":"CRIME","cost":20,"mpp":1,"early":1,"late":6,"req":[]},{"name":"HACKING","dept":"CRIME","cost":20,"mpp":1,"early":6,"late":14,"req":["BANK_JOBS"]},{"name":"KIDNAPPING","dept":"CRIME","cost":30,"mpp":1,"early":6,"late":12,"req":["BANK_JOBS"]}];

const ACT1_STYLES = ['absent', 'cautious', 'typical', 'aggressive'];
const ACT1_DEFAULTS = {
  runs: 500, months: 18, seed: 1,
  dromeCost: 1550, donorStep: 200, dromeFrom: 8, startBuildingAt: 0.5, minBuildMonths: 2,
  leakPct: 25, startFunds: 400, startMateriel: 150, startFronts: 3, startDepots: 2, startCells: 2, hiddenFindMult: 0.5,
  offmapBenches: 3, crimeOdds: 0.25, crimePays: 150, terrorFirstMonth: 4, terrorPreDrome: 0.15, cellStrikeFrom: 2,
  cellStrikeOdds: 0.20, cellGoal: 300, defenceCost: 150, terrorPerDrome: 0.9, transferFrom: 2, transferTargetSites: 4,
  transferPerMissing: 150, bNeedsMonths: 2, pushPastLatest: 2.0, wellSupplied: 50, buildStart: 2,
  front: {cost: 300, funds: 120, uf: 8,  mat: 0,  um: 0,  mc: 0,  benches: 0, odds: 66, loot: 60},
  factory: {cost: 680, funds: 0, uf: 28, mat: 80, um: 0, mc: 48, benches: 0, odds: 44, loot: 0},
  camp: {cost: 400, funds: 0, uf: 12, mat: 0, um: 20, mc: 0, benches: 0, odds: 26, loot: 0},
  depot: {cost: 160, funds: 0, uf: 5, mat: 0, um: 0, mc: 0, benches: 0, odds: 26, loot: 0},
  lab: {cost: 300, funds: 0, uf: 10, mat: 0, um: 10, mc: 0, benches: 1, odds: 45, loot: 0},
  broadcast: {cost: 200, funds: 0, uf: 6, mat: 0, um: 0, mc: 0, benches: 0, odds: 18, loot: 0},
  drome: {funds: 0, uf: 58, mat: 0, um: 30, mc: 0, benches: 4, odds: 0, loot: 200},
  styles: {
    absent:     {find: 0.0,  raids: 0.0, factory: 0.0, intercept: 0.0,  respond: 0.0, assault: 0.0, spine: null, spend: 15},
    cautious:   {find: 0.25, raids: 0.5, factory: 0.3, intercept: 0.05, respond: 0.3, assault: 0.5, spine: 12,   spend: 40},
    typical:    {find: 0.40, raids: 1.0, factory: 0.6, intercept: 0.15, respond: 0.5, assault: 0.8, spine: 10.5, spend: 70},
    aggressive: {find: 0.55, raids: 2.0, factory: 0.9, intercept: 0.30, respond: 0.7, assault: 1.0, spine: 9.5,  spend: 120},
  },
};

const NAMES = {FRONT: 'front company', FACTORY: 'factory', CAMP: 'training camp', DEPOT: 'depot', LAB: 'lab', BROADCAST: 'broadcast station', CELL: 'cell', DROME: 'Terror Drome', DROME_BUILDING: 'Drome under construction'};
const NM = t => NAMES[t] || t.toLowerCase();
function act1Run(P, style, R, rec) {
  const SITES = {FRONT: P.front, FACTORY: P.factory, CAMP: P.camp, DEPOT: P.depot, LAB: P.lab, BROADCAST: P.broadcast,
                 DROME: Object.assign({cost: P.dromeCost}, P.drome)};
  const isSite = t => t in SITES;
  const st = P.styles[style];
  const startTypes = [...Array(P.startFronts).fill('FRONT'), ...Array(P.startDepots).fill('DEPOT'), ...Array(P.startCells).fill('CELL')];
  let nid = 0; const mk = (type, found, hidden) => ({id: nid++, type, found, hidden});
  const sites = startTypes.map(t => mk(t, false, true));
  const frames = [], E = []; const ev = (kind, text, extra) => { if (rec) E.push(Object.assign({kind, text}, extra || {})); };
  let funds = P.startFunds, mat = P.startMateriel;
  const done = {}, prog = {}; TREE.forEach(t => prog[t.name] = 0);
  const drome = {saved: 0, building: null, built: null};
  const L = {end: null, version: null, terror: 0, firstTerror: null, rifles: null, dry: 0, peak: 0, fronts: 0, crimePaid: 0,
             strikes: 0, cellFronts: 0, fortified: 0, dromeBuilt: null, dromeStarted: null, broken: 0, leaked: 0,
             track: {funds: [], mat: [], sites: []}};
  const frontCap = others => 2 + Math.floor(others / 3);
  const factoryLive = R() >= st.factory;
  const loc = st.spine;
  const spineM = loc == null ? null : loc + (R() * 3 - 1.5);
  const prio = ['DROME', 'DROME_BUILDING', 'FACTORY', 'FRONT', 'CELL', 'LAB', 'DEPOT', 'CAMP', 'BROADCAST'];
  for (let m = 0; m < P.months; m++) {
    E.length = 0;
    if (m === 2 && factoryLive) { const s0 = mk('FACTORY', true, false); sites.push(s0); ev('build', 'The abandoned factory reactivates (found)', {id: s0.id}); }
    let types = sites.map(s => s.type);
    let econ = types.filter(isSite);
    let inc = 0;
    for (const t of econ) if (SITES[t].funds && R() >= st.intercept) inc += SITES[t].funds;
    const leak = P.leakPct * st.spend / 100; inc += leak; L.leaked += leak;
    funds = Math.max(0, funds + inc - econ.reduce((a, t) => a + SITES[t].uf, 0));
    mat = Math.max(0, mat - econ.reduce((a, t) => a + SITES[t].um, 0));
    for (const t of econ) if (SITES[t].mat) { const pay = Math.min(funds, SITES[t].mc); funds -= pay; mat += Math.floor(SITES[t].mat * pay / SITES[t].mc); }
    const hasDrome = types.includes('DROME');
    if (m >= P.transferFrom) { const missing = Math.max(0, P.transferTargetSites - econ.length);
      if (missing) { if (R() >= st.intercept) { funds += P.transferPerMissing * missing; ev('transfer', `The network flies in ${P.transferPerMissing * missing} funds`); } else ev('intercept', 'A Cobra cash transfer is intercepted'); } }
    if (!hasDrome) {
      for (const ls of sites.filter(x => x.type === 'FRONT' || x.type === 'CELL')) {
        if (R() < P.crimeOdds) {
          if (R() < st.respond) { ev('crimeStopped', 'A Cobra robbery is stopped', {id: ls.id}); for (const s of sites) if ((s.type === 'FRONT' || s.type === 'CELL') && !s.found) { s.found = true; ev('found', `The robbery leads the Joes to a ${NM(s.type)}`, {id: s.id}); break; } }
          else { L.crimePaid++; ev('crime', 'A robbery gets away', {id: ls.id}); if (ls.type === 'CELL') ls.purse = (ls.purse || 0) + P.crimePays; else funds += P.crimePays; }
        }
      }
      for (const c of sites.filter(x => x.type === 'CELL' && (x.purse || 0) >= P.cellGoal)) {
        const ec = sites.filter(x => isSite(x.type)).map(x => x.type);
        const othersN = ec.filter(t => t !== 'FRONT').length;
        c.purse -= P.cellGoal;
        if (ec.filter(t => t === 'FRONT').length < frontCap(othersN)) { const s0 = mk('FRONT', false, false); sites.push(s0); L.cellFronts++; ev('build', 'A cell grows into a front company', {id: s0.id, from: c.id}); }
        else funds += P.cellGoal;
      }
      if (m >= P.cellStrikeFrom) { const nc = types.filter(t => t === 'CELL').length; for (let i = 0; i < nc; i++) if (R() < P.cellStrikeOdds) L.strikes++; }
      if (m >= P.terrorFirstMonth && R() < P.terrorPreDrome) { L.terror++; ev('terror', 'Cobra stages a terror attack'); if (L.firstTerror == null) L.firstTerror = m; }
    } else {
      let n = 0; const nd = types.filter(t => t === 'DROME').length; for (let i = 0; i < nd; i++) if (R() < P.terrorPerDrome) n++;
      if (n) { L.terror += n; ev('terror', `The Drome launches ${n > 1 ? n + ' terror attacks' : 'a terror attack'}`); if (L.firstTerror == null) L.firstTerror = m; }
    }
    let benches = P.offmapBenches + econ.reduce((a, t) => a + SITES[t].benches, 0);
    const busy = new Set();
    for (const t of TREE) {
      if (t.name in done || m < t.early || busy.has(t.dept) || benches <= 0) continue;
      if (t.req.some(r => !(r in done))) continue;
      busy.add(t.dept); benches--;
      let pts = 10 * (t.late != null && m >= t.late ? P.pushPastLatest : 1);
      if (t.mpp) { pts = Math.min(pts, Math.floor(mat / t.mpp)); mat -= Math.trunc(pts * t.mpp); }
      prog[t.name] += pts;
      if (prog[t.name] >= t.cost) done[t.name] = m;
    }
    const reserve = econ.reduce((a, t) => a + SITES[t].uf, 0);
    if (m >= P.dromeFrom && !hasDrome) {
      drome.saved += P.donorStep * (m - P.dromeFrom + 1);
      const spare = Math.max(0, funds - reserve); drome.saved += spare; funds -= spare;
      if (drome.building == null && drome.saved >= P.dromeCost * P.startBuildingAt) {
        drome.building = m; L.dromeStarted = m; const s0 = mk('DROME_BUILDING', false, false); sites.push(s0); ev('drome', 'Cobra starts building the Terror Drome', {id: s0.id}); }
      if (drome.building != null && drome.saved >= P.dromeCost && m - drome.building >= P.minBuildMonths) {
        for (const s of sites) if (s.type === 'DROME_BUILDING') s.type = 'DROME';
        drome.built = m; L.dromeBuilt = m; ev('drome', 'The Terror Drome is finished'); }
    }
    econ = sites.map(s => s.type).filter(isSite);
    if (m >= P.buildStart && !(m >= P.dromeFrom && !hasDrome)) {
      const planning = econ.includes('DROME');
      const netF = econ.reduce((a, t) => a + SITES[t].funds - SITES[t].uf, 0);
      const netM = econ.reduce((a, t) => a + SITES[t].mat - SITES[t].um, 0);
      const others = econ.filter(t => t !== 'FRONT').length;
      for (const [t, r] of Object.entries(SITES)) {
        if (t === 'DROME') continue;
        const have = econ.filter(x => x === t).length;
        const earner = r.funds > r.uf, maker = r.mat > r.um;
        let wanted;
        if (t === 'FRONT') wanted = have < frontCap(others);
        else if (!planning) wanted = have === 0;
        else if (netF <= 0) wanted = earner;
        else if (netM < 0 && maker) wanted = true;
        else wanted = have === 0;
        if (wanted && funds - reserve >= r.cost && R() * 100 < r.odds) { funds -= r.cost; const s0 = mk(t, false, false); sites.push(s0); econ.push(t); ev('build', `Cobra builds a ${NM(t)}`, {id: s0.id}); }
      }
    }
    for (const s of sites) {
      let p = st.find * (s.hidden ? P.hiddenFindMult : 1);
      if (s.type === 'DROME' || s.type === 'DROME_BUILDING') p = (loc != null && m >= spineM) ? 1 : 0;
      if (!s.found && R() < p) { s.found = true; ev('found', `The Joes find a ${NM(s.type)}`, {id: s.id}); }
    }
    for (const s of sites)
      if (s.found && !s.fort && isSite(s.type) && s.type !== 'DROME' && funds - reserve >= P.defenceCost) { funds -= P.defenceCost; s.fort = 2; L.fortified++; ev('fort', `Cobra digs in at a found ${NM(s.type)}`, {id: s.id}); }
    const n = Math.floor(st.raids) + (R() < st.raids % 1 ? 1 : 0);
    for (let i = 0; i < n; i++) {
      const found = sites.filter(s => s.found).sort((a, b) => prio.indexOf(a.type) - prio.indexOf(b.type));
      if (!found.length) break;
      const tgt = found[0];
      if (tgt.type === 'DROME' || tgt.type === 'DROME_BUILDING') {
        if (R() < st.assault) { ev('raid', 'The Joes assault the Drome', {id: tgt.id, win: true}); L.end = m; L.version = tgt.type === 'DROME' ? 'A: Drome assault (finished)' : 'A: Drome assault (unfinished)'; break; }
        ev('raid', 'The Joes are not ready to assault the Drome', {id: tgt.id}); continue;
      }
      if ((tgt.fort || 0) > 1) { tgt.fort--; ev('raid', `A raid breaks the defences of a ${NM(tgt.type)}`, {id: tgt.id}); continue; }
      sites.splice(sites.indexOf(tgt), 1); ev('destroy', `The Joes destroy a ${NM(tgt.type)}`, {id: tgt.id, type: tgt.type});
      if (isSite(tgt.type)) funds = Math.max(0, funds - SITES[tgt.type].loot);
      if (tgt.type === 'DEPOT') mat = 0;
    }
    L.track.funds.push(funds); L.track.mat.push(mat); L.track.sites.push(sites.length);
    const snap = () => { if (rec) frames.push({m, funds, mat, sites: sites.map(x => ({id: x.id, type: x.type, found: x.found, hidden: x.hidden, fort: x.fort || 0})), events: E.slice(), end: L.version}); };
    if (L.end != null) { snap(); }
    if (L.end != null) break;
    const e2 = sites.map(s => s.type);
    if (m >= P.dromeFrom && !['FRONT', 'FACTORY', 'DROME', 'DROME_BUILDING'].some(t => e2.includes(t))) {
      L.broken++; if (L.broken >= P.bNeedsMonths) { L.end = m; L.version = 'B: network broken'; ev('end', 'Cobra\'s network is broken'); snap(); break; }
    } else L.broken = 0;
    if (drome.built != null && m - drome.built >= 3) { L.end = m; L.version = 'Drome strike'; ev('end', 'The Drome strikes the nearest Joe base'); snap(); break; }
    snap();
    if (L.rifles == null && done.RIFLES != null && mat >= P.wellSupplied) L.rifles = m;
    if (mat < P.wellSupplied) L.dry++;
    L.peak = Math.max(L.peak, sites.length); L.fronts = Math.max(L.fronts, econ.filter(t => t === 'FRONT').length);
  }
  L.frames = frames; return L;
}

function act1(P) {
  const R = rng(P.seed), out = {};
  for (const style of ACT1_STYLES) {
    const Ls = []; for (let i = 0; i < P.runs; i++) Ls.push(act1Run(P, style, R));
    const med = k => { const v = Ls.map(l => l[k]).filter(x => x != null); return {med: median(v), pct: Math.floor(v.length * 100 / P.runs)}; };
    const vers = {}; for (const l of Ls) { const k = l.version || `not over by month ${P.months}`; vers[k] = (vers[k] || 0) + 1; }
    const endHist = Array(P.months).fill(0); for (const l of Ls) if (l.end != null) endHist[l.end]++;
    const trackMed = key => { const res = []; for (let m = 0; m < P.months; m++) { const v = Ls.filter(l => l.track[key].length > m).map(l => l.track[key][m]); res.push(v.length >= P.runs * 0.25 ? median(v) : null); } return res; };
    out[style] = {end: med('end'), versions: vers, endHist, firstTerror: med('firstTerror'), terror: median(Ls.map(l => l.terror)),
      crimePaid: median(Ls.map(l => l.crimePaid)), strikes: median(Ls.map(l => l.strikes)), dromeStarted: med('dromeStarted'),
      dromeBuilt: med('dromeBuilt'), rifles: med('rifles'), dry: median(Ls.map(l => l.dry)), peak: median(Ls.map(l => l.peak)),
      fronts: median(Ls.map(l => l.fronts)), leaked: mean(Ls.map(l => l.leaked)), cellFronts: mean(Ls.map(l => l.cellFronts)),
      fortified: mean(Ls.map(l => l.fortified)),
      track: {funds: trackMed('funds'), mat: trackMed('mat'), sites: trackMed('sites')}};
  }
  return out;
}

const ACT1_SCENARIOS = {
  'As designed (M.A.R.S. leak 25%)': {},
  'No M.A.R.S. leak': {leakPct: 0},
  'Heavy leak (50%)': {leakPct: 50},
  'Stingy backers (100 a month)': {donorStep: 100},
  'Generous backers (300 a month)': {donorStep: 300},
  'Expensive Drome (2,000)': {dromeCost: 2000},
  'Cheap Drome (1,100)': {dromeCost: 1100},
  'Early Drome planning (month 6)': {dromeFrom: 6},
  'No crime money': {crimeOdds: 0},
  'Rich start (funds 800, materiel 300)': {startFunds: 800, startMateriel: 300},
  'Lean start (1 front, 1 depot, 1 cell)': {startFronts: 1, startDepots: 1, startCells: 1},
  'No network transfers': {transferPerMissing: 0},
  'Cheap defences (75)': {defenceCost: 75},
};

// ---------------------------------------------------------------------------- MODE 2: SUPPLY SPLIT
const STOCKS = ['bullets', 'guns', 'missiles', 'vehicles', 'aircraft', 'cells'];
const SPLIT_STYLES = ['absent', 'cautious', 'typical', 'aggressive'];
const SPLIT_DEFAULTS = {
  runs: 300, months: 24, seed: 7, regions: 3, garrisons: 6, destroMonth: 11,
  startFunds: 300, regionIncome: 300, producerUpkeep: 6, rebuildMonths: 3, rebuildCost: 200,
  // manpower and quality (the Cobra thesis, John 17 Nov 20:33: more weapons than soldiers; more soldiers rather than better guns)
  manpowerPriority: 0.9, startMen: 8, garrisonCap: 16, campRecruits: 6, recruitCost: 8, fundsReserve: 40,
  menLostCobraBattle: 1, menLostJoeRaid: 3, tierCost: 150,
  tierCap: {0: 0, 3: 1, 8: 2, 14: 3, 22: 4, 30: 5},
  produce:  {bullets: 50,  guns: 24, missiles: 10, vehicles: 3,   aircraft: 3,   cells: 14},
  unitCost: {bullets: 0.4, guns: 1.0, missiles: 3, vehicles: 12, aircraft: 16, cells: 2},
  upkeep:   {bullets: 3,   guns: 0.6, missiles: 0.5, vehicles: 0.1, aircraft: 0.1, cells: 0.8},   // per garrison per month
  battleNeed: {bullets: 10, guns: 2,  missiles: 3,   vehicles: 1,   aircraft: 1,   cells: 4},     // what one battle draws
  battleWants: {bullets: 1, guns: 1,  missiles: 0.5, vehicles: 0.25, aircraft: 0.15, cells: 0.4},   // chance a battle calls for it
  startStock: {bullets: 120, guns: 100, missiles: 20, vehicles: 4, aircraft: 3, cells: 0},          // per region, at the hub
  floor: 1, shipFraction: 0.5, ticksPerMonth: 3, cobraMissions: 2,
  postureWeight: 1.2, attackPlanBonus: 1.0, underAttackBonus: 1.0,
  vanSpot: 0.03, emergencyThreshold: 2, emergencyLoadBattles: 4, pullbackEmptyStocks: 2, pullbackMonths: 2, quietFactor: 0.3,
  strategy: 'balanced',   // balanced | producers | missileWorks | hub | vans | strangle
  styles: {
    absent:     {raids: 0,   ambush: 0,   intercept: 0,    intelBoost: 1},
    cautious:   {raids: 0.7, ambush: 0.4, intercept: 0.1,  intelBoost: 1},
    typical:    {raids: 1.5, ambush: 0.6, intercept: 0.25, intelBoost: 1.5},
    aggressive: {raids: 3,   ambush: 0.8, intercept: 0.4,  intelBoost: 2},
  },
};

function splitRun(P, style, R, rec) {
  const st = P.styles[style], T = P.ticksPerMonth, NT = P.months * T;
  const regions = [];
  for (let r = 0; r < P.regions; r++) {
    const g = []; for (let i = 0; i < P.garrisons; i++) g.push({stock: Object.fromEntries(STOCKS.map(k => [k, 0])), attacked: 0, men: P.startMen});
    regions.push({hub: Object.assign({}, P.startStock), garrisons: g, funds: P.startFunds,
      producers: Object.fromEntries(STOCKS.map(k => [k, {down: 0}])), quiet: 0, starvedMonths: 0, cool: {}, plan: -1,
      emptyMonths: Object.fromEntries(STOCKS.map(k => [k, 0])), tier: 0, tierFund: 0});
  }
  const L = {battles: 0, battlesBy: Object.fromEntries(STOCKS.map(k => [k, 0])), short: Object.fromEntries(STOCKS.map(k => [k, 0])),
    onFloor: 0, vans: 0, vansSpotted: 0, vansHit: 0, emergSent: 0, emergHit: 0, quietMonths: 0, producerRaids: 0, hubRaids: 0,
    downMonths: 0, prodScale: 0, prodScaleN: 0, emptyGarrison: 0, recruited: 0, behind: 0, behindN: 0, armed: 0, armedN: 0,
    track: Object.assign(Object.fromEntries(STOCKS.map(k => [k, []])), {men: [], tier: [], cap: [], spare: []})};
  const capAt = m => { let c = 0; for (const [mm, v] of Object.entries(P.tierCap)) if (m >= +mm) c = Math.max(c, v); return c; };
  const total = (reg, k) => reg.hub[k] + reg.garrisons.reduce((a, g) => a + g.stock[k], 0);
  const intransit = [], frames = [];
  let E = [], VANS = [];
  const ev = (kind, text, extra) => { if (rec) E.push(Object.assign({kind, text}, extra || {})); };
  const battle = (reg, g, lost) => {
    if (g.men <= 0) { L.emptyGarrison++; return; }
    L.battles++; g.men = Math.max(0, g.men - lost);
    for (const k of STOCKS) {
      if (k === 'cells' && monthOf(curT) < P.destroMonth) continue;
      if (R() >= P.battleWants[k]) continue;
      L.battlesBy[k]++;
      const need = P.battleNeed[k];
      if (g.stock[k] >= need) g.stock[k] -= need;
      else if (k === 'bullets' || k === 'guns') { g.stock[k] = 0; L.onFloor++; }   // the floor: sidearms and a magazine
      else { L.short[k]++; g.stock[k] = 0; if (rec) g.shortNow = (g.shortNow || []).concat(k); }   // all or nothing
    }
  };
  const monthOf = t => Math.floor(t / T);
  let curT = 0;
  for (let t = 0; t < NT; t++) {
    curT = t; const m = monthOf(t), newMonth = t % T === 0;
    // deliveries in transit arrive
    for (let i = intransit.length - 1; i >= 0; i--) if (intransit[i].at <= t) { const d = intransit[i]; for (const k in d.load) d.to.hub[k] += d.load[k]; intransit.splice(i, 1); }
    for (const [ri, reg] of regions.entries()) {
      if (newMonth) {
        // income and production (funds only; cells only once Destro has joined)
        reg.funds += P.regionIncome * (reg.quiet > 0 ? 0.7 : 1);
        const running = [];
        for (const k of STOCKS) {
          const p = reg.producers[k];
          if (p.down > 0) { p.down--; L.downMonths++; if (p.down === 0) { if (reg.funds >= P.rebuildCost) reg.funds -= P.rebuildCost; else p.down = 1; } continue; }
          if (k === 'cells' && m < P.destroMonth) continue;
          running.push(k);
        }
        // every running line is paid together; if money is short, every line slows by the same share
        const bill = running.reduce((a, k) => a + P.producerUpkeep + P.produce[k] * P.unitCost[k], 0);
        const scale = bill > 0 ? Math.min(1, reg.funds / bill) : 0;
        for (const k of running) { reg.hub[k] += Math.floor(P.produce[k] * scale); }
        reg.funds -= bill * scale; L.prodScale += scale; L.prodScaleN++;
        reg.funds = Math.max(0, reg.funds);
        // what is left goes to men first and better guns second, by Cobra's priority (the thesis)
        const spare = Math.max(0, reg.funds - P.fundsReserve);
        let menBudget = spare * P.manpowerPriority; const qualBudget = spare - menBudget;
        const room = reg.garrisons.reduce((a, g) => a + Math.max(0, P.garrisonCap - g.men), 0);
        const recruits = Math.min(P.campRecruits, room, Math.floor(menBudget / P.recruitCost));
        for (let i = 0; i < recruits; i++) { const g = reg.garrisons.reduce((a, b) => b.men < a.men ? b : a); g.men++; }
        L.recruited += recruits; reg.funds -= recruits * P.recruitCost; menBudget -= recruits * P.recruitCost;
        const toQuality = qualBudget + (room === 0 ? menBudget : 0);   // men at full strength: the money goes to quality
        reg.tierFund += toQuality; reg.funds -= toQuality;
        if (reg.tier < capAt(m) && reg.tierFund >= P.tierCost * (reg.tier + 1)) {
          reg.tierFund -= P.tierCost * (reg.tier + 1); reg.tier++; ev('tier', `Region ${ri + 1}: Cobra issues better guns (tier ${reg.tier})`, {r: ri}); }
        // garrison upkeep
        for (const g of reg.garrisons) for (const k of STOCKS) g.stock[k] = Math.max(0, g.stock[k] - P.upkeep[k] * (k === 'cells' && m < P.destroMonth ? 0 : 1));
        reg.plan = R() < 0.5 ? Math.floor(R() * reg.garrisons.length) : -1;   // a site staging an attack this month
        for (const g of reg.garrisons) g.attacked = Math.max(0, g.attacked - 1);
      }
      // standing orders: the hub ships a share of its stock to every garrison, one van each
      const w = reg.garrisons.map((g, i) => P.postureWeight + (i === reg.plan ? P.attackPlanBonus : 0) + (g.attacked > 0 ? P.underAttackBonus : 0));
      const wsum = w.reduce((a, b) => a + b, 0);
      // whole units only: each stock's shipment is split by the shares, largest remainder first; the rest stays at the hub
      const loads = reg.garrisons.map(() => Object.fromEntries(STOCKS.map(k => [k, 0])));
      for (const k of STOCKS) {
        const amount = Math.floor(reg.hub[k] * P.shipFraction); if (amount <= 0) continue;
        const raw = w.map(x => amount * x / wsum), base = raw.map(Math.floor);
        let left = amount - base.reduce((a, b) => a + b, 0);
        const order = raw.map((x, i) => [x - base[i], i]).sort((a, b) => b[0] - a[0]);
        for (let j = 0; j < left; j++) base[order[j % order.length][1]]++;
        base.forEach((n, i) => loads[i][k] = n); reg.hub[k] -= amount;
      }
      for (const [gi, g] of reg.garrisons.entries()) {
        const load = loads[gi]; if (!STOCKS.some(k => load[k] > 0)) continue;
        L.vans++;
        const spotted = R() < P.vanSpot * st.intelBoost;
        if (rec) VANS.push({r: ri, g: gi, load, hit: false});
        if (spotted) { L.vansSpotted++; if (R() < st.ambush) { L.vansHit++; if (rec) VANS.at(-1).hit = true; ev('van', `Region ${ri + 1}: a supply van is ambushed`, {r: ri, g: gi}); continue; } }
        for (const k of STOCKS) g.stock[k] += load[k];
      }
      if (newMonth) {
        // Cobra's own missions draw stock (fewer while the region is quiet)
        const nm = P.cobraMissions * (reg.quiet > 0 ? P.quietFactor : 1);
        const k1 = Math.floor(nm) + (R() < nm % 1 ? 1 : 0);
        for (let i = 0; i < k1; i++) battle(reg, reg.garrisons[Math.floor(R() * reg.garrisons.length)], P.menLostCobraBattle);
      }
    }
    if (t % T === 0) {
      // the player: raids this month, by strategy
      const strangle = P.strategy === 'strangle';
      const n = Math.floor(st.raids) + (R() < st.raids % 1 ? 1 : 0);
      for (let i = 0; i < n; i++) {
        const reg = strangle ? regions[0] : regions[Math.floor(R() * regions.length)];
        const live = STOCKS.filter(k => reg.producers[k].down === 0 && !(k === 'cells' && m < P.destroMonth));
        let tgt = 'garrison';
        if (P.strategy === 'producers' && live.length) tgt = 'producer';
        else if (P.strategy === 'missileWorks' && reg.producers.missiles.down === 0) tgt = 'missiles';
        else if (P.strategy === 'hub' && R() < 0.6) tgt = 'hub';
        else if ((strangle || P.strategy === 'balanced') && R() < 0.3 && live.length) tgt = 'producer';
        const ri = regions.indexOf(reg);
        if (tgt === 'producer') { const k = live[Math.floor(R() * live.length)]; reg.producers[k].down = P.rebuildMonths; L.producerRaids++; ev('raidProducer', `Region ${ri + 1}: the Joes wreck the ${k} producer`, {r: ri, k}); }
        else if (tgt === 'missiles') { reg.producers.missiles.down = P.rebuildMonths; L.producerRaids++; ev('raidProducer', `Region ${ri + 1}: the Joes wreck the missile works`, {r: ri, k: 'missiles'}); }
        else if (tgt === 'hub') { for (const k of STOCKS) reg.hub[k] *= 0.2; L.hubRaids++; ev('raidHub', `Region ${ri + 1}: the Joes raid the hub and blow its stock`, {r: ri}); }
        else { const gi = Math.floor(R() * reg.garrisons.length), g = reg.garrisons[gi]; g.attacked = 2; battle(reg, g, P.menLostJoeRaid); ev('raidGarrison', `Region ${ri + 1}: the Joes hit garrison ${gi + 1}`, {r: ri, g: gi}); }
      }
    }
    if (t % T === T - 1) {
      // end of month: emergency shipments, pull-back, tracking
      for (const [ri, reg] of regions.entries()) {
        let empty = 0;
        for (const k of STOCKS) {
          if (k === 'cells' && m < P.destroMonth) continue;
          const need = P.battleNeed[k];
          if (total(reg, k) < need * P.emergencyThreshold) {
            if (k === 'missiles' || k === 'vehicles' || k === 'aircraft') empty++;
            if (!(reg.cool[k] > m)) {
              const donor = regions.filter(o => o !== reg).sort((a, b) => b.hub[k] - a.hub[k])[0];
              const load = need * P.emergencyLoadBattles;
              if (load > 0 && donor && donor.hub[k] >= load * 2) {
                donor.hub[k] -= load; L.emergSent++; reg.cool[k] = m + 1;
                const from = regions.indexOf(donor), hit = R() < st.intercept;
                ev('emergency', `Emergency ${k} from region ${from + 1} to region ${ri + 1}${hit ? ': intercepted' : ''}`, {from, to: ri, k, hit});
                if (hit) L.emergHit++; else intransit.push({at: t + 1, to: reg, load: {[k]: load}});
              }
            }
          }
        }
        if (reg.quiet > 0) { reg.quiet--; L.quietMonths++; }
        else if (empty >= P.pullbackEmptyStocks) { reg.starvedMonths++; if (reg.starvedMonths >= 2) { reg.quiet = P.pullbackMonths; reg.starvedMonths = 0; ev('quiet', `Region ${ri + 1} is starved: Cobra pulls back there`, {r: ri}); } }
        else reg.starvedMonths = 0;
      }
      for (const k of STOCKS) L.track[k].push(total(regions[0], k));
      for (const reg of regions) { L.behind += capAt(m) - reg.tier; L.behindN++;
        for (const g of reg.garrisons) if (g.men > 0) { L.armed += Math.min(1, g.stock.guns / g.men); L.armedN++; } }
      const r0 = regions[0], men0 = r0.garrisons.reduce((a, g) => a + g.men, 0);
      L.track.men.push(men0 / r0.garrisons.length); L.track.tier.push(r0.tier); L.track.cap.push(capAt(m));
      L.track.spare.push(Math.max(0, total(r0, 'guns') - men0));
      if (rec) {
        frames.push({m, events: E, vans: VANS, cap: capAt(m), regions: regions.map(reg => ({funds: reg.funds, quiet: reg.quiet, tier: reg.tier,
          hub: Object.fromEntries(STOCKS.map(k => [k, Math.floor(reg.hub[k])])),
          producers: Object.fromEntries(STOCKS.map(k => [k, k === 'cells' && m < P.destroMonth ? -1 : reg.producers[k].down])),
          garrisons: reg.garrisons.map(g => { const o = {stock: Object.fromEntries(STOCKS.map(k => [k, Math.floor(g.stock[k])])), short: g.shortNow || [], attacked: g.attacked, men: g.men}; g.shortNow = []; return o; })}))});
        E = []; VANS = [];
      }
    }
  }
  L.frames = frames; return L;
}

function split(P) {
  const R = rng(P.seed), out = {};
  for (const style of SPLIT_STYLES) {
    const Ls = []; for (let i = 0; i < P.runs; i++) Ls.push(splitRun(P, style, R));
    const sum = k => mean(Ls.map(l => l[k]));
    const shortPct = {}, wanted = {};
    for (const k of STOCKS) { const b = Ls.reduce((a, l) => a + l.battlesBy[k], 0), s = Ls.reduce((a, l) => a + l.short[k], 0); wanted[k] = b; shortPct[k] = b ? s * 100 / b : 0; }
    const track = {}; for (const k of [...STOCKS, 'men', 'tier', 'cap', 'spare']) { track[k] = []; for (let m = 0; m < P.months; m++) track[k].push(k === 'tier' ? mean(Ls.map(l => l.track[k][m])) : median(Ls.map(l => l.track[k][m]))); }
    out[style] = {battles: sum('battles'), shortPct, onFloor: sum('onFloor'), vans: sum('vans'), vansSpotted: sum('vansSpotted'),
      vansHit: sum('vansHit'), emergSent: sum('emergSent'), emergHit: sum('emergHit'), quietMonths: sum('quietMonths'),
      emptyGarrison: sum('emptyGarrison'), recruited: sum('recruited'), behind: mean(Ls.map(l => l.behind / l.behindN)),
      armed: mean(Ls.map(l => l.armedN ? l.armed * 100 / l.armedN : 0)), menEnd: mean(Ls.map(l => l.track.men.at(-1))),
      tierEnd: mean(Ls.map(l => l.track.tier.at(-1))), capEnd: Ls[0].track.cap.at(-1), spareEnd: median(Ls.map(l => l.track.spare.at(-1))),
      producerRaids: sum('producerRaids'), prodPct: mean(Ls.map(l => l.prodScaleN ? l.prodScale * 100 / l.prodScaleN : 0)), hubRaids: sum('hubRaids'), downMonths: sum('downMonths'), track};
  }
  return out;
}

const SPLIT_SCENARIOS = {
  'Balanced player (mostly garrisons, some producers)': {strategy: 'balanced'},
  'Producer hunter (hit any factory line)': {strategy: 'producers'},
  'Missile works hunter': {strategy: 'missileWorks'},
  'Hub raider (hit the Drome / depot stock)': {strategy: 'hub'},
  'Van hunter (strong intel)': {strategy: 'vans', vanSpot: 0.12},
  'Strangle one region (all raids on region 1)': {strategy: 'strangle'},
  'Destro joins early (month 6)': {destroMonth: 6},
  'Destro joins late (month 16)': {destroMonth: 16},
  'All-in on manpower (priority 0.99)': {manpowerPriority: 0.99},
  'Even split, men and guns (priority 0.5)': {manpowerPriority: 0.5},
  'Quality Cobra (priority 0.2, against the thesis)': {manpowerPriority: 0.2},
  'Poor Cobra (income 200)': {regionIncome: 200},
  'Rich Cobra (income 450)': {regionIncome: 450},
  'No emergency shipments': {emergencyLoadBattles: 0},
  'Hoarding hub (ships 25% a tick)': {shipFraction: 0.25},
  'One region only': {regions: 1},
};

function act1Replay(P, style, n) { const R = rng((P.seed * 7919 + n * 104729) >>> 0); return act1Run(P, style, R, true); }
function splitReplay(P, style, n) { const R = rng((P.seed * 7919 + n * 104729) >>> 0); return splitRun(P, style, R, true); }
return {NAMES, act1Replay, splitReplay, act1, split, ACT1_DEFAULTS, SPLIT_DEFAULTS, ACT1_SCENARIOS, SPLIT_SCENARIOS, ACT1_STYLES, SPLIT_STYLES, STOCKS};
})();
if (typeof module !== 'undefined') module.exports = SIM;
