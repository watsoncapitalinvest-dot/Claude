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


// ---------------------------------------------------------------------------- MODE 3: THE SECRET WAR (COBRA_WORLDWIDE_v1)
// Cobra worldwide from day one; the Joes US-only until the reveal. Leaks fill a worldwide count; the reveal (Cobra takes
// Sierra Gordo, goes public, M.A.R.S. alliance) fires when the count is full and the floor has passed, or at the ceiling.
// Abroad runs on its own budget (it never touches the US fight). After the reveal: imports to Sierra Gordo, Joe strikes abroad.
const WORLD_REGIONS = ['Sierra Gordo', 'South America', 'Europe', 'Middle East', 'Africa', 'Asia'];
const LEAKS = ['covert', 'interrogation', 'paperwork', 'liaison', 'news'];
const WORLD_STYLES = ['absent', 'cautious', 'typical', 'aggressive'];
const WORLD_DEFAULTS = {
  runs: 400, months: 24, seed: 11,
  // the reveal
  revealThreshold: 100, revealFloor: 10, revealCeiling: 15,
  // the leaks: points each, and how often
  points: {covert: 10, interrogation: 6, paperwork: 5, liaison: 2, news: 1},
  covertSuccess: 0.7, covertCaught: 0.12, covertMarks: 1,       // per operation abroad
  paperworkPerRaid: 0.3, paperworkMarks: 0.5,                     // per US raid
  interrogationPerCapture: 0.5, interrogationMarks: 0.2,                                    // per prisoner taken
  liaisonPerMonth: 0.25, newsPerMonth: 0.5,
  // Cobra abroad grows offstage (its own budget), capped so 'big everywhere' is not too big
  startSitesAbroad: 2, growthPerMonth: 0.35, capSitesAbroad: 7,
  sgStartSites: 6, sgGrowthPerMonth: 0.5, sgCap: 14, sgStartMen: 60, sgMenPerMonth: 6,
  // after the reveal: Sierra Gordo makes rifles and grenades; lasers and up arrive as M.A.R.S. imports
  importsPerMonth: 2, importLoad: 6, importInterceptBase: 0.2, importInterceptPerPaperwork: 0.05, importInterceptMax: 0.7,
  cellsPerLaserMan: 1, regrowAfterReveal: 0.25, findUnknownPerOp: 0.5,
  styles: {
    absent:     {ops: 0,   raids: 0,   captures: 0,   strikes: 0,   goodwill: 1},
    cautious:   {ops: 0.3, raids: 0.5, captures: 0.3, strikes: 0.5, goodwill: 1},
    typical:    {ops: 0.6, raids: 1.0, captures: 0.6, strikes: 1,   goodwill: 1.2},
    aggressive: {ops: 1.0, raids: 2.0, captures: 1.0, strikes: 2,   goodwill: 1.2},
  },
};

