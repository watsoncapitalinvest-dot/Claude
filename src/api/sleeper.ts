/**
 * Sleeper API client.
 *
 * Sleeper's read-only API is public — no auth, no API key. There are two hosts:
 *   - api.sleeper.app/v1  → core resources (users, leagues, rosters, matchups)
 *   - api.sleeper.com     → stats & projections (unofficial but stable)
 *
 * The full player dictionary (~5MB) is fetched at most once a day and cached in
 * AsyncStorage so the rest of the app can resolve player_id → name/team/pos
 * without re-downloading it constantly.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const CORE = 'https://api.sleeper.app/v1';
const DATA = 'https://api.sleeper.com';

// ---- Types -----------------------------------------------------------------

export interface SleeperUser {
  user_id: string;
  username: string;
  display_name: string;
  avatar: string | null;
}

export interface NflState {
  season: string;
  season_type: string;
  week: number;
  leg: number;
  display_week: number;
}

export interface League {
  league_id: string;
  name: string;
  season: string;
  status: string;
  total_rosters: number;
  avatar: string | null;
  scoring_settings: Record<string, number>;
  roster_positions: string[];
  settings: Record<string, number>;
}

export interface Roster {
  roster_id: number;
  owner_id: string | null;
  players: string[] | null;
  starters: string[] | null;
  reserve: string[] | null;
  taxi: string[] | null;
  settings: {
    wins: number;
    losses: number;
    ties: number;
    fpts: number;
    fpts_decimal?: number;
    fpts_against?: number;
    fpts_against_decimal?: number;
    waiver_position?: number;
  };
}

export interface LeagueUser {
  user_id: string;
  display_name: string;
  avatar: string | null;
  metadata?: { team_name?: string };
}

export interface Matchup {
  roster_id: number;
  matchup_id: number | null;
  points: number;
  players: string[] | null;
  starters: string[] | null;
  players_points: Record<string, number> | null;
  starters_points: number[] | null;
}

export interface Player {
  player_id: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  position?: string | null;
  fantasy_positions?: string[] | null;
  team?: string | null;
  status?: string | null;
  injury_status?: string | null;
  injury_notes?: string | null;
  number?: number | null;
  age?: number | null;
  years_exp?: number | null;
  search_rank?: number | null;
  depth_chart_order?: number | null;
}

export type PlayerMap = Record<string, Player>;

export interface TrendingPlayer {
  player_id: string;
  count: number;
}

export interface Draft {
  draft_id: string;
  league_id: string;
  status: string; // 'pre_draft' | 'drafting' | 'complete'
  type: string; // 'snake' | 'linear' | 'auction'
  season: string;
  settings: Record<string, number>;
  draft_order: Record<string, number> | null; // user_id -> slot
  slot_to_roster_id: Record<string, number> | null;
  metadata?: Record<string, string>;
}

export interface DraftPick {
  player_id: string;
  picked_by: string; // user_id
  roster_id: number | null;
  round: number;
  pick_no: number;
  draft_slot: number;
}

/** Projection/stat rows come back with a `stats` bag keyed by Sleeper stat ids. */
export interface StatRow {
  player_id: string;
  week?: number;
  stats: Record<string, number>;
}

// ---- Fetch helper ----------------------------------------------------------

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: { accept: 'application/json' } });
  if (!res.ok) {
    throw new Error(`Sleeper request failed (${res.status}) for ${url}`);
  }
  return (await res.json()) as T;
}

// ---- Core endpoints --------------------------------------------------------

export function getUser(username: string): Promise<SleeperUser | null> {
  return getJson<SleeperUser | null>(`${CORE}/user/${encodeURIComponent(username.trim())}`);
}

export function getNflState(): Promise<NflState> {
  return getJson<NflState>(`${CORE}/state/nfl`);
}

export function getUserLeagues(userId: string, season: string): Promise<League[]> {
  return getJson<League[]>(`${CORE}/user/${userId}/leagues/nfl/${season}`);
}

export function getLeague(leagueId: string): Promise<League> {
  return getJson<League>(`${CORE}/league/${leagueId}`);
}

export function getRosters(leagueId: string): Promise<Roster[]> {
  return getJson<Roster[]>(`${CORE}/league/${leagueId}/rosters`);
}

export function getLeagueUsers(leagueId: string): Promise<LeagueUser[]> {
  return getJson<LeagueUser[]>(`${CORE}/league/${leagueId}/users`);
}

export function getMatchups(leagueId: string, week: number): Promise<Matchup[]> {
  return getJson<Matchup[]>(`${CORE}/league/${leagueId}/matchups/${week}`);
}

export function getTrending(
  type: 'add' | 'drop',
  lookbackHours = 24,
  limit = 40,
): Promise<TrendingPlayer[]> {
  return getJson<TrendingPlayer[]>(
    `${CORE}/players/nfl/trending/${type}?lookback_hours=${lookbackHours}&limit=${limit}`,
  );
}

