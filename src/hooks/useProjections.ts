/**
 * Weekly projected points, scored under the active league's rules. Returns a
 * `proj(playerId)` lookup plus raw stat bags. Projections come from Sleeper's
 * unofficial data host and can be empty (off-season, endpoint hiccup); callers
 * should treat 0 as "no projection" and degrade gracefully.
 */
import { useEffect, useMemo, useState } from 'react';
import { getWeeklyProjections } from '../api/sleeper';
import { scoreStats } from '../lib/scoring';

export function useProjections(
  season: string | null,
  week: number,
  scoring: Record<string, number> | undefined,
) {
  const [raw, setRaw] = useState<Record<string, Record<string, number>>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!season) return;
    let cancelled = false;
    setLoading(true);
    (async () => {
      const data = await getWeeklyProjections(season, week);
      if (!cancelled) {
        setRaw(data);
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [season, week]);

  const proj = useMemo(() => {
    const cache: Record<string, number> = {};
    return (playerId: string): number => {
      if (playerId in cache) return cache[playerId];
      const v = scoreStats(raw[playerId], scoring);
      cache[playerId] = v;
      return v;
    };
  }, [raw, scoring]);

  const available = useMemo(() => Object.keys(raw).length > 0, [raw]);

  return { proj, raw, loading, available };
}