function worldRun(P, style, R, rec) {
  const st = P.styles[style];
  const roll = x => Math.floor(x) + (R() < x % 1 ? 1 : 0);
  const regs = WORLD_REGIONS.map((name, i) => ({name, sg: i === 0, sites: i === 0 ? P.sgStartSites : P.startSitesAbroad, known: 0,
    cap: i === 0 ? P.sgCap : P.capSitesAbroad, grow: i === 0 ? P.sgGrowthPerMonth : P.growthPerMonth}));
  let count = 0, revealM = null, early = false, spiesHeld = 0, sgMen = P.sgStartMen, cellsStock = 0, laserMen = 0;
  const L = {by: Object.fromEntries(LEAKS.map(k => [k, 0])), opsRun: 0, caught: 0, imports: 0, intercepted: 0, struck: 0,
    track: {count: [], sites: [], known: [], laser: []}, frames: [], paperwork: 0};
  for (let m = 0; m < P.months; m++) {
    const E = []; const ev = (kind, text, extra) => { if (rec) E.push(Object.assign({kind, text}, extra || {})); };
    const pre = revealM == null;
    // Cobra abroad grows on its own budget; after the reveal it keeps growing a little
    for (const r of regs) { const g = pre ? r.grow : P.regrowAfterReveal; const add = roll(g); const room = r.cap - r.sites;
      const n = Math.max(0, Math.min(add, room)); if (n) { r.sites += n; ev('grow', `${r.name}: Cobra opens ${n > 1 ? n + ' sites' : 'a site'}`, {r: r.name}); } }
    if (pre) sgMen += P.sgMenPerMonth;
    const leak = (k, text, reg) => { if (!pre) return; count += P.points[k]; L.by[k] += P.points[k]; ev('leak', text, {k, r: reg}); };
    const mark = r => { if (r.known < r.sites) { r.known++; ev('mark', `${r.name}: a Cobra site is now known`, {r: r.name}); } };
    // covert operations abroad (pre-reveal: intel only)
    const ops = roll(st.ops);
    for (let i = 0; i < ops; i++) { L.opsRun++; const r = regs[Math.floor(R() * regs.length)];
      if (R() < P.covertCaught) { L.caught++; spiesHeld++; ev('caught', `A Joe spy is caught in ${r.name}`, {r: r.name}); continue; }
      if (R() < P.covertSuccess) { if (pre) leak('covert', `Covert operation in ${r.name} brings back a leak`, r.name);
        if (R() < (pre ? P.covertMarks : P.findUnknownPerOp)) mark(r); }
      else ev('op', `Covert operation in ${r.name} comes back empty`, {r: r.name}); }
    // US raids: paperwork with foreign addresses; captures: interrogations
    const raids = roll(st.raids);
    for (let i = 0; i < raids; i++) if (R() < P.paperworkPerRaid) { L.paperwork++;
      const r = regs[Math.floor(R() * regs.length)]; leak('paperwork', `Captured paperwork with an address in ${r.name}`, r.name); if (R() < P.paperworkMarks) mark(r); }
    const caps = roll(st.captures);
    for (let i = 0; i < caps; i++) if (R() < P.interrogationPerCapture) { leak('interrogation', 'A Cobra prisoner talks about "the other cells"'); if (R() < P.interrogationMarks) mark(regs[Math.floor(R() * regs.length)]); }
    if (R() < P.liaisonPerMonth * st.goodwill) leak('liaison', 'A foreign government quietly passes something on');
    if (R() < P.newsPerMonth) leak('news', ['An unexplained bombing abroad', 'The junta tightens its grip in Sierra Gordo', 'A ship vanishes off West Africa'][Math.floor(R() * 3)]);
    // the reveal
    if (pre && ((count >= P.revealThreshold && m >= P.revealFloor) || m >= P.revealCeiling)) {
      revealM = m; early = m < P.revealCeiling;
      ev('reveal', `THE REVEAL: Cobra takes Sierra Gordo and goes public; M.A.R.S. joins${early ? ' (the leaks brought it early)' : ' (the ceiling: it happens anyway)'}`);
    }
    // after the reveal: M.A.R.S. imports to Sierra Gordo, Joe strikes on known sites abroad
    if (revealM != null && m > revealM) {
      const ic = Math.min(P.importInterceptMax, P.importInterceptBase + P.importInterceptPerPaperwork * L.paperwork);
      const n = roll(P.importsPerMonth);
      for (let i = 0; i < n; i++) { L.imports++; if (R() < ic * (st.strikes > 0 ? 1 : 0)) { L.intercepted++; ev('intercept', 'A M.A.R.S. cargo to Sierra Gordo is intercepted'); }
        else { cellsStock += P.importLoad; ev('import', 'A M.A.R.S. cargo reaches Sierra Gordo'); } }
      const arm = Math.min(Math.floor(cellsStock / P.cellsPerLaserMan), sgMen - laserMen); laserMen += arm; cellsStock -= arm * P.cellsPerLaserMan;
      const sk = roll(st.strikes);
      for (let i = 0; i < sk; i++) { const tg = regs.filter(r => r.known > 0); if (!tg.length) break; const r = tg[Math.floor(R() * tg.length)];
        r.known--; r.sites--; L.struck++; ev('strike', `The Joes strike a known Cobra site in ${r.name}`, {r: r.name}); }
    }
    const sites = regs.reduce((a, r) => a + r.sites, 0), known = regs.reduce((a, r) => a + r.known, 0);
    L.track.count.push(count); L.track.sites.push(sites); L.track.known.push(known); L.track.laser.push(sgMen ? laserMen * 100 / sgMen : 0);
    if (rec) L.frames.push({m, count, revealed: revealM != null && m >= revealM, revealNow: revealM === m, spiesHeld,
      regions: regs.map(r => ({name: r.name, sg: r.sg, sites: r.sites, known: r.known})), sgMen, laserMen, events: E});
  }
  const atReveal = revealM == null ? null : {sites: L.track.sites[revealM], known: L.track.known[revealM]};
  return Object.assign(L, {revealM, early, atReveal});
}

