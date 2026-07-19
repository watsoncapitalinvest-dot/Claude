/**
 * Loads the common "league bundle" every screen needs — league settings,
 * rosters, member users, and the player dictionary — and pins down which roster
 * belongs to the signed-in user. Screens layer their own week-specific data
 * (matchups, projections) on top of this.
 */
import { useCallback, useEffect, useState } from 'react';
import {
  getLeague,
  getLeagueUsers,
  getPlayers,
  getRosters,
  type League,
  type LeagueUser,
  type PlayerMap,
  type Roster,
} from '../api/sleeper';
import { useApp } from '../store/AppContext';

export interface LeagueBundle {
  league: League;
  rosters: Roster[];
  users: LeagueUser[];
  players: PlayerMap;
  myRoster: Roster | null;
  usersById: Record<string, LeagueUser>;
  rostersByOwner: Record<string, Roster>;
}

interface State {
  data: LeagueBundle | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useLeague(): State {
  const { leagueId, user } = useApp();
  const [data, setData] = useState<LeagueBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  const refresh = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    if (!leagueId || !user) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const [league, rosters, users, players] = await Promise.all([
          getLeague(leagueId),
          getRosters(leagueId),
          getLeagueUsers(leagueId),
          getPlayers(),
        ]);
        if (cancelled) return;

        const usersById: Record<string, LeagueUser> = {};
        for (const u of users) usersById[u.user_id] = u;
        const rostersByOwner: Record<string, Roster> = {};
        for (const r of rosters) if (r.owner_id) rostersByOwner[r.owner_id] = r;

        const myRoster = rosters.find((r) => r.owner_id === user.user_id) ?? null;

        setData({ league, rosters, users, players, myRoster, usersById, rostersByOwner });
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load league');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [leagueId, user, nonce]);

  return { data, loading, error, refresh };
}

/** Display name for a roster's manager, preferring a custom team name. */
export function managerName(
  ownerId: string | null,
  usersById: Record<string, LeagueUser>,
): string {
  if (!ownerId) return 'Unowned';
  const u = usersById[ownerId];
  if (!u) return 'Unknown';
  return u.metadata?.team_name || u.display_name || 'Manager';
}