export function getLeagueDrafts(leagueId: string): Promise<Draft[]> {
  return getJson<Draft[]>(`${CORE}/league/${leagueId}/drafts`);
}

export function getDraftPicks(draftId: string): Promise<DraftPick[]> {
  return getJson<DraftPick[]>(`${CORE}/draft/${draftId}/picks`);
}

// ---- Stats & projections (api.sleeper.com) ---------------------------------

/**
 * Weekly projections for every player. Returned as rows with a `stats` bag; we
 * turn it into a player_id → stats map. Best-effort: callers should tolerate an
 * empty map if the unofficial endpoint is unavailable.
 */
export async function getWeeklyProjections(
  season: string,
  week: number,
): Promise<Record<string, Record<string, number>>> {
  const url =
    `${DATA}/projections/nfl/${season}/${week}?season_type=regular` +
    `&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF`;
  try {
    const rows = await getJson<StatRow[] | Record<string, StatRow>>(url);
    return statRowsToMap(rows);
  } catch {
    return {};
  }
}

/** Actual weekly stats (used to grade past weeks / show real production). */
export async function getWeeklyStats(
  season: string,
  week: number,
): Promise<Record<string, Record<string, number>>> {
  const url =
    `${DATA}/stats/nfl/${season}/${week}?season_type=regular` +
    `&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF`;
  try {
    const rows = await getJson<StatRow[] | Record<string, StatRow>>(url);
    return statRowsToMap(rows);
  } catch {
    return {};
  }
}

/**
 * Full-season projections (no week param). Used to derive a league-aware player
 * "value" for the trade analyzer and draft board. Best-effort — returns an empty
 * map if the endpoint is unavailable.
 */
export async function getSeasonProjections(
  season: string,
): Promise<Record<string, Record<string, number>>> {
  const url =
    `${DATA}/projections/nfl/${season}?season_type=regular` +
    `&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF`;
  try {
    const rows = await getJson<StatRow[] | Record<string, StatRow>>(url);
    return statRowsToMap(rows);
  } catch {
    return {};
  }
}

function statRowsToMap(
  rows: StatRow[] | Record<string, StatRow>,
): Record<string, Record<string, number>> {
  const out: Record<string, Record<string, number>> = {};
  // Sleeper has returned both an array of rows and an object keyed by player_id
  // across versions — handle either so the News Room doesn't go dark on a shape
  // change.
  const list = Array.isArray(rows) ? rows : Object.values(rows || {});
  for (const row of list) {
    if (row && row.player_id && row.stats) out[row.player_id] = row.stats;
  }
  return out;
}

// ---- Player dictionary with on-device cache --------------------------------

const PLAYERS_CACHE_KEY = 'sleeper.players.nfl.v1';
const PLAYERS_TS_KEY = 'sleeper.players.nfl.ts.v1';
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

let memoryPlayers: PlayerMap | null = null;

export async function getPlayers(forceRefresh = false): Promise<PlayerMap> {
  if (memoryPlayers && !forceRefresh) return memoryPlayers;

  if (!forceRefresh) {
    try {
      const [cached, tsRaw] = await Promise.all([
        AsyncStorage.getItem(PLAYERS_CACHE_KEY),
        AsyncStorage.getItem(PLAYERS_TS_KEY),
      ]);
      const ts = tsRaw ? Number(tsRaw) : 0;
      if (cached && Date.now() - ts < ONE_DAY_MS) {
        memoryPlayers = JSON.parse(cached) as PlayerMap;
        return memoryPlayers;
      }
    } catch {
      // fall through to network
    }
  }

  const fresh = await getJson<PlayerMap>(`${CORE}/players/nfl`);
  memoryPlayers = fresh;
  // Persist best-effort; a 5MB string can occasionally fail to write.
  try {
    await AsyncStorage.setItem(PLAYERS_CACHE_KEY, JSON.stringify(fresh));
    await AsyncStorage.setItem(PLAYERS_TS_KEY, String(Date.now()));
  } catch {
    // ignore — memory cache still serves this session
  }
  return fresh;
}

export function playerName(p: Player | undefined, id?: string): string {
  if (!p) return id ? `Player ${id}` : 'Unknown';
  if (p.full_name) return p.full_name;
  const composed = [p.first_name, p.last_name].filter(Boolean).join(' ').trim();
  return composed || (id ? `Player ${id}` : 'Unknown');
}

// ---- Avatars ---------------------------------------------------------------

export function avatarUrl(avatar: string | null | undefined, thumb = true): string | null {
  if (!avatar) return null;
  return thumb
    ? `https://sleepercdn.com/avatars/thumbs/${avatar}`
    : `https://sleepercdn.com/avatars/${avatar}`;
}