function world(P) {
  const R = rng(P.seed), out = {};
  for (const style of WORLD_STYLES) {
    const Ls = []; for (let i = 0; i < P.runs; i++) Ls.push(worldRun(P, style, R));
    const hist = Array(P.months).fill(0); for (const l of Ls) if (l.revealM != null) hist[l.revealM]++;
    const tr = k => { const res = []; for (let m = 0; m < P.months; m++) res.push(median(Ls.map(l => l.track[k][m]))); return res; };
    out[style] = {revealMed: median(Ls.map(l => l.revealM).filter(x => x != null)), earlyPct: Ls.filter(l => l.early).length * 100 / P.runs,
      hist, sitesAtReveal: mean(Ls.filter(l => l.atReveal).map(l => l.atReveal.sites)), knownAtReveal: mean(Ls.filter(l => l.atReveal).map(l => l.atReveal.known)),
      knownPctAtReveal: mean(Ls.filter(l => l.atReveal).map(l => l.atReveal.sites ? l.atReveal.known * 100 / l.atReveal.sites : 0)),
      leakBy: Object.fromEntries(LEAKS.map(k => [k, mean(Ls.map(l => l.by[k]))])), caught: mean(Ls.map(l => l.caught)), ops: mean(Ls.map(l => l.opsRun)),
      imports: mean(Ls.map(l => l.imports)), intercepted: mean(Ls.map(l => l.intercepted)), struck: mean(Ls.map(l => l.struck)),
      laserEnd: mean(Ls.map(l => l.track.laser.at(-1))), sitesEnd: mean(Ls.map(l => l.track.sites.at(-1))),
      track: {count: tr('count'), sites: tr('sites'), known: tr('known'), laser: tr('laser')}};
  }
  return out;
}
const WORLD_SCENARIOS = {
  'As designed': {},
  'The player never digs (no covert ops)': {styles: {absent: WORLD_DEFAULTS.styles.absent, cautious: Object.assign({}, WORLD_DEFAULTS.styles.cautious, {ops: 0}), typical: Object.assign({}, WORLD_DEFAULTS.styles.typical, {ops: 0}), aggressive: Object.assign({}, WORLD_DEFAULTS.styles.aggressive, {ops: 0})}},
  'Spy-heavy player (two operations a month)': {styles: {absent: WORLD_DEFAULTS.styles.absent, cautious: Object.assign({}, WORLD_DEFAULTS.styles.cautious, {ops: 2}), typical: Object.assign({}, WORLD_DEFAULTS.styles.typical, {ops: 2}), aggressive: Object.assign({}, WORLD_DEFAULTS.styles.aggressive, {ops: 2})}},
  'Cobra grows fast abroad (0.7 a month, cap 10)': {growthPerMonth: 0.7, capSitesAbroad: 10},
  'Cobra grows slowly abroad (0.15 a month, cap 4)': {growthPerMonth: 0.15, capSitesAbroad: 4},
  'Easier reveal (threshold 60)': {revealThreshold: 60},
  'Harder reveal (threshold 140)': {revealThreshold: 140},
  'Earlier window (floor 8, ceiling 12)': {revealFloor: 8, revealCeiling: 12},
  'Later window (floor 12, ceiling 18)': {revealFloor: 12, revealCeiling: 18},
  'Heavy M.A.R.S. imports (4 a month)': {importsPerMonth: 4},
  'Leaky spies (25% caught)': {covertCaught: 0.25},
};
function worldReplay(P, style, n) { const R = rng((P.seed * 7919 + n * 104729) >>> 0); return worldRun(P, style, R, true); }

