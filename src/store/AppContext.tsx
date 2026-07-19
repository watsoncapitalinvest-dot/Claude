/**
 * App-wide selection state: which Sleeper user we're acting as, which league is
 * active, and the current NFL week. Persisted to AsyncStorage so the app opens
 * straight to your team on relaunch. Everything here is derived from public
 * Sleeper data — no credentials are ever stored.
 */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getNflState, type NflState, type SleeperUser } from '../api/sleeper';

const STORAGE_KEY = 'gridirongm.session.v1';

interface PersistedSession {
  user: SleeperUser;
  leagueId: string;
  season: string;
}

interface AppState {
  ready: boolean;
  user: SleeperUser | null;
  leagueId: string | null;
  season: string | null;
  nflState: NflState | null;
  /** Week a manager is actively planning — defaults to the current NFL week. */
  activeWeek: number;
  setActiveWeek: (w: number) => void;
  signIn: (user: SleeperUser, leagueId: string, season: string) => Promise<void>;
  switchLeague: (leagueId: string, season: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<SleeperUser | null>(null);
  const [leagueId, setLeagueId] = useState<string | null>(null);
  const [season, setSeason] = useState<string | null>(null);
  const [nflState, setNflState] = useState<NflState | null>(null);
  const [activeWeek, setActiveWeek] = useState<number>(1);

  // Boot: load NFL state (for the current week) and any saved session.
  useEffect(() => {
    (async () => {
      try {
        const state = await getNflState();
        setNflState(state);
        const wk = state.display_week || state.week || 1;
        setActiveWeek(Math.max(1, wk));
      } catch {
        // Offline or endpoint hiccup — app still works, just without week hints.
      }
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (raw) {
          const s = JSON.parse(raw) as PersistedSession;
          setUser(s.user);
          setLeagueId(s.leagueId);
          setSeason(s.season);
        }
      } catch {
        // ignore corrupt session
      }
      setReady(true);
    })();
  }, []);

  const persist = useCallback(async (next: PersistedSession) => {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }, []);

  const signIn = useCallback(
    async (u: SleeperUser, lid: string, ssn: string) => {
      setUser(u);
      setLeagueId(lid);
      setSeason(ssn);
      await persist({ user: u, leagueId: lid, season: ssn });
    },
    [persist],
  );

  const switchLeague = useCallback(
    async (lid: string, ssn: string) => {
      if (!user) return;
      setLeagueId(lid);
      setSeason(ssn);
      await persist({ user, leagueId: lid, season: ssn });
    },
    [persist, user],
  );

  const signOut = useCallback(async () => {
    setUser(null);
    setLeagueId(null);
    setSeason(null);
    await AsyncStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo<AppState>(
    () => ({
      ready,
      user,
      leagueId,
      season,
      nflState,
      activeWeek,
      setActiveWeek,
      signIn,
      switchLeague,
      signOut,
    }),
    [ready, user, leagueId, season, nflState, activeWeek, signIn, switchLeague, signOut],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useApp(): AppState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
