/**
 * League-aware scoring.
 *
 * Sleeper stores a league's scoring rules as a flat map of stat_id → multiplier
 * (e.g. { rec: 1, rec_yd: 0.1, pass_td: 4, fum_lost: -2 }). Projection and stat
 * rows use the *same* stat ids. So a player's projected points under YOUR
 * league's rules is simply the dot product of the two maps. This means a PPR
 * league and a standard league see different numbers from the same projection —
 * exactly what a GM needs.
 */
import type { Player } from '../api/sleeper';

export function scoreStats(
  stats: Record<string, number> | undefined,
  scoring: Record<string, number> | undefined,
): number {
  if (!stats || !scoring) return 0;
  let total = 0;
  for (const key in scoring) {
    const stat = stats[key];
    if (typeof stat === 'number') total += stat * scoring[key];
  }
  return total;
}

export function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

/** Injury designations that should visibly warn a manager, worst first. */
const INJURY_WEIGHT: Record<string, number> = {
  Out: 4,
  IR: 4,
  Sus: 4,
  PUP: 4,
  Doubtful: 3,
  Questionable: 2,
  Probable: 1,
};

export interface InjuryFlag {
  label: string;
  severity: number; // 0 none, 1 note, 2 caution, 3-4 danger
}

export function injuryFlag(p: Player | undefined): InjuryFlag | null {
  if (!p) return null;
  const raw = p.injury_status || (p.status && p.status !== 'Active' ? p.status : null);
  if (!raw) return null;
  const severity = INJURY_WEIGHT[raw] ?? 1;
  return { label: raw, severity };
}

/** A ranked lineup decision for one roster slot. */
export interface LineupCandidate {
  playerId: string;
  player: Player | undefined;
  projected: number;
  injury: InjuryFlag | null;
  isStarter: boolean;
}

/**
 * Slot definitions from roster_positions, minus the non-playable ones (BN, IR,
 * TAXI). FLEX-type slots list every position they can accept.
 */
const FLEX_ELIGIBILITY: Record<string, string[]> = {
  FLEX: ['RB', 'WR', 'TE'],
  WRRB_FLEX: ['RB', 'WR'],
  REC_FLEX: ['WR', 'TE'],
  SUPER_FLEX: ['QB', 'RB', 'WR', 'TE'],
  IDP_FLEX: ['DL', 'LB', 'DB'],
};

export function slotAccepts(slot: string, pos: string | null | undefined): boolean {
  if (!pos) return false;
  if (slot === pos) return true;
  const elig = FLEX_ELIGIBILITY[slot];
  return elig ? elig.includes(pos) : false;
}

export function playablePositions(rosterPositions: string[]): string[] {
  return rosterPositions.filter((s) => s !== 'BN' && s !== 'IR' && s !== 'TAXI');
}

/**
 * Greedy optimal lineup: for each roster slot (in league order), pick the
 * highest-projected still-available player that the slot accepts. Rigid slots
 * (QB, RB…) are filled before flex slots so a flex doesn't steal a player a
 * rigid slot needed. Returns the chosen player id per slot plus the leftovers.
 */
export interface OptimalResult {
  slots: { slot: string; playerId: string | null; projected: number }[];
  benchedButBetter: string[]; // players outscoring someone you're starting
  totalProjected: number;
}

export function optimizeLineup(
  rosterPositions: string[],
  candidateIds: string[],
  projById: (id: string) => number,
  posById: (id: string) => string | null,
): OptimalResult {
  const slots = playablePositions(rosterPositions);
  // Fill rigid (non-flex) slots first, then flex slots — both in descending
  // projection order within the eligible pool.
  const order = [...slots]
    .map((slot, i) => ({ slot, i, flex: FLEX_ELIGIBILITY[slot] ? 1 : 0 }))
    .sort((a, b) => a.flex - b.flex || a.i - b.i);

  const used = new Set<string>();
  const chosen: Record<number, { playerId: string | null; projected: number }> = {};

  for (const { slot, i } of order) {
    let best: string | null = null;
    let bestProj = -Infinity;
    for (const id of candidateIds) {
      if (used.has(id)) continue;
      if (!slotAccepts(slot, posById(id))) continue;
      const proj = projById(id);
      if (proj > bestProj) {
        bestProj = proj;
        best = id;
      }
    }
    if (best) used.add(best);
    chosen[i] = { playerId: best, projected: best ? Math.max(bestProj, 0) : 0 };
  }

  const resultSlots = slots.map((slot, i) => ({
    slot,
    playerId: chosen[i]?.playerId ?? null,
    projected: chosen[i]?.projected ?? 0,
  }));

  const totalProjected = resultSlots.reduce((s, r) => s + r.projected, 0);

  return { slots: resultSlots, benchedButBetter: [], totalProjected };
}