// ------------------------------------------------------------------ mode 4: intel cases (INTEL_CASES_v1)
// Missions bring things home; at the debrief the player chooses what to send to Intel (the sending policy). Each item sent
// opens a case and waits for an analyst; an analyst works one case a month. Whether a case pays depends on its source
// (officer > papers > gear). A hit is a key story clue (the Act 1 chain), a lead to act on (a site or a delivery: a raid),
// or a name (field work for an intel Joe; often a dead end). Leads age: the warning is by time only; whether Cobra really
// moved is hidden and depends on how alert it is. A key clue the player misses comes back by another road, late.
const INTEL_STYLES = ['absent', 'cautious', 'typical', 'aggressive'];
const INTEL_POLICIES = ['everything', 'pick', 'little'];
const INTEL_SOURCES = ['officer', 'papers', 'gear', 'lab', 'villain'];
const INTEL_KEYS = ['Flight routes', 'A depot', 'The second depot', 'Drome rumours', 'Where the Drome is', 'M.A.R.S. markings'];
const INTEL_DEFAULTS = {
  runs: 400, months: 18, seed: 23,
  // what one mission brings home (average count per mission)
  bring: {officer: {perMission: 0.5, pays: 0.35, send_pick: 1, send_little: 1},
          papers: {perMission: 0.8, pays: 0.20, send_pick: 1, send_little: 0.5},
          gear: {perMission: 3.0, pays: 0.075, send_pick: 0.2, send_little: 0},
          // places and people that carry key intel (John 23:06): a lab outpost's research files, a captured named villain
          lab: {perMission: 0.08, pays: 0.6, send_pick: 1, send_little: 1, key: 0.6, leads: 1},
          villain: {perMission: 0.03, pays: 1, send_pick: 1, send_little: 1, key: 1, leads: 3}},
  // analysts: seats on Day 1, the share put on cases (the rest research), cases one analyst closes a month
  analystsStart: 10, analystShare: 0.5, casesPerAnalyst: 1,
  // what a hit is: a key clue (only once that clue is due), a lead to act on, or a name
  keyChance: 0.35, leadChance: 0.4,
  keyDue: [3, 5, 7, 9, 10, 12], keyEarly: 2, keyGrace: 3,           // a key can be found from due-early; it comes back by another road at due+grace
  // field work on a name: an intel Joe, a few jobs a month
  joeJobsPerMonth: 2, namePays: 0.3, joeCaught: 0.05, joeHeldMonths: 2,
  // leads: acting on one is a raid; Cobra may have moved since (hidden)
  // the squad is shared (John 22:54, C): answering Cobra's own moves (terror, robberies, outpost defence) comes first, and
  // lead raids get what is left; an answered move is a mission that brings things home
  cobraMoves: 1.5, cobraMovesGrowth: 0.1, answerFirst: 1,
  // leads point at something (John 22:58): some at the key clue the player is after; he raids those first and lets old side
  // leads lapse once he has found what he was looking for
  keyLeadChance: 0.35, dropSideOnKey: 1,
  staleAfter: 2, moveQuiet: 0.08, moveAlert: 0.3, alertRaids: 3, trapShare: 0.3, raidCaptures: 0.6,
  styles: {
    absent:     {squad: 0.5, squadGrowth: 0,    seatsPerMonth: 0,    joeEvery: 0},
    cautious:   {squad: 1.5, squadGrowth: 0.05, seatsPerMonth: 0.25, joeEvery: 8},
    typical:    {squad: 3,   squadGrowth: 0.1,  seatsPerMonth: 0.5,  joeEvery: 5},
    aggressive: {squad: 4.5, squadGrowth: 0.15, seatsPerMonth: 0.75, joeEvery: 4},
  },
};

