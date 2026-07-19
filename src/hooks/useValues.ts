/**
 * League-aware player value. The trade analyzer and draft board both need a
 * single number that says "how good is this player, under our rules?". We derive
 * it from Sleeper's full-season projection scored with the league's own scoring
 * settings, so a PPR league values pass-catching backs higher than a standard
 * league does — automatically.
 *
 * If season projections are unavailable (off-season, endpoint down) we fall back
 * to Sleeper's `search_rank`, an ADP-like relevance ordering, so the board still
 * ranks sensibly.
 */
import { useEffect, useMemo, useState } from 'react';
import { getSeasonProjections, type PlayerMap } from '../api/sleeper';
import { scoreStats } from '../lib/scoring';

export interface ValueApi {
  value: (playerId: string) => number;
  loading: boolean;
  projectionBased: boolean;
  /** All fantasy-relevant players, ranked by value descending. */
  ranked: string[];
}

const REAL_POSITIONS = new Set(['QB', 'RB', 'WR', 'TE', 'K', 'DEF']);

export function useValues(
  season: string | null,
  scoring: Record<string, number> | undefined,
  players: PlayerMap | undefined,
): ValueApi {
  const [raw, setRaw] = useState<Record<string, Record<string, number>>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!season) return;
    let cancelled = false;
    setLoading(true);
    getSeasonProjections(season)
      .then((r) => !cancelled && setRaw(r))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [season]);

  const projectionBased = Object.keys(raw).length > 0;

  const value = useMemo(() => {
    const cache: Record<string, number> = {};
    return (id: string): number => {
      if (id in cache) return cache[id];
      let v = 0;
      if (projectionBased && raw[id]) {
        v = scoreStats(raw[id], scoring);
      } else {
        // Fallback: invert search_rank into a rough 0–100 value band.
        const rank = players?.[id]?.search_rank;
        if (typeof rank === 'number' && rank > 0) v = Math.max(0, 300 - rank) / 3;
      }
      cache[id] = v;
      return v;
    };
  }, [raw, scoring, players, projectionBased]);

  const ranked = useMemo(() => {
    if (!players) return [];
    const ids = Object.keys(players).filter((id) => {
      const p = players[id];
      const pos = p.position || p.fantasy_positions?.[0];
      return pos && REAL_POSITIONS.has(pos) && (p.team || pos === 'DEF');
    });
    return ids.sort((a, b) => value(b) - value(a));
  }, [players, value]);

  return { value, loading, projectionBased, ranked };
}

/** Positional need weights from a set of roster slots (how many starters each pos needs). */
export function startingNeeds(rosterPositions: string[]): Record<string, number> {
  const needs: Record<string, number> = {};
  for (const slot of rosterPositions) {
    if (slot === 'BN' || slot === 'IR' || slot === 'TAXI') continue;
    const base = slot.includes('FLEX') || slot === 'SUPER_FLEX' ? 'FLEX' : slot;
    needs[base] = (needs[base] || 0) + 1;
  }
  return needs;
}