function intelRun(P, style, policy, R, rec) {
  const st = P.styles[style];
  const roll = x => Math.floor(x) + (R() < x % 1 ? 1 : 0);
  const pois = l => { let k = 0, p = Math.exp(-l), c = p; const u = R(); while (u > c && k < 50) { k++; p *= l / k; c += p; } return k; };
  let seats = P.analystsStart, joes = 1, held = [], keys = 0, nextCase = 1;
  const queue = [], leads = [], names = [], keyMonth = Array(INTEL_KEYS.length).fill(null), keyRoad = Array(INTEL_KEYS.length).fill(null);
  const raidHist = [];
  const L = {moves: 0, answered: 0, unanswered: 0, opened: 0, worked: 0, dead: 0, hits: 0, byKeyRoad: 0, missedKeys: 0, notSent: 0, waitSum: 0,
    leadsActed: 0, keyRaids: 0, keyByRaid: 0, dropped: 0, leadsOld: 0, empty: 0, traps: 0, good: 0, namesChased: 0, namesPaid: 0, joesCaught: 0, extraCaptures: 0,
    track: {keys: [], backlog: [], seats: [], leads: []}, frames: []};
  const send = src => policy === 'everything' ? 1 : P.bring[src][policy === 'pick' ? 'send_pick' : 'send_little'];
  let carry = 0;   // captures from raids on good leads, brought home next month
  for (let m = 0; m < P.months; m++) {
    const E = []; const ev = (kind, text, extra) => { if (rec) E.push(Object.assign({kind, text}, extra || {})); };
    if (m > 0) seats += st.seatsPerMonth;
    if (st.joeEvery && m > 0 && m % st.joeEvery === 0) { joes++; ev('joe', 'A new intel Joe joins Scarlett'); }
    held = held.filter(h => { if (h <= m) { joes++; ev('joe', 'A held intel Joe is back'); return false; } return true; });
    const due = k => m >= P.keyDue[k] - P.keyEarly;
    const findKey = (how, src) => { if (keys >= INTEL_KEYS.length || !due(keys)) return false;
      keyMonth[keys] = m; keyRoad[keys] = how; ev('key', `KEY CLUE: ${INTEL_KEYS[keys]} (${how === 'road' ? 'came back by another road' : 'from ' + src})`); keys++;
      // what he was after is found: leads aimed at it become side leads, and old side leads are let go
      for (const l of leads) if (l.key != null && l.key < keys) l.key = null;
      if (P.dropSideOnKey) { const before = leads.length; for (let j = leads.length - 1; j >= 0; j--) if (leads[j].key == null && m - leads[j].found >= P.staleAfter) leads.splice(j, 1);
        if (before > leads.length) { L.dropped += before - leads.length; ev('drop', `${before - leads.length} old side lead${before - leads.length > 1 ? 's' : ''} let go`); } }
      return true; };
    const newLead = (text) => { const key = keys < INTEL_KEYS.length && R() < P.keyLeadChance ? keys : null; leads.push({found: m, key});
      ev('lead', text + (key != null ? ` (points toward ${INTEL_KEYS[key]})` : '')); };
    // the squad: Cobra's moves first (if the player answers them first), then lead raids with what is left
    let squad = roll(st.squad + st.squadGrowth * m); const moves = pois(P.cobraMoves + P.cobraMovesGrowth * m); L.moves += moves;   // busy months and quiet months
    const answered = Math.min(moves, R() < P.answerFirst ? squad : Math.max(0, squad - leads.length)); squad -= answered;
    L.answered += answered; L.unanswered += moves - answered;
    if (moves) ev('moves', `Cobra makes ${moves} move${moves > 1 ? 's' : ''}; the Joes answer ${answered}`);
    // the debrief: what the missions brought home, and what is sent to Intel
    const missions = answered;
    let brought = 0, sent = 0;
    for (const src of INTEL_SOURCES) {
      const n = roll(P.bring[src].perMission * missions) + (src === 'officer' ? carry : 0);
      for (let i = 0; i < n; i++) { brought++;
        if (R() < send(src)) { sent++; L.opened++; queue.push({id: nextCase++, src, opened: m}); }
        else { L.notSent++; if (R() < P.bring[src].pays && R() < (P.bring[src].key ?? P.keyChance) && keys < INTEL_KEYS.length && due(keys)) L.missedKeys++; } } }
    carry = 0;
    if (missions) ev('debrief', `${missions} mission${missions > 1 ? 's' : ''}: ${brought} things brought home, ${sent} sent to Intel`);
    // analysts work the queue, oldest first
    const cap = Math.floor(seats * P.analystShare * P.casesPerAnalyst);
    const work = queue.splice(0, cap), done = [];
    for (const c of work) { L.worked++; L.waitSum += m - c.opened;
      if (R() < P.bring[c.src].pays) { L.hits++;
        const extra = P.bring[c.src].leads || 0;
        for (let x = 0; x < extra; x++) newLead(c.src === 'villain' ? 'The captured villain talks: a site to hit' : 'The lab\'s research files point somewhere');
        if (c.src === 'villain') ev('villain', 'A NAMED VILLAIN IS CAPTURED AND TALKS');
        if (R() < (P.bring[c.src].key ?? P.keyChance) && findKey('case', c.src === 'villain' ? 'the captured villain' : c.src)) { done.push({c, out: 'key'}); continue; }
        if (R() < P.leadChance / (1 - P.keyChance)) { newLead(`Case ${c.id} (${c.src}): a delivery time or a site to hit`); done.push({c, out: 'lead'}); }
        else { names.push({found: m}); done.push({c, out: 'name'}); ev('name', `Case ${c.id} (${c.src}): a name, nobody on file`); } }
      else { L.dead++; done.push({c, out: 'dead'}); } }
    // field work: intel Joes chase names
    const jobs = joes * P.joeJobsPerMonth;
    for (let j = 0; j < jobs && names.length; j++) { names.shift(); L.namesChased++;
      if (R() < P.joeCaught) { L.joesCaught++; joes--; held.push(m + P.joeHeldMonths); ev('caught', 'An intel Joe is caught chasing a name'); if (joes <= 0) break; continue; }
      if (R() < P.namePays) { L.namesPaid++; if (!findKey('case', 'a name')) newLead('A name pays: an address worth hitting'); }
      else ev('deadname', 'A name leads nowhere (a regular guy, asleep)'); }
    // raids on leads, oldest first; Cobra may have moved (hidden, more likely when it is alert)
    const alert = raidHist.slice(-2).reduce((a, b) => a + b, 0) >= P.alertRaids;
    let raids = 0; const rc = squad;
    // leads aimed at the clue he is after go first (freshest first), then side leads (freshest first)
    leads.sort((a, b) => ((a.key != null ? 0 : 1) - (b.key != null ? 0 : 1)) || (b.found - a.found));
    for (let i = 0; i < rc && leads.length; i++) { const ld = leads.shift(); raids++; L.leadsActed++; if (ld.key != null) L.keyRaids++;
      const age = m - ld.found; if (age >= P.staleAfter) L.leadsOld++;
      const moved = 1 - Math.pow(1 - (alert ? P.moveAlert : P.moveQuiet), age + 1);
      if (R() < moved) { if (R() < P.trapShare) { L.traps++; ev('trap', `Raid on a ${age}-month-old lead: a trap`); } else { L.empty++; ev('empty', `Raid on a ${age}-month-old lead: empty, Cobra moved`); } }
      else if (ld.key != null && ld.key === keys && findKey('raid', 'a raid')) { L.good++; L.keyByRaid++; }
      else { L.good++; const c = roll(P.raidCaptures); carry += c; L.extraCaptures += c; ev('raid', `Raid on a ${age}-month-old lead pays${c ? ': an officer taken' : ''}`); } }
    raidHist.push(raids + answered);   // every fight counts toward Cobra's alertness
    // a key clue the player missed comes back by another road
    if (keys < INTEL_KEYS.length && m >= P.keyDue[keys] + P.keyGrace) { L.byKeyRoad++; findKey('road'); }
    L.track.keys.push(keys); L.track.backlog.push(queue.length); L.track.seats.push(cap);
    L.track.leads.push(leads.length);
    if (rec) L.frames.push({m, moves, answered, seats: cap, joes, held: held.length, queue: queue.map(c => ({id: c.id, src: c.src, age: m - c.opened})),
      done: done.map(d => ({id: d.c.id, src: d.c.src, out: d.out})), leads: leads.map(l => ({age: m - l.found, key: l.key != null})), names: names.length, keys, alert, events: E});
  }
  return Object.assign(L, {keyMonth, keyRoad, spineDone: keys >= INTEL_KEYS.length ? keyMonth.at(-1) : null});
}

function intel(P) {
  const R = rng(P.seed), out = {};
  for (const policy of INTEL_POLICIES) { out[policy] = {};
    for (const style of INTEL_STYLES) {
      const Ls = []; for (let i = 0; i < P.runs; i++) Ls.push(intelRun(P, style, policy, R));
      const tr = k => { const res = []; for (let m = 0; m < P.months; m++) res.push(median(Ls.map(l => l.track[k][m]))); return res; };
      const hist = Array(P.months).fill(0); for (const l of Ls) if (l.spineDone != null) hist[l.spineDone]++;
      out[policy][style] = {spineMed: median(Ls.map(l => l.spineDone).filter(x => x != null)), spinePct: Ls.filter(l => l.spineDone != null).length * 100 / P.runs, hist,
        keyMed: INTEL_KEYS.map((_, k) => median(Ls.map(l => l.keyMonth[k]).filter(x => x != null))),
        roadPct: mean(Ls.map(l => l.byKeyRoad * 100 / INTEL_KEYS.length)), missedKeys: mean(Ls.map(l => l.missedKeys)),
        opened: mean(Ls.map(l => l.opened)), deadPct: mean(Ls.map(l => l.worked ? l.dead * 100 / l.worked : 0)),
        wait: mean(Ls.map(l => l.worked ? l.waitSum / l.worked : 0)), backlogEnd: mean(Ls.map(l => l.track.backlog.at(-1))),
        backlogPeak: mean(Ls.map(l => Math.max(...l.track.backlog))), notSent: mean(Ls.map(l => l.notSent)),
        leadsActed: mean(Ls.map(l => l.leadsActed)), oldPct: mean(Ls.map(l => l.leadsActed ? l.leadsOld * 100 / l.leadsActed : 0)),
        emptyPct: mean(Ls.map(l => l.leadsActed ? l.empty * 100 / l.leadsActed : 0)), trapPct: mean(Ls.map(l => l.leadsActed ? l.traps * 100 / l.leadsActed : 0)),
        keyRaids: mean(Ls.map(l => l.keyRaids)), keyByRaid: mean(Ls.map(l => l.keyByRaid)), dropped: mean(Ls.map(l => l.dropped)),
        names: mean(Ls.map(l => l.namesChased)), namesPaidPct: mean(Ls.map(l => l.namesChased ? l.namesPaid * 100 / l.namesChased : 0)), joesCaught: mean(Ls.map(l => l.joesCaught)),
        unansweredPct: mean(Ls.map(l => l.moves ? l.unanswered * 100 / l.moves : 0)), leadsEnd: mean(Ls.map(l => l.track.leads.at(-1))),
        track: {keys: tr('keys'), backlog: tr('backlog'), seats: tr('seats'), leads: tr('leads')}};
    } }
  return out;
}
const INTEL_SCENARIOS = {
  'As designed (far less: 35 / 20 / 5-10%)': {},
  'STORY\'s first odds (70 / 50 / 25%)': {bring: {officer: {perMission: 0.5, pays: 0.7, send_pick: 1, send_little: 1}, papers: {perMission: 0.8, pays: 0.5, send_pick: 1, send_little: 0.5}, gear: {perMission: 3, pays: 0.25, send_pick: 0.2, send_little: 0}, lab: INTEL_DEFAULTS.bring.lab, villain: INTEL_DEFAULTS.bring.villain}},
  'No labs or villains (before 23:06)': {bring: Object.assign({}, INTEL_DEFAULTS.bring, {lab: Object.assign({}, INTEL_DEFAULTS.bring.lab, {perMission: 0}), villain: Object.assign({}, INTEL_DEFAULTS.bring.villain, {perMission: 0})})},
  'All analysts on cases': {analystShare: 1},
  'Few analysts on cases (a quarter)': {analystShare: 0.25},
  'No fallback: a missed key clue never comes back': {keyGrace: 99},
  'Slow fallback (6 months late)': {keyGrace: 6},
  'Cobra moves fast (quiet 15%, alert 50% a month)': {moveQuiet: 0.15, moveAlert: 0.5},
  'Names pay more often (50%)': {namePays: 0.5},
  'Only Scarlett all Act 1': {styles: {absent: INTEL_DEFAULTS.styles.absent, cautious: Object.assign({}, INTEL_DEFAULTS.styles.cautious, {joeEvery: 0}), typical: Object.assign({}, INTEL_DEFAULTS.styles.typical, {joeEvery: 0}), aggressive: Object.assign({}, INTEL_DEFAULTS.styles.aggressive, {joeEvery: 0})}},
  'Leads first: the player lets Cobra\'s moves go when he has leads': {answerFirst: 0},
  'Busy Cobra (2.5 moves a month, growing)': {cobraMoves: 2.5},
  'Quiet Cobra (0.8 moves a month)': {cobraMoves: 0.8, cobraMovesGrowth: 0.05},
};
function intelReplay(P, style, n, policy) { const R = rng((P.seed * 7919 + n * 104729) >>> 0); return intelRun(P, style, policy || 'pick', R, true); }

function act1Replay(P, style, n) { const R = rng((P.seed * 7919 + n * 104729) >>> 0); return act1Run(P, style, R, true); }
function splitReplay(P, style, n) { const R = rng((P.seed * 7919 + n * 104729) >>> 0); return splitRun(P, style, R, true); }
return {intel, intelReplay, INTEL_DEFAULTS, INTEL_SCENARIOS, INTEL_STYLES, INTEL_POLICIES, INTEL_SOURCES, INTEL_KEYS, world, worldReplay, WORLD_DEFAULTS, WORLD_SCENARIOS, WORLD_STYLES, WORLD_REGIONS, LEAKS, NAMES, act1Replay, splitReplay, act1, split, ACT1_DEFAULTS, SPLIT_DEFAULTS, ACT1_SCENARIOS, SPLIT_SCENARIOS, ACT1_STYLES, SPLIT_STYLES, STOCKS};
})();
if (typeof module !== 'undefined') module.exports = SIM;
